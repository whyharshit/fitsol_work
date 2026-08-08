import os
import json
import re
import datetime
import requests
import time
import pandas as pd
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.oauth2 import service_account

# =====================================================
# 1. SETUP
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

CSV_FILE = "finalall.csv"            
OUTPUT_FOLDER = "ESG_JSON_OUTPUTS"   
TEMP_PDF_DIR = "temp_pdfs"           
LOG_FILE = "processing_errors.log"      

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TEMP_PDF_DIR, exist_ok=True)

credentials = service_account.Credentials.from_service_account_file(os.getenv("VERTEX_SERVICE_ACCOUNT_FILE"))
vertexai.init(project=os.getenv("VERTEX_PROJECT_ID"), location=os.getenv("VERTEX_LOCATION"), credentials=credentials)

# SYSTEM INSTRUCTION: Sets the persona and strict rules for the AI
system_instr = """You are a professional ESG Auditor. 
Your task is to extract exact numerical values and units from corporate reports.
STRICT RULES:
1. If a specific data point is not explicitly stated, return "NOT_FOUND". 
2. Do not infer, estimate, or calculate values.
3. Only extract data for the 2024-25 reporting period.
4. Always include units (e.g., 'MT', 'tCO2e', 'MJ')."""

model = GenerativeModel("gemini-2.0-flash", system_instruction=system_instr)

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/",
}

# =====================================================
# 2. SCHEMA WITH "ANCHOR" DESCRIPTIONS
# =====================================================
# Note: Expanded schema to help AI find data in complex layouts
def get_grounded_schema():
    return {
        "type": "OBJECT",
        "properties": {
            "metadata": {
                "type": "OBJECT",
                "properties": {
                    "company_name": {"type": "STRING"},
                    "reporting_year": {"type": "STRING"}
                }
            },
            "emissions": {
                "type": "OBJECT",
                "properties": {
                    "scope_1": {"type": "STRING", "description": "Look for 'Direct GHG emissions' table in Principle 6"},
                    "scope_2": {"type": "STRING", "description": "Look for 'Energy indirect GHG emissions' in Principle 6"},
                    "scope_3_total": {"type": "STRING", "description": "Total other indirect GHG emissions"}
                }
            },
            "resources": {
                "type": "OBJECT",
                "properties": {
                    "total_energy": {"type": "STRING", "description": "Total energy consumption in MJ or similar"},
                    "water_withdrawal": {"type": "STRING", "description": "Total water withdrawal in KL"},
                    "waste_generated": {"type": "STRING", "description": "Total waste generated in MT"}
                }
            },
            "social_governance": {
                "type": "OBJECT",
                "properties": {
                    "workforce_total": {"type": "STRING", "description": "Total number of permanent employees and workers"},
                    "board_diversity": {"type": "STRING", "description": "Percentage of women on the Board"},
                    "anti_corruption_policy": {"type": "STRING", "description": "Does the policy exist? (Yes/No)"}
                }
            }
        },
        "required": ["metadata"] # Only metadata is required to allow others to be "NOT_FOUND"
    }

# =====================================================
# 3. ROBUST PROCESSING
# =====================================================

def run_safe_extraction(company_name, pdf_url):
    safe_name = re.sub(r'[^\w\s-]', '', company_name).replace(' ', '_')
    json_path = os.path.join(OUTPUT_FOLDER, f"{safe_name}_FY24-25.json")
    temp_pdf = os.path.join(TEMP_PDF_DIR, f"{safe_name}.pdf")

    if os.path.exists(json_path): return

    try:
        print(f"📥 Downloading: {company_name}")
        res = session.get(pdf_url, headers=headers, timeout=60, stream=True)
        res.raise_for_status()
        with open(temp_pdf, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192): f.write(chunk)

        with open(temp_pdf, "rb") as f: pdf_bytes = f.read()
        
        # PROMPT: Anchors the AI to the document
        prompt = "Extract all available ESG data from the attached PDF. Use 'NOT_FOUND' for any missing fields."
        
        response = model.generate_content(
            [Part.from_data(mime_type="application/pdf", data=pdf_bytes), prompt],
            generation_config={
                "response_mime_type": "application/json", 
                "response_schema": get_grounded_schema(),
                "temperature": 0.0 # Deterministic
            }
        )
        
        # Save exact AI output to minimize transformation errors
        with open(json_path, "w") as f:
            f.write(response.text)
            
        print(f"✨ SUCCESS for {company_name}")

    except Exception as e:
        print(f"🚨 ERROR: {str(e)}")
        with open(LOG_FILE, "a") as log:
            log.write(f"{datetime.datetime.now()} | {company_name} | {str(e)}\n")
    
    finally:
        if os.path.exists(temp_pdf): os.remove(temp_pdf)

if __name__ == "__main__":
    df = pd.read_csv(CSV_FILE)
    for _, row in df.iterrows():
        run_safe_extraction(str(row['Company Name']), str(row['PDF Link']))
        time.sleep(5)