"""
ESG Dashboard — Data Loader
Lazy-loading pipeline for 2,000+ ESG JSON files.
"""

import os
import json
import streamlit as st
import pandas as pd
from pathlib import Path

ESG_DIR = Path(__file__).parent / "esg_outputs"


# ── Index Builder ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def build_company_index() -> pd.DataFrame:
    """
    Scans the esg_outputs directory and reads only metadata from each file.
    Returns a DataFrame with columns: filename, company_name, company_id, year.
    """
    rows = []
    for entry in os.scandir(ESG_DIR):
        if not entry.name.endswith(".json"):
            continue
        try:
            with open(entry.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("metadata", {})
            rows.append({
                "filename": entry.name,
                "company_name": meta.get("company_name", entry.name.replace("_esg.json", "").replace("_", " ")),
                "company_id": meta.get("company_id", ""),
                "year": meta.get("year", "N/A"),
                "source_url": meta.get("source_url", ""),
            })
        except Exception:
            continue
    df = pd.DataFrame(rows)
    # Deduplicate — keep the first occurrence per company_id (case-insensitive)
    df["_id_lower"] = df["company_id"].str.upper()
    df = df.drop_duplicates(subset="_id_lower", keep="first").drop(columns="_id_lower")
    df = df.sort_values("company_name", ignore_index=True)
    return df


# ── Single Company Loader ─────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_company(filename: str) -> dict:
    """Load and return a single company's full JSON."""
    filepath = ESG_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ── KPI Extractor ─────────────────────────────────────────────────────────────
def extract_kpi(data_points: list, name: str):
    """
    Pull a named data_point from the list.
    Returns (value, unit, evidence_snippet, confidence_score) or Nones.
    """
    for dp in data_points:
        if dp.get("data_point") == name:
            return (
                dp.get("value"),
                dp.get("unit"),
                dp.get("evidence_snippet"),
                dp.get("confidence_score", 0),
            )
    return (None, None, None, 0)


def extract_numeric(data_points: list, name: str):
    """Extract a numeric value; returns None if non-numeric."""
    val, *_ = extract_kpi(data_points, name)
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ── Value Formatter ────────────────────────────────────────────────────────────
def format_value(val, unit=""):
    """
    Converts scientific notation to readable strings, handles None.
    Examples: 3e-07 → '0.0000003', None → 'Not Disclosed'
    """
    if val is None or val == "null" or val == "":
        return "Not Disclosed"
    if isinstance(val, float):
        if abs(val) < 0.001 and val != 0:
            return f"{val:.10f}".rstrip("0").rstrip(".")
        return f"{val:,.2f}"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)


def format_metric(val, unit=""):
    """For st.metric display — shorter."""
    formatted = format_value(val, unit)
    if formatted == "Not Disclosed":
        return formatted
    if unit and unit not in ("Text", ""):
        return f"{formatted} {unit}"
    return formatted


# ── Aggregate Statistics (cached) ──────────────────────────────────────────────
@st.cache_data(show_spinner="Scanning all companies…")
def get_aggregate_stats() -> dict:
    """
    One-time scan of all files for aggregate Market View data.
    Returns dict with keys:
      - scope1_values, scope2_values (lists of floats)
      - disclosed_count, not_disclosed_count
      - pillar_data: list of dicts for treemap
      - avg_emissions_intensity (float)
      - total_companies (int)
    """
    scope1 = []
    scope2 = []
    disclosed = 0
    not_disclosed = 0
    pillar_data = []
    emissions_intensities = []

    for entry in os.scandir(ESG_DIR):
        if not entry.name.endswith(".json"):
            continue
        try:
            with open(entry.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        meta = data.get("metadata", {})
        dps = data.get("data_points", [])
        cname = meta.get("company_name", entry.name)

        # Pillar confidence averages
        pillar_scores = {"E": [], "S": [], "G": []}
        for dp in dps:
            pillar = dp.get("esg_pillar", "")
            conf = dp.get("confidence_score", 0)

            # Disclosure tracking
            v = dp.get("value")
            if v is None or v == "null" or str(v).strip() == "":
                not_disclosed += 1
            else:
                disclosed += 1

            if pillar in pillar_scores:
                pillar_scores[pillar].append(conf)

        # Scope 1 / 2
        s1 = extract_numeric(dps, "Scope 1 emissions (absolute)")
        s2 = extract_numeric(dps, "Scope 2 emissions (LB & MB)")
        if s1 is not None and s1 > 0:
            scope1.append(s1)
        if s2 is not None and s2 > 0:
            scope2.append(s2)

        # Emissions intensity
        ei = extract_numeric(dps, "Emissions Intensity (Physical)")
        if ei is not None and ei > 0:
            emissions_intensities.append(ei)

        # Treemap entry
        avg_conf = {}
        for p, scores in pillar_scores.items():
            avg_conf[p] = sum(scores) / len(scores) if scores else 0
        overall = sum(avg_conf.values()) / 3 if any(avg_conf.values()) else 0
        pillar_data.append({
            "company": cname,
            "E_score": round(avg_conf["E"] * 100, 1),
            "S_score": round(avg_conf["S"] * 100, 1),
            "G_score": round(avg_conf["G"] * 100, 1),
            "overall": round(overall * 100, 1),
        })

    avg_ei = sum(emissions_intensities) / len(emissions_intensities) if emissions_intensities else 0

    return {
        "scope1_values": scope1,
        "scope2_values": scope2,
        "disclosed_count": disclosed,
        "not_disclosed_count": not_disclosed,
        "pillar_data": pillar_data,
        "avg_emissions_intensity": avg_ei,
        "total_companies": len(pillar_data),
    }
