import os
import json
import re
import datetime
import requests
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.oauth2 import service_account
import pandas as pd

# =====================================================
# 1. SETUP
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SERVICE_FILE = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE")
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION")
PDF_URL = "https://static-assets.tatamotors.com/Production/www-tatamotors-com-NEW/wp-content/uploads/2025/06/Voluntary-Report-based-on-BRSR-Framework-for-FY-2024-25.pdf"
LOCAL_FILE = "Tata_Motors_BRSR_2025.pdf"

credentials = service_account.Credentials.from_service_account_file(SERVICE_FILE)
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# =====================================================
# 2. COMPLETE FIELD METADATA MAPPING
# =====================================================
FIELD_METADATA = {
    # --- ENVIRONMENT ---
    "scope_1_emissions_absolute": {"pillar": "E", "category": "Emissions", "label": "Scope 1 emissions (absolute)", "metric_type": "quantitative"},
    "scope_2_emissions_lb_mb": {"pillar": "E", "category": "Emissions", "label": "Scope 2 emissions (LB & MB)", "metric_type": "quantitative"},
    "scope_3_emissions_total": {"pillar": "E", "category": "Emissions", "label": "Scope 3 emissions (total)", "metric_type": "quantitative"},
    
    # Scope 3 Categories
    "cat_1_purchased_goods": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 1: Purchased Goods", "metric_type": "quantitative"},
    "cat_3_fuel_energy_related": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 3: Fuel/Energy Related", "metric_type": "quantitative"},
    "cat_5_waste_generated": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 5: Waste Generated", "metric_type": "quantitative"},
    "cat_6_business_travel": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 6: Business Travel", "metric_type": "quantitative"},
    "cat_7_employee_commuting": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 7: Employee Commuting", "metric_type": "quantitative"},
    "cat_8_upstream_leased_assets": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 8: Upstream Leased Assets", "metric_type": "quantitative"},
    "cat_11_use_of_sold_products": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 11: Use of Sold Products", "metric_type": "quantitative"},
    "cat_14_franchises": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 14: Franchises", "metric_type": "quantitative"},

    # Intensity & Targets
    "revenue_intensity": {"pillar": "E", "category": "Emissions", "label": "Emissions Intensity (Revenue)", "metric_type": "quantitative"},
    "physical_intensity": {"pillar": "E", "category": "Emissions", "label": "Emissions Intensity (Physical)", "metric_type": "quantitative"},
    "emissions_baseline_year": {"pillar": "E", "category": "Strategy", "label": "Emissions Baseline Year", "metric_type": "categorical"},
    "emissions_reduction_target": {"pillar": "E", "category": "Strategy", "label": "Emissions Reduction Target", "metric_type": "quantitative"},
    "net_zero_commitment": {"pillar": "E", "category": "Strategy", "label": "Net Zero Commitment", "metric_type": "binary"},
    "net_zero_target_year": {"pillar": "E", "category": "Strategy", "label": "Net Zero Target Year", "metric_type": "categorical"},
    "sbti_commitment_status": {"pillar": "E", "category": "Strategy", "label": "SBTi Status", "metric_type": "binary"},
    
    # Energy
    "renewable_electricity_percent": {"pillar": "E", "category": "Energy", "label": "Renewable Electricity %", "metric_type": "quantitative"},
    "onsite_renewable_capacity": {"pillar": "E", "category": "Energy", "label": "Onsite Renewable Capacity", "metric_type": "quantitative"},
    "energy_consumption_total": {"pillar": "E", "category": "Energy", "label": "Total Energy Consumption", "metric_type": "quantitative"},
    "revenue": {"pillar": "E", "category": "Energy", "label": "Energy Intensity (Revenue)", "metric_type": "quantitative"},
    "physical": {"pillar": "E", "category": "Energy", "label": "Energy Intensity (Physical)", "metric_type": "quantitative"},
    "iso_50001_certification": {"pillar": "E", "category": "Energy", "label": "ISO 50001 Certified", "metric_type": "binary"},

    # Water
    "water_withdrawal_total": {"pillar": "E", "category": "Water", "label": "Total Water Withdrawal", "metric_type": "quantitative"},
    "water_consumption_net": {"pillar": "E", "category": "Water", "label": "Net Water Consumption", "metric_type": "quantitative"},
    "water_recycled_percent": {"pillar": "E", "category": "Water", "label": "Water Recycled %", "metric_type": "quantitative"},
    "water_stressed_locations": {"pillar": "E", "category": "Water", "label": "Water Stressed Locations", "metric_type": "quantitative"},
    "zld_status": {"pillar": "E", "category": "Water", "label": "ZLD Status", "metric_type": "binary"},
    "discharge_volume": {"pillar": "E", "category": "Water", "label": "Effluent Discharge Volume", "metric_type": "quantitative"},

    # Waste
    "waste_generated_total": {"pillar": "E", "category": "Waste", "label": "Total Waste Generated", "metric_type": "quantitative"},
    "hazardous_waste": {"pillar": "E", "category": "Waste", "label": "Hazardous Waste", "metric_type": "quantitative"},
    "waste_recycled_diverted_percent": {"pillar": "E", "category": "Waste", "label": "Waste Recycled %", "metric_type": "quantitative"},
    "landfill_volume": {"pillar": "E", "category": "Waste", "label": "Landfill Volume", "metric_type": "quantitative"},
    "incineration_volume": {"pillar": "E", "category": "Waste", "label": "Incineration Volume", "metric_type": "quantitative"},
    "plastic_usage_disclosure": {"pillar": "E", "category": "Waste", "label": "Plastic Usage", "metric_type": "quantitative"},
    "recycled_material_content": {"pillar": "E", "category": "Materials", "label": "Recycled Material Content", "metric_type": "quantitative"},

    # Other E
    "environmental_policy_published": {"pillar": "E", "category": "Policy", "label": "Env Policy Published", "metric_type": "binary"},
    "iso_14001_certification": {"pillar": "E", "category": "Policy", "label": "ISO 14001 Certified", "metric_type": "binary"},
    "environmental_fines_penalties": {"pillar": "E", "category": "Compliance", "label": "Env Fines/Penalties", "metric_type": "quantitative"},
    "cpcb_spcb_compliance": {"pillar": "E", "category": "Compliance", "label": "CPCB/SPCB Compliance", "metric_type": "binary"},
    "climate_risk_assessment": {"pillar": "E", "category": "Risk", "label": "Climate Risk Assessment", "metric_type": "binary"},
    "tcfd_alignment": {"pillar": "E", "category": "Risk", "label": "TCFD Alignment", "metric_type": "binary"},
    "transition_plan": {"pillar": "E", "category": "Strategy", "label": "Transition Plan", "metric_type": "binary"},
    "supplier_environmental_requirements": {"pillar": "E", "category": "Supply Chain", "label": "Supplier Env Requirements", "metric_type": "binary"},
    "r_and_d_percent": {"pillar": "E", "category": "Investment", "label": "Green R&D %", "metric_type": "quantitative"},
    "capex_percent": {"pillar": "E", "category": "Investment", "label": "Green CapEx %", "metric_type": "quantitative"},
    "product_carbon_footprint": {"pillar": "E", "category": "Product", "label": "Product Carbon Footprint", "metric_type": "quantitative"},

    # --- SOCIAL ---
    "total_workforce": {"pillar": "S", "category": "Workforce", "label": "Total Workforce", "metric_type": "quantitative"},
    "permanent_employees_percent": {"pillar": "S", "category": "Diversity", "label": "Gender Diversity (Perm Emp)", "metric_type": "quantitative"},
    "total_employees_percent": {"pillar": "S", "category": "Diversity", "label": "Gender Diversity (Total Emp)", "metric_type": "quantitative"},
    "board_diversity_percent": {"pillar": "S", "category": "Diversity", "label": "Gender Diversity (Board)", "metric_type": "quantitative"},
    "permanent_employees": {"pillar": "S", "category": "Retention", "label": "Attrition (Employees)", "metric_type": "quantitative"},
    "permanent_workers": {"pillar": "S", "category": "Retention", "label": "Attrition (Workers)", "metric_type": "quantitative"},
    "training_hours_per_employee": {"pillar": "S", "category": "Training", "label": "Training Hours", "metric_type": "quantitative"},
    "employees": {"pillar": "S", "category": "Safety", "label": "LTIFR (Employees)", "metric_type": "quantitative"},
    "workers": {"pillar": "S", "category": "Safety", "label": "LTIFR (Workers)", "metric_type": "quantitative"},
    "iso_45001": {"pillar": "S", "category": "Safety", "label": "ISO 45001 Certified", "metric_type": "binary"},
    "human_rights_policy": {"pillar": "S", "category": "Human Rights", "label": "Human Rights Policy", "metric_type": "binary"},
    "supplier_audits": {"pillar": "S", "category": "Supply Chain", "label": "Supplier Social Audits", "metric_type": "quantitative"},
    "csr_spend": {"pillar": "S", "category": "Community", "label": "CSR Spend", "metric_type": "quantitative"},

    # --- GOVERNANCE ---
    "board_independence_percent": {"pillar": "G", "category": "Board", "label": "Board Independence %", "metric_type": "quantitative"},
    "esg_oversight": {"pillar": "G", "category": "Board", "label": "ESG Oversight Committee", "metric_type": "binary"},
    "esg_linked_remuneration": {"pillar": "G", "category": "Remuneration", "label": "ESG Linked Pay", "metric_type": "binary"},
    "anti_corruption_policy": {"pillar": "G", "category": "Ethics", "label": "Anti-Corruption Policy", "metric_type": "binary"},
    "whistleblower_mechanism": {"pillar": "G", "category": "Ethics", "label": "Whistleblower Mechanism", "metric_type": "binary"},
    "legal_cases": {"pillar": "G", "category": "Compliance", "label": "Legal Cases", "metric_type": "quantitative"},

    # --- EXTERNAL ---
    "cdp_scores": {"pillar": "External", "category": "Ratings", "label": "CDP Score", "metric_type": "categorical"},
    "msci_esg_rating": {"pillar": "External", "category": "Ratings", "label": "MSCI Rating", "metric_type": "categorical"},
    "sustainalytics_risk_score": {"pillar": "External", "category": "Ratings", "label": "Sustainalytics Score", "metric_type": "quantitative"},
    "djsi_inclusion": {"pillar": "External", "category": "Ratings", "label": "DJSI Inclusion", "metric_type": "binary"},
    "ungc_participant": {"pillar": "External", "category": "Commitments", "label": "UNGC Participant", "metric_type": "binary"},
    "ecovadis_medal": {"pillar": "External", "category": "Ratings", "label": "EcoVadis Medal", "metric_type": "categorical"},
    "pat_scheme_participation": {"pillar": "External", "category": "Regulatory", "label": "PAT Scheme", "metric_type": "binary"},
    "pli_auto_participation": {"pillar": "External", "category": "Regulatory", "label": "PLI Auto Participation", "metric_type": "binary"},
}

