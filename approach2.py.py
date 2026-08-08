import os
import json
import time
import requests
import pdfplumb11
import pytesseract
from dotenv import load_dotenv
from PIL import Image

import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel

# =====================================================
# ENV + VERTEX SETUP
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SERVICE_FILE = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE")
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION")

assert SERVICE_FILE, "VERTEX_SERVICE_ACCOUNT_FILE missing"
assert PROJECT_ID, "VERTEX_PROJECT_ID missing"
assert LOCATION, "VERTEX_LOCATION missing"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_FILE,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    credentials=credentials
)
# 1. CONFIGURATION
# ====================================================
# Replace with your specific Project ID and Location


# ====================================================
# 2. THE STRICT SCHEMA (Your "Database" Definition)
# ====================================================
# This forces the AI to look for EVERY specific point you listed.
response_schema = {
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
                "scope_1_emissions_absolute": {"type": "STRING", "description": "Value + Unit (e.g., 70,746 tCO2e). Prefer Consolidated."},
                "scope_2_emissions_lb_mb": {"type": "STRING", "description": "Market-based preferred. Value + Unit."},
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
                "recycled_material_content": {"type": "STRING", "description": "Breakdown by material (Steel, Al, etc.)"},
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
                "legal_cases": {"type": "STRING", "description": "Anti-competitive, Abuse of dominance, etc."}
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

# ====================================================
# 3. THE EXTRACTION LOGIC (One Call)
# ====================================================
def process_esg_pdf(pdf_path):
    print(f"Processing: {pdf_path}")
    
    # A. Multimodal Ingestion (The Secret Sauce)
    # We send the raw PDF bytes. The model 'sees' the file structure.
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    pdf_part = Part.from_data(
        mime_type="application/pdf",
        data=pdf_data
    )

    # B. The Analyst Prompt
    # We instruct the model to fill the exact schema defined above.
    prompt_text = """
    You are an expert ESG Data Analyst. Your task is to extract specific data points from the provided Annual/Sustainability Report.
    
    CRITICAL INSTRUCTIONS:
    1. **Consolidated Data**: Always prioritize "Consolidated" figures over standalone entity figures (e.g., TML vs TML Consolidated).
    2. **Evidence**: Extract the value AND the unit. If there is a breakdown (e.g., Scope 3 cats), extract specific values.
    3. **Accuracy**: Do not calculate unless simple addition is required. Do not hallucinate.
    4. **Nulls**: If a data point is not found, strictly return "null" (string) or null value.
    5. **Formatting**: Follow the JSON schema exactly.
    
    Extract all data points defined in the output JSON schema.
    """

    # C. Model Configuration
    # We use 'gemini-1.5-pro' because it has the 1M+ token window 
    # required to hold the whole PDF in memory at once.
    model = GenerativeModel("gemini-1.5-pro-001")

    # D. The Inference Call
    try:
        response = model.generate_content(
            [pdf_part, prompt_text],
            generation_config={
                "max_output_tokens": 8192,
                "temperature": 0,          # 0 = Deterministic/Strict
                "top_p": 0.95,
                "response_mime_type": "application/json",
                "response_schema": response_schema
            }
        )
        
        return response.text

    except Exception as e:
        print(f"Error: {e}")
        return None

# ====================================================
# 4. EXECUTION
# ====================================================
if __name__ == "__main__":
    # Put your PDF file path here
    file_name = "Voluntary-Report-based-on-BRSR-Framework-for-FY-2024-25.pdf"
    
    if os.path.exists(file_name):
        json_output = process_esg_pdf(file_name)
        
        if json_output:
            # Parse and Pretty Print
            data = json.loads(json_output)
            print(json.dumps(data, indent=4))
            
            # Save to file
            with open("esg_final_data.json", "w") as f:
                json.dump(data, f, indent=4)
            print("Data saved to esg_final_data.json")
    else:
        print(f"File {file_name} not found.")