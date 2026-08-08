import os
import json
import re
import datetime
import requests
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.oauth2 import service_account

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
    "scope_1_emissions_absolute": {"pillar": "E", "category": "Emissions", "label": "Scope 1 emissions (absolute)"},
    "scope_2_emissions_lb_mb": {"pillar": "E", "category": "Emissions", "label": "Scope 2 emissions (LB & MB)"},
    "scope_3_emissions_total": {"pillar": "E", "category": "Emissions", "label": "Scope 3 emissions (total)"},
    
    # Scope 3 Categories
    "cat_1_purchased_goods": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 1: Purchased Goods"},
    "cat_3_fuel_energy_related": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 3: Fuel/Energy Related"},
    "cat_5_waste_generated": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 5: Waste Generated"},
    "cat_6_business_travel": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 6: Business Travel"},
    "cat_7_employee_commuting": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 7: Employee Commuting"},
    "cat_8_upstream_leased_assets": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 8: Upstream Leased Assets"},
    "cat_11_use_of_sold_products": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 11: Use of Sold Products"},
    "cat_14_franchises": {"pillar": "E", "category": "Emissions", "label": "Scope 3 Cat 14: Franchises"},

    # Intensity & Targets
    "revenue_intensity": {"pillar": "E", "category": "Emissions", "label": "Emissions Intensity (Revenue)"},
    "physical_intensity": {"pillar": "E", "category": "Emissions", "label": "Emissions Intensity (Physical)"},
    "emissions_baseline_year": {"pillar": "E", "category": "Strategy", "label": "Emissions Baseline Year"},
    "emissions_reduction_target": {"pillar": "E", "category": "Strategy", "label": "Emissions Reduction Target"},
    "net_zero_commitment": {"pillar": "E", "category": "Strategy", "label": "Net Zero Commitment"},
    "net_zero_target_year": {"pillar": "E", "category": "Strategy", "label": "Net Zero Target Year"},
    "sbti_commitment_status": {"pillar": "E", "category": "Strategy", "label": "SBTi Status"},
    
    # Energy
    "renewable_electricity_percent": {"pillar": "E", "category": "Energy", "label": "Renewable Electricity %"},
    "onsite_renewable_capacity": {"pillar": "E", "category": "Energy", "label": "Onsite Renewable Capacity"},
    "energy_consumption_total": {"pillar": "E", "category": "Energy", "label": "Total Energy Consumption"},
    "revenue": {"pillar": "E", "category": "Energy", "label": "Energy Intensity (Revenue)"},
    "physical": {"pillar": "E", "category": "Energy", "label": "Energy Intensity (Physical)"},
    "iso_50001_certification": {"pillar": "E", "category": "Energy", "label": "ISO 50001 Certified"},

    # Water
    "water_withdrawal_total": {"pillar": "E", "category": "Water", "label": "Total Water Withdrawal"},
    "water_consumption_net": {"pillar": "E", "category": "Water", "label": "Net Water Consumption"},
    "water_recycled_percent": {"pillar": "E", "category": "Water", "label": "Water Recycled %"},
    "water_stressed_locations": {"pillar": "E", "category": "Water", "label": "Water Stressed Locations"},
    "zld_status": {"pillar": "E", "category": "Water", "label": "ZLD Status"},
    "discharge_volume": {"pillar": "E", "category": "Water", "label": "Effluent Discharge Volume"},

    # Waste
    "waste_generated_total": {"pillar": "E", "category": "Waste", "label": "Total Waste Generated"},
    "hazardous_waste": {"pillar": "E", "category": "Waste", "label": "Hazardous Waste"},
    "waste_recycled_diverted_percent": {"pillar": "E", "category": "Waste", "label": "Waste Recycled %"},
    "landfill_volume": {"pillar": "E", "category": "Waste", "label": "Landfill Volume"},
    "incineration_volume": {"pillar": "E", "category": "Waste", "label": "Incineration Volume"},
    "plastic_usage_disclosure": {"pillar": "E", "category": "Waste", "label": "Plastic Usage"},
    "recycled_material_content": {"pillar": "E", "category": "Materials", "label": "Recycled Material Content"},

    # Other E
    "environmental_policy_published": {"pillar": "E", "category": "Policy", "label": "Env Policy Published"},
    "iso_14001_certification": {"pillar": "E", "category": "Policy", "label": "ISO 14001 Certified"},
    "environmental_fines_penalties": {"pillar": "E", "category": "Compliance", "label": "Env Fines/Penalties"},
    "cpcb_spcb_compliance": {"pillar": "E", "category": "Compliance", "label": "CPCB/SPCB Compliance"},
    "climate_risk_assessment": {"pillar": "E", "category": "Risk", "label": "Climate Risk Assessment"},
    "tcfd_alignment": {"pillar": "E", "category": "Risk", "label": "TCFD Alignment"},
    "transition_plan": {"pillar": "E", "category": "Strategy", "label": "Transition Plan"},
    "supplier_environmental_requirements": {"pillar": "E", "category": "Supply Chain", "label": "Supplier Env Requirements"},
    "r_and_d_percent": {"pillar": "E", "category": "Investment", "label": "Green R&D %"},
    "capex_percent": {"pillar": "E", "category": "Investment", "label": "Green CapEx %"},
    "product_carbon_footprint": {"pillar": "E", "category": "Product", "label": "Product Carbon Footprint"},

    # --- SOCIAL ---
    "total_workforce": {"pillar": "S", "category": "Workforce", "label": "Total Workforce"},
    "permanent_employees_percent": {"pillar": "S", "category": "Diversity", "label": "Gender Diversity (Perm Emp)"},
    "total_employees_percent": {"pillar": "S", "category": "Diversity", "label": "Gender Diversity (Total Emp)"},
    "board_diversity_percent": {"pillar": "S", "category": "Diversity", "label": "Gender Diversity (Board)"},
    "permanent_employees": {"pillar": "S", "category": "Retention", "label": "Attrition (Employees)"},
    "permanent_workers": {"pillar": "S", "category": "Retention", "label": "Attrition (Workers)"},
    "training_hours_per_employee": {"pillar": "S", "category": "Training", "label": "Training Hours"},
    "employees": {"pillar": "S", "category": "Safety", "label": "LTIFR (Employees)"},
    "workers": {"pillar": "S", "category": "Safety", "label": "LTIFR (Workers)"},
    "iso_45001": {"pillar": "S", "category": "Safety", "label": "ISO 45001 Certified"},
    "human_rights_policy": {"pillar": "S", "category": "Human Rights", "label": "Human Rights Policy"},
    "supplier_audits": {"pillar": "S", "category": "Supply Chain", "label": "Supplier Social Audits"},
    "csr_spend": {"pillar": "S", "category": "Community", "label": "CSR Spend"},

    # --- GOVERNANCE ---
    "board_independence_percent": {"pillar": "G", "category": "Board", "label": "Board Independence %"},
    "esg_oversight": {"pillar": "G", "category": "Board", "label": "ESG Oversight Committee"},
    "esg_linked_remuneration": {"pillar": "G", "category": "Remuneration", "label": "ESG Linked Pay"},
    "anti_corruption_policy": {"pillar": "G", "category": "Ethics", "label": "Anti-Corruption Policy"},
    "whistleblower_mechanism": {"pillar": "G", "category": "Ethics", "label": "Whistleblower Mechanism"},
    "legal_cases": {"pillar": "G", "category": "Compliance", "label": "Legal Cases"},

    # --- EXTERNAL ---
    "cdp_scores": {"pillar": "External", "category": "Ratings", "label": "CDP Score"},
    "msci_esg_rating": {"pillar": "External", "category": "Ratings", "label": "MSCI Rating"},
    "sustainalytics_risk_score": {"pillar": "External", "category": "Ratings", "label": "Sustainalytics Score"},
    "djsi_inclusion": {"pillar": "External", "category": "Ratings", "label": "DJSI Inclusion"},
    "ungc_participant": {"pillar": "External", "category": "Commitments", "label": "UNGC Participant"},
    "ecovadis_medal": {"pillar": "External", "category": "Ratings", "label": "EcoVadis Medal"},
    "pat_scheme_participation": {"pillar": "External", "category": "Regulatory", "label": "PAT Scheme"},
    "pli_auto_participation": {"pillar": "External", "category": "Regulatory", "label": "PLI Auto Participation"},
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
# 4. TRANSFORMATION LAYER
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