# =====================================================
# 3. EXTRACTION LAYER (With FULL Schema)
# =====================================================
def extract_nested_data(pdf_path):
    print(f"🚀 Extracting data from {pdf_path}...")
    
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    model = GenerativeModel("gemini-2.5-pro")
    
    full_response_schema = {
        "type": "OBJECT",
        "properties": {
            "company_metadata": {
                "type": "OBJECT",
                "properties": {
                    "company_name": {"type": "STRING"},
                    "reporting_year": {"type": "STRING"},
                    "currency": {"type": "STRING"}
                }
            },
            "environment": {
                "type": "OBJECT",
                "properties": {
                    "scope_1_emissions_absolute": {"type": "STRING"},
                    "scope_2_emissions_lb_mb": {"type": "STRING"},
                    "scope_3_emissions_total": {"type": "STRING"},
                    "scope_3_breakdown": {
                        "type": "OBJECT",
                        "properties": {
                            "cat_1_purchased_goods": {"type": "STRING"},
                            "cat_3_fuel_energy_related": {"type": "STRING"},
                            "cat_5_waste_generated": {"type": "STRING"},
                            "cat_6_business_travel": {"type": "STRING"},
                            "cat_7_employee_commuting": {"type": "STRING"},
                            "cat_8_upstream_leased_assets": {"type": "STRING"},
                            "cat_11_use_of_sold_products": {"type": "STRING"},
                            "cat_14_franchises": {"type": "STRING"}
                        }
                    },
                    "emissions_intensity": {
                        "type": "OBJECT",
                        "properties": {
                            "revenue_intensity": {"type": "STRING"},
                            "physical_intensity": {"type": "STRING"}
                        }
                    },
                    "emissions_baseline_year": {"type": "STRING"},
                    "emissions_reduction_target": {"type": "STRING"},
                    "net_zero_commitment": {"type": "STRING"},
                    "net_zero_target_year": {"type": "STRING"},
                    "sbti_commitment_status": {"type": "STRING"},
                    "renewable_electricity_percent": {"type": "STRING"},
                    "onsite_renewable_capacity": {"type": "STRING"},
                    "energy_consumption_total": {"type": "STRING"},
                    "energy_intensity": {
                        "type": "OBJECT",
                        "properties": {
                            "revenue": {"type": "STRING"},
                            "physical": {"type": "STRING"}
                        }
                    },
                    "iso_50001_certification": {"type": "STRING"},
                    "water_withdrawal_total": {"type": "STRING"},
                    "water_consumption_net": {"type": "STRING"},
                    "water_recycled_percent": {"type": "STRING"},
                    "water_stressed_locations": {"type": "STRING"},
                    "zld_effluent_discharge": {
                        "type": "OBJECT",
                        "properties": {
                            "zld_status": {"type": "STRING"},
                            "discharge_volume": {"type": "STRING"}
                        }
                    },
                    "waste_generated_total": {"type": "STRING"},
                    "hazardous_waste": {"type": "STRING"},
                    "waste_recycled_diverted_percent": {"type": "STRING"},
                    "landfill_disposal_route": {
                        "type": "OBJECT",
                        "properties": {
                            "landfill_volume": {"type": "STRING"},
                            "incineration_volume": {"type": "STRING"}
                        }
                    },
                    "plastic_usage_disclosure": {"type": "STRING"},
                    "recycled_material_content": {"type": "STRING"},
                    "environmental_policy_published": {"type": "STRING"},
                    "iso_14001_certification": {"type": "STRING"},
                    "environmental_fines_penalties": {"type": "STRING"},
                    "cpcb_spcb_compliance": {"type": "STRING"},
                    "climate_risk_assessment": {"type": "STRING"},
                    "tcfd_alignment": {"type": "STRING"},
                    "transition_plan": {"type": "STRING"},
                    "supplier_environmental_requirements": {"type": "STRING"},
                    "ev_cleantech_investments": {
                        "type": "OBJECT",
                        "properties": {
                            "r_and_d_percent": {"type": "STRING"},
                            "capex_percent": {"type": "STRING"}
                        }
                    },
                    "product_carbon_footprint": {"type": "STRING"}
                }
            },
            "social": {
                "type": "OBJECT",
                "properties": {
                    "total_workforce": {"type": "STRING"},
                    "gender_diversity": {
                        "type": "OBJECT",
                        "properties": {
                            "permanent_employees_percent": {"type": "STRING"},
                            "total_employees_percent": {"type": "STRING"},
                            "board_diversity_percent": {"type": "STRING"}
                        }
                    },
                    "attrition_rate": {
                        "type": "OBJECT",
                        "properties": {
                            "permanent_employees": {"type": "STRING"},
                            "permanent_workers": {"type": "STRING"}
                        }
                    },
                    "training_hours_per_employee": {"type": "STRING"},
                    "safety_metrics_ltifr": {
                        "type": "OBJECT",
                        "properties": {
                            "employees": {"type": "STRING"},
                            "workers": {"type": "STRING"}
                        }
                    },
                    "iso_45001": {"type": "STRING"},
                    "human_rights_policy": {"type": "STRING"},
                    "supplier_audits": {"type": "STRING"},
                    "csr_spend": {"type": "STRING"}
                }
            },
            "governance": {
                "type": "OBJECT",
                "properties": {
                    "board_independence_percent": {"type": "STRING"},
                    "esg_oversight": {"type": "STRING"},
                    "esg_linked_remuneration": {"type": "STRING"},
                    "anti_corruption_policy": {"type": "STRING"},
                    "whistleblower_mechanism": {"type": "STRING"},
                    "legal_cases": {"type": "STRING"}
                }
            },
            "external_signals": {
                "type": "OBJECT",
                "properties": {
                    "cdp_scores": {"type": "STRING"},
                    "msci_esg_rating": {"type": "STRING"},
                    "sustainalytics_risk_score": {"type": "STRING"},
                    "djsi_inclusion": {"type": "STRING"},
                    "ungc_participant": {"type": "STRING"},
                    "ecovadis_medal": {"type": "STRING"},
                    "pat_scheme_participation": {"type": "STRING"},
                    "pli_auto_participation": {"type": "STRING"}
                }
            }
        }
    }

    prompt = """
    You are an expert ESG Data Analyst. Extract ALL data points defined in the schema from the provided PDF.
    
    INSTRUCTIONS:
    1. Extract the Value AND Unit (e.g. '70,476 tCO2e').
    2. If a value is missing, return the string "null".
    3. Prioritize 'Consolidated' figures.
    """
    
    response = model.generate_content(
        [Part.from_data(mime_type="application/pdf", data=pdf_data), prompt],
        generation_config={
            "response_mime_type": "application/json", 
            "response_schema": full_response_schema,
            "temperature": 0
        }
    )
    return json.loads(response.text)

