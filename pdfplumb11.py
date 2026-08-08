import pdfplumber
import pandas as pd
import re
import json
import datetime

# -----------------------------
# Metadata mapping (unchanged)
# -----------------------------
FIELD_METADATA_MAP = {
    "scope_1_emissions_absolute": [r"Scope 1 emissions", r"Direct emissions"],
    "scope_2_emissions_lb_mb": [r"Scope 2 emissions", r"Indirect emissions"],
    "scope_3_emissions_total": [r"Total Scope 3 emissions"],
    "cat_1_purchased_goods": [r"Purchased goods and services"],
    "cat_3_fuel_energy_related": [r"Fuel-and-energy-related activities"],
    "cat_5_waste_generated": [r"Waste generated in operations"],
    "cat_6_business_travel": [r"Business travel"],
    "cat_7_employee_commuting": [r"Employee commuting"],
    "cat_8_upstream_leased_assets": [r"Upstream leased assets"],
    "cat_11_use_of_sold_products": [r"Use of sold products"],
    "cat_14_franchises": [r"Franchises"],
    "renewable_electricity_percent": [
        r"renewable sources.*percentage",
        r"Percentage of energy.*renewable"
    ],
    "onsite_renewable_capacity": [r"On-site renewable energy capacity"],
    "energy_consumption_total": [r"Total energy consumption"],
    "water_withdrawal_total": [r"Total volume of water withdrawal"],
    "water_consumption_net": [r"Total water consumption"],
    "water_recycled_percent": [r"Percentage of water recycled"],
    "zld_status": [r"Zero Liquid Discharge", r"\bZLD\b"],
    "waste_generated_total": [r"Total waste generated"],
    "hazardous_waste": [r"Total hazardous waste"],
    "waste_recycled_diverted_percent": [
        r"Total waste recycled",
        r"waste diverted from disposal"
    ],
    "plastic_usage_disclosure": [r"Total weight of plastic"],
    "environmental_policy_published": [
        r"environmental policy"
    ],
    "iso_14001_certification": [r"ISO\s*14001"],
    "iso_50001_certification": [r"ISO\s*50001"],
    "total_workforce": [
        r"Total number of employees",
        r"Total workforce"
    ],
    "permanent_employees_percent": [
        r"Percentage of female.*permanent employees"
    ],
    "board_diversity_percent": [
        r"Percentage of women on the Board"
    ],
    "training_hours_per_employee": [
        r"Average training hours"
    ],
    "iso_45001": [r"ISO\s*45001"],
    "human_rights_policy": [r"human rights policy"],
    "csr_spend": [
        r"Total amount spent on CSR",
        r"CSR.*expenditure"
    ],
    "board_independence_percent": [
        r"Percentage of independent directors"
    ],
    "esg_oversight": [
        r"Board committee responsible for ESG"
    ],
    "anti_corruption_policy": [
        r"Anti-corruption policy",
        r"Anti-bribery policy"
    ],
    "whistle_mechanism": [
        r"Whistle blower mechanism",
        r"Vigil mechanism"
    ]
}

# -----------------------------
# Utility: clean numbers
# -----------------------------
def clean_numerical_value(raw_val):
    if raw_val is None:
        return None

    raw_val = str(raw_val).strip().lower()
    if raw_val in ["null", "nan", "-", "", "not applicable", "na"]:
        return None

    match = re.search(r"([-+]?\d[\d,]*\.?\d*)", raw_val)
    if not match:
        return None

    try:
        num = match.group(1).replace(",", "")
        return float(num) if "." in num else int(num)
    except ValueError:
        return None

# -----------------------------
# Main extraction logic
# -----------------------------
def extract_brsr_data(pdf_path):
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            if not tables:
                continue

            for table in tables:
                df = pd.DataFrame(table).fillna("")

                for _, row in df.iterrows():
                    row_text = " ".join(map(str, row))

                    for key, patterns in FIELD_METADATA_MAP.items():
                        for pattern in patterns:
                            if re.search(pattern, row_text, re.IGNORECASE):

                                # Prefer last non-empty cell as value
                                value_cell = None
                                for cell in reversed(row.tolist()):
                                    if str(cell).strip():
                                        value_cell = cell
                                        break

                                results.append({
                                    "company_id": "TATA_MOTORS_IN",
                                    "data_point": key,
                                    "value": clean_numerical_value(value_cell),
                                    "raw_value": str(value_cell).strip(),
                                    "year": "2024-25",
                                    "page_number": page_num,
                                    "extraction_method": "rule_based_regex_table",
                                    "last_crawled": datetime.date.today().isoformat()
                                })

                                break  # stop after first pattern match

    return results

# -----------------------------
# Script entry point
# -----------------------------
if __name__ == "__main__":
    PDF_FILE = "Tata_Motors_BRSR_2025.pdf"
    OUTPUT_FILE = "esg_standardized_output.json"

    data = extract_brsr_data(PDF_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Extraction complete. Records extracted: {len(data)}")
