import pdfplumber
import pandas as pd
import re
import json
import datetime

# -----------------------------------
# Unit pattern dictionary
# -----------------------------------
UNIT_PATTERNS = {
    "tCO2e": r"(tco2e|tonnes? of co2e)",
    "kgCO2e": r"(kgco2e)",
    "GJ": r"\bGJ\b",
    "MJ": r"\bMJ\b",
    "kWh": r"\bkwh\b",
    "MWh": r"\bmwh\b",
    "%": r"\b%\b|percent|percentage",
    "KL": r"\bkl\b",
    "ML": r"\bml\b",
    "m3": r"(m3|cubic meter)",
    "MT": r"\bmt\b",
    "tonnes": r"\btonnes?\b",
    "No": r"(yes|no)"
}

# -----------------------------------
# ESG field mapping (unchanged)
# -----------------------------------
FIELD_METADATA_MAP = {
    "scope_1_emissions_absolute": [r"Scope 1 emissions", r"Direct emissions"],
    "scope_2_emissions_lb_mb": [r"Scope 2 emissions", r"Indirect emissions"],
    "scope_3_emissions_total": [r"Total Scope 3 emissions"],
    "renewable_electricity_percent": [r"renewable sources"],
    "energy_consumption_total": [r"Total energy consumption"],
    "water_withdrawal_total": [r"Total volume of water withdrawal"],
    "waste_generated_total": [r"Total waste generated"],
    "csr_spend": [r"CSR.*expenditure"]
}

# -----------------------------------
# Clean number
# -----------------------------------
def extract_number(text):
    if not text:
        return None
    match = re.search(r"([-+]?\d[\d,]*\.?\d*)", str(text))
    if not match:
        return None
    try:
        val = match.group(1).replace(",", "")
        return float(val) if "." in val else int(val)
    except ValueError:
        return None

# -----------------------------------
# Extract unit
# -----------------------------------
def extract_unit(text):
    if not text:
        return None

    text = str(text).lower()
    for unit, pattern in UNIT_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return unit
    return None

# -----------------------------------
# Main extraction logic
# -----------------------------------
def extract_brsr_data(pdf_path):
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                df = pd.DataFrame(table).fillna("")
                headers = df.iloc[0].astype(str).str.lower()

                header_unit = None
                for h in headers:
                    header_unit = extract_unit(h)
                    if header_unit:
                        break

                for idx, row in df.iterrows():
                    row_text = " ".join(map(str, row))

                    for key, patterns in FIELD_METADATA_MAP.items():
                        if any(re.search(p, row_text, re.IGNORECASE) for p in patterns):

                            value_cell = None
                            unit = None

                            for cell in reversed(row.tolist()):
                                if extract_number(cell) is not None:
                                    value_cell = cell
                                    unit = extract_unit(cell)
                                    break

                            if not unit:
                                unit = header_unit

                            results.append({
                                "company_id": "TATA_MOTORS_IN",
                                "data_point": key,
                                "value": extract_number(value_cell),
                                "unit": unit or "UNKNOWN",
                                "raw_value": str(value_cell).strip(),
                                "page_number": page_num,
                                "year": "2024-25",
                                "extraction_method": "rule_based_with_unit_inference",
                                "last_crawled": datetime.date.today().isoformat()
                            })

    return results

# -----------------------------------
# Entry point
# -----------------------------------
if __name__ == "__main__":
    PDF_FILE = "Tata_Motors_BRSR_2025.pdf"

    data = extract_brsr_data(PDF_FILE)

    with open("esg_standardized_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Extraction complete. Records: {len(data)}")