# =====================================================
# 4. TRANSFORMATION LAYER - ML READY
# =====================================================
def parse_value_unit(raw_string):
    """Splits '70,746 tCO2e' into value=70746 and unit='tCO2e'"""
    if not raw_string or str(raw_string).lower() == "null":
        return None, None
    
    clean_str = str(raw_string).strip()
    
    match = re.match(r"^([\d,.]+)\s*(.*)$", clean_str)
    if match:
        val_str = match.group(1).replace(",", "")
        try:
            val = float(val_str) if "." in val_str else int(val_str)
        except:
            val = val_str
        unit = match.group(2).strip()
        return val, unit
    return clean_str, "Text"

def transform_to_ml_ready_format(nested_data):
    print("🔄 Transforming to ML-Ready Standard Format...")
    
    # Extract metadata once
    meta = nested_data.get("company_metadata", {})
    company_name = meta.get("company_name", "Unknown")
    year = meta.get("reporting_year", "2024-25")
    
    rows = []
    
    def process_item(key, value):
        if key == "company_metadata": 
            return

        # Recursion for nested dicts
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                process_item(sub_key, sub_val)
            return

        # Lookup Metadata
        mapping = FIELD_METADATA.get(key)
        
        if not mapping:
            mapping = {
                "pillar": "General", 
                "category": "Unmapped", 
                "label": key.replace("_", " ").title(),
                "metric_type": "text"
            }
        
        parsed_val, parsed_unit = parse_value_unit(value)
        
        # Create standardized row with all metadata
        row = {
            # Company Identifiers
            "company_id": "TATA_MOTORS_IN",
            "company_name": company_name,
            "industry": "Automotive Manufacturing",
            "tier": "OEM",
            "reporting_year": year,
            
            # Metric Information
            "metric_id": key,
            "metric_name": mapping["label"],
            "esg_pillar": mapping["pillar"],
            "category": mapping["category"],
            "metric_type": mapping.get("metric_type", "text"),
            
            # Values
            "value_numeric": parsed_val if isinstance(parsed_val, (int, float)) else None,
            "value_text": str(value) if parsed_val is None else None,
            "unit": parsed_unit,
            "raw_value": str(value),
            
            # Data Quality
            "confidence_score": 0.95 if parsed_val is not None else 0.5,
            "verification_level": "Self-declared",
            "data_completeness": 1.0 if parsed_val is not None else 0.0,
            
            # Source Information
            "source_type": "BRSR",
            "source_url": PDF_URL,
            "document_title": "Voluntary Report based on BRSR Framework FY 2024-25",
            "extraction_method": "multimodal_llm",
            "extraction_timestamp": datetime.datetime.now().isoformat(),
            "last_updated": datetime.date.today().isoformat()
        }
        rows.append(row)

    # Process all root keys
    for key, val in nested_data.items():
        process_item(key, val)
                
    return rows