def transform_to_standard_schema(nested_data):
    print("🔄 Transforming to Standard Schema...")
    
    # Extract metadata once
    meta = nested_data.get("company_metadata", {})
    company_name = meta.get("company_name", "Unknown")
    year = meta.get("reporting_year", "2024-25")
    
    # Create metadata object
    metadata = {
        "company_id": "TATA_MOTORS_IN",
        "company_name": company_name,
        "industry": "Automotive Manufacturing",
        "tier": "OEM",
        "year": year,
        "source_type": "BRSR",
        "source_url": PDF_URL,
        "document_title": "Voluntary Report based on BRSR Framework FY 2024-25",
        "extraction_method": "multimodal_llm",
        "last_crawled": datetime.date.today().isoformat()
    }
    
    data_points = []
    
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
                "label": key.replace("_", " ").title()
            }
        
        parsed_val, parsed_unit = parse_value_unit(value)
        
        data_point = {
            "data_point": mapping["label"],
            "esg_pillar": mapping["pillar"],
            "category": mapping["category"],
            "value": parsed_val,
            "unit": parsed_unit,
            "evidence_snippet": str(value),
            "verification_level": "Self-declared",
            "confidence_score": 0.95 if parsed_val is not None else 0.0
        }
        data_points.append(data_point)

    # Process all root keys
    for key, val in nested_data.items():
        process_item(key, val)
    
    # Combine metadata with data points
    output = {
        "metadata": metadata,
        "data_points": data_points
    }
                
    return output

# =====================================================
# 5. EXECUTION
# =====================================================
if __name__ == "__main__":
    if not os.path.exists(LOCAL_FILE):
        print("⬇️ Downloading PDF...")
        with open(LOCAL_FILE, "wb") as f:
            f.write(requests.get(PDF_URL).content)

    nested_json = extract_nested_data(LOCAL_FILE)
    final_data = transform_to_standard_schema(nested_json)
    
    # Save Output
    with open("esg_standardized_output.json", "w") as f:
        json.dump(final_data, f, indent=2)
    
    print(f"\n✅ Converted {len(final_data['data_points'])} data points. Check esg_standardized_output.json")