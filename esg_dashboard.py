"""
ESG Intelligence Dashboard
A high-performance Streamlit dashboard for 2,000+ ESG JSON files.
Run: streamlit run esg_dashboard.py
"""

import streamlit as st
import pandas as pd

# ── Page Config (must be first Streamlit command) ──────────────────────────────
st.set_page_config(
    page_title="ESG Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after page config) ────────────────────────────────────────────────
from data_loader import (
    build_company_index,
    load_company,
    extract_kpi,
    extract_numeric,
    format_value,
    format_metric,
    get_aggregate_stats,
)
from charts import (
    company_treemap,
    emissions_histogram,
    disclosure_pie,
    emissions_gauge,
    diversity_sunburst,
    energy_breakdown_bar,
    governance_table_data,
)
from styles import inject_css, EMERALD, ROYAL_BLUE, AMBER, MUTED, TEXT

# ── Inject CSS ─────────────────────────────────────────────────────────────────
st.markdown(inject_css(), unsafe_allow_html=True)

# ── Session State Init ─────────────────────────────────────────────────────────
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
        <div style="text-align:center; padding: 1rem 0 0.5rem;">
            <div style="font-size:2.2rem;">🌍</div>
            <div style="font-size:1.1rem; font-weight:700; 
                 background: linear-gradient(135deg, {EMERALD}, {ROYAL_BLUE});
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 background-clip: text;">ESG Intelligence</div>
            <div style="font-size:0.7rem; color:{MUTED}; margin-top:2px;">
                BRSR Data Explorer
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Load index
    index_df = build_company_index()

    # Search
    search = st.text_input("🔍 Search company", placeholder="Type to filter…", label_visibility="collapsed")

    filtered = index_df
    if search:
        filtered = index_df[index_df["company_name"].str.contains(search, case=False, na=False)]

    # Company selector
    company_options = ["📊 Market Overview"] + filtered["company_name"].tolist()
    choice = st.selectbox(
        "Select company",
        company_options,
        index=0,
        label_visibility="collapsed",
    )

    if choice == "📊 Market Overview":
        st.session_state.selected_company = None
    else:
        row = filtered[filtered["company_name"] == choice].iloc[0]
        st.session_state.selected_company = row.to_dict()

    # Stats footer
    st.markdown("---")
    st.markdown(f"""
        <div style="text-align:center; padding:0.5rem 0;">
            <div style="font-size:2rem; font-weight:800; color:{TEXT};">{len(index_df):,}</div>
            <div style="font-size:0.75rem; color:{MUTED}; text-transform:uppercase; letter-spacing:1px;">
                Companies Indexed
            </div>
        </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MARKET VIEW  (no company selected)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.selected_company is None:
    # Hero
    st.markdown(f"""
        <div class="hero-card">
            <div class="hero-title">ESG Market Intelligence</div>
            <div class="hero-subtitle">
                Aggregate view across <b>{len(index_df):,}</b> Indian companies · BRSR / ESG disclosures
            </div>
            <div style="margin-top:1rem; display:flex; gap:1rem; flex-wrap:wrap;">
                <div class="stat-pill">
                    <span style="color:{EMERALD};">●</span> Environmental
                </div>
                <div class="stat-pill">
                    <span style="color:{ROYAL_BLUE};">●</span> Social
                </div>
                <div class="stat-pill">
                    <span style="color:{AMBER};">●</span> Governance
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Load aggregates
    stats = get_aggregate_stats()

    # Row of summary KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
            <div class="kpi-card env">
                <div class="kpi-label">Companies with Scope 1 Data</div>
                <div class="kpi-value">{len(stats['scope1_values']):,}</div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="kpi-card soc">
                <div class="kpi-label">Companies with Scope 2 Data</div>
                <div class="kpi-value">{len(stats['scope2_values']):,}</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        total_dp = stats["disclosed_count"] + stats["not_disclosed_count"]
        disc_pct = stats["disclosed_count"] / total_dp * 100 if total_dp else 0
        st.markdown(f"""
            <div class="kpi-card gov">
                <div class="kpi-label">Disclosure Rate</div>
                <div class="kpi-value">{disc_pct:.1f}%</div>
                <div class="kpi-unit">{stats['disclosed_count']:,} / {total_dp:,} data points</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="kpi-card env">
                <div class="kpi-label">Avg Emissions Intensity</div>
                <div class="kpi-value">{stats['avg_emissions_intensity']:.2f}</div>
                <div class="kpi-unit">tCO₂e per unit</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # Charts row 1 — Treemap
    st.plotly_chart(
        company_treemap(stats["pillar_data"]),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # Charts row 2 — Histogram + Pie
    col_hist, col_pie = st.columns([3, 2])
    with col_hist:
        st.plotly_chart(
            emissions_histogram(stats["scope1_values"], stats["scope2_values"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with col_pie:
        st.plotly_chart(
            disclosure_pie(stats["disclosed_count"], stats["not_disclosed_count"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )


# ══════════════════════════════════════════════════════════════════════════════
#  COMPANY DEEP-DIVE
# ══════════════════════════════════════════════════════════════════════════════
else:
    company_info = st.session_state.selected_company
    data = load_company(company_info["filename"])
    meta = data.get("metadata", {})
    dps = data.get("data_points", [])

    # Back button
    if st.button("← Back to Market View"):
        st.session_state.selected_company = None
        st.rerun()

    # ── Hero Card ──────────────────────────────────────────────────────────────
    source_btn = ""
    if meta.get("source_url"):
        source_btn = f'<a href="{meta["source_url"]}" target="_blank" style="display:inline-block;margin-top:0.8rem;padding:0.4rem 1.2rem;background:linear-gradient(135deg,{ROYAL_BLUE},#2563EB);color:white;border-radius:8px;text-decoration:none;font-size:0.8rem;font-weight:600;">📄 View Source Document</a>'

    st.markdown(f"""
        <div class="hero-card">
            <div class="hero-title">{meta.get('company_name', 'Company')}</div>
            <div class="hero-subtitle">
                FY {meta.get('year', '—')} · {meta.get('source_type', 'BRSR')} Report · 
                Extracted via {meta.get('extraction_method', '—')}
            </div>
            {source_btn}
        </div>
    """, unsafe_allow_html=True)

    # ── Pillar Scorecard (3 KPIs) ─────────────────────────────────────────────
    carbon_val, carbon_unit, _, _ = extract_kpi(dps, "Emissions Intensity (Physical)")
    gender_val, gender_unit, _, _ = extract_kpi(dps, "Gender Diversity (Total Emp)")
    energy_val, energy_unit, _, _ = extract_kpi(dps, "Total Energy Consumed (A+B+C+D+E+F)")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
            <div class="kpi-card env">
                <div class="kpi-label">Carbon Intensity</div>
                <div class="kpi-value">{format_value(carbon_val)}</div>
                <div class="kpi-unit">{carbon_unit or ''}</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="kpi-card soc">
                <div class="kpi-label">Gender Diversity</div>
                <div class="kpi-value">{format_value(gender_val)}{('%' if isinstance(gender_val, (int, float)) and gender_val is not None else '')}</div>
                <div class="kpi-unit">Female representation (total)</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="kpi-card gov">
                <div class="kpi-label">Energy Consumed</div>
                <div class="kpi-value">{format_value(energy_val)}</div>
                <div class="kpi-unit">{energy_unit or ''}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Tabs: E / S / G ──────────────────────────────────────────────────────
    tab_e, tab_s, tab_g = st.tabs([
        f"🌿 Environmental",
        f"👥 Social",
        f"⚖️ Governance",
    ])

    # ── Environmental Tab ─────────────────────────────────────────────────────
    with tab_e:
        # Load aggregate for comparison
        stats = get_aggregate_stats()

        e_col1, e_col2 = st.columns(2)
        with e_col1:
            ei_val = extract_numeric(dps, "Emissions Intensity (Physical)") or 0
            avg_ei = stats["avg_emissions_intensity"]
            st.plotly_chart(
                emissions_gauge(ei_val, avg_ei, meta.get("company_name", "")),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        with e_col2:
            renew = extract_numeric(dps, "Total Renewable Energy (A+B+C)") or 0
            non_renew = extract_numeric(dps, "Total Non-Renewable Energy (D+E+F)") or 0
            st.plotly_chart(
                energy_breakdown_bar(renew, non_renew),
                use_container_width=True,
                config={"displayModeBar": False},
            )

            # Key metrics
            scope1 = extract_numeric(dps, "Scope 1 emissions (absolute)")
            scope2 = extract_numeric(dps, "Scope 2 emissions (LB & MB)")
            scope3 = extract_numeric(dps, "Scope 3 emissions (total)")
            waste_recycled = extract_kpi(dps, "Waste Recycled %")[0]
            water = extract_numeric(dps, "Total Water Withdrawal")

            met_cols = st.columns(3)
            with met_cols[0]:
                st.metric("Scope 1", format_metric(scope1, "tCO₂e"))
            with met_cols[1]:
                st.metric("Scope 2", format_metric(scope2, "tCO₂e"))
            with met_cols[2]:
                st.metric("Scope 3", format_metric(scope3, "tCO₂e"))

            met_cols2 = st.columns(2)
            with met_cols2[0]:
                st.metric("Waste Recycled", format_value(waste_recycled))
            with met_cols2[1]:
                st.metric("Water Withdrawal", format_metric(water, "kL"))

    # ── Social Tab ────────────────────────────────────────────────────────────
    with tab_s:
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            board_pct = extract_numeric(dps, "Gender Diversity (Board)")
            total_pct = extract_numeric(dps, "Gender Diversity (Total Emp)")
            attr_emp = extract_numeric(dps, "Attrition (Employees)")
            attr_wrk = extract_numeric(dps, "Attrition (Workers)")

            st.plotly_chart(
                diversity_sunburst(board_pct, total_pct, attr_emp, attr_wrk),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        with s_col2:
            st.markdown(f"""
                <div class="kpi-card soc" style="margin-bottom:1rem;">
                    <div class="kpi-label">Total Workforce</div>
                    <div class="kpi-value">{format_value(extract_kpi(dps, 'Total Workforce')[0])}</div>
                </div>
            """, unsafe_allow_html=True)

            safety_cols = st.columns(2)
            with safety_cols[0]:
                ltifr_emp = extract_kpi(dps, "LTIFR (Employees)")[0]
                st.metric("LTIFR Employees", format_value(ltifr_emp))
            with safety_cols[1]:
                ltifr_wrk = extract_kpi(dps, "LTIFR (Workers)")[0]
                st.metric("LTIFR Workers", format_value(ltifr_wrk))

            iso_val = extract_kpi(dps, "ISO 45001 Certified")[0]
            hr_val = extract_kpi(dps, "Human Rights Policy")[0]
            sup_val = extract_kpi(dps, "Supplier Social Audits")[0]

            st.markdown("**Safety & Policies**")
            for label, val in [("ISO 45001", iso_val), ("Human Rights Policy", hr_val), ("Supplier Social Audits", sup_val)]:
                badge_cls = "high" if val and str(val).lower().startswith("yes") else "low"
                display = str(val)[:100] if val and val != "null" else "Not Disclosed"
                st.markdown(f"""
                    <div style="padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">
                        <span style="color:{MUTED}; font-size:0.8rem;">{label}</span><br>
                        <span class="evidence-badge {badge_cls}">{display[:60]}</span>
                    </div>
                """, unsafe_allow_html=True)

    # ── Governance Tab ────────────────────────────────────────────────────────
    with tab_g:
        gov_df = governance_table_data(dps)
        if not gov_df.empty:
            st.dataframe(
                gov_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Metric": st.column_config.TextColumn("Metric", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="large"),
                    "Verification": st.column_config.TextColumn("Verification", width="small"),
                    "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                },
            )
        else:
            st.info("No governance metrics available for this company.")

    # ── Evidence Explorer ─────────────────────────────────────────────────────
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="font-size:1.2rem; font-weight:700; color:{TEXT}; margin-bottom:0.75rem;">
            🔎 Evidence Explorer
        </div>
    """, unsafe_allow_html=True)

    # Build evidence table
    evidence_rows = []
    for dp in dps:
        val = dp.get("value")
        display_val = format_value(val)
        evidence_rows.append({
            "Pillar": dp.get("esg_pillar", "—"),
            "Category": dp.get("category", "—"),
            "Data Point": dp.get("data_point", "—"),
            "Value": display_val,
            "Unit": dp.get("unit") or "—",
            "Confidence": f"{dp.get('confidence_score', 0) * 100:.0f}%",
            "Verification": dp.get("verification_level", "—"),
            "Evidence": dp.get("evidence_snippet", "—"),
        })

    ev_df = pd.DataFrame(evidence_rows)

    # Filter bar
    filter_cols = st.columns([1, 1, 3])
    with filter_cols[0]:
        pillar_filter = st.selectbox(
            "Filter by Pillar",
            ["All"] + sorted(ev_df["Pillar"].unique().tolist()),
            key="ev_pillar",
        )
    with filter_cols[1]:
        cat_filter = st.selectbox(
            "Filter by Category",
            ["All"] + sorted(ev_df["Category"].unique().tolist()),
            key="ev_category",
        )
    with filter_cols[2]:
        ev_search = st.text_input("Search data points", placeholder="Type to search…", key="ev_search")

    display_df = ev_df.copy()
    if pillar_filter != "All":
        display_df = display_df[display_df["Pillar"] == pillar_filter]
    if cat_filter != "All":
        display_df = display_df[display_df["Category"] == cat_filter]
    if ev_search:
        display_df = display_df[
            display_df["Data Point"].str.contains(ev_search, case=False, na=False)
            | display_df["Evidence"].str.contains(ev_search, case=False, na=False)
        ]

    # Show table (without evidence column — shown in expander)
    st.dataframe(
        display_df[["Pillar", "Category", "Data Point", "Value", "Unit", "Confidence", "Verification"]],
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    # Expandable evidence detail
    with st.expander("📋 View Evidence Snippets", expanded=False):
        for _, row in display_df.iterrows():
            evidence_text = row["Evidence"]
            if evidence_text and evidence_text not in ("—", "null"):
                conf_pct = row["Confidence"]
                st.markdown(f"""
                    **{row['Data Point']}** ({row['Pillar']} · {row['Category']})  
                    > {evidence_text}  
                    
                    `{row['Verification']}` · Confidence: **{conf_pct}**
                    
                    ---
                """)