# =====================================================
# 5. SAVE IN MULTIPLE FORMATS
# =====================================================
def save_outputs(data_rows):
    """Save in JSON, CSV, and Parquet for ML compatibility"""
    
    # 1. Save as JSON (nested structure preserved)
    with open("esg_data_ml_ready.json", "w") as f:
        json.dump(data_rows, f, indent=2)
    print("✅ Saved: esg_data_ml_ready.json")
    
    # 2. Save as CSV (tabular format for easy analysis)
    df = pd.DataFrame(data_rows)
    df.to_csv("esg_data_ml_ready.csv", index=False)
    print("✅ Saved: esg_data_ml_ready.csv")
    
    # 3. Save as Parquet (optimized for ML pipelines)
    df.to_parquet("esg_data_ml_ready.parquet", index=False)
    print("✅ Saved: esg_data_ml_ready.parquet")
    
    # 4. Create a summary statistics file
    summary = {
        "total_metrics": len(data_rows),
        "metrics_by_pillar": df.groupby("esg_pillar").size().to_dict(),
        "metrics_by_category": df.groupby("category").size().to_dict(),
        "data_completeness": {
            "numeric_metrics": int(df["value_numeric"].notna().sum()),
            "text_metrics": int(df["value_text"].notna().sum()),
            "missing_values": int(df[["value_numeric", "value_text"]].isna().all(axis=1).sum())
        },
        "metric_types": df.groupby("metric_type").size().to_dict()
    }
    
    with open("esg_data_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("✅ Saved: esg_data_summary.json")
    
    return df

# =====================================================
# 6. EXECUTION
# =====================================================
if __name__ == "__main__":
    if not os.path.exists(LOCAL_FILE):
        print("⬇️ Downloading PDF...")
        with open(LOCAL_FILE, "wb") as f:
            f.write(requests.get(PDF_URL).content)

    nested_json = extract_nested_data(LOCAL_FILE)
    ml_ready_data = transform_to_ml_ready_format(nested_json)
    df = save_outputs(ml_ready_data)
    
    print(f"\n🎯 Processed {len(ml_ready_data)} ESG metrics")
    print(f"📊 Numeric metrics: {df['value_numeric'].notna().sum()}")
    print(f"📝 Text metrics: {df['value_text'].notna().sum()}")
    print("\n✨ Data ready for ML models in 3 formats: JSON, CSV, Parquet")