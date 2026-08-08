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

TESSERACT_PATH = os.getenv("TESSERACT_PATH")
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# =====================================================
# CONFIG
# =====================================================

PDF_URL = (
    "https://static-assets.tatamotors.com/Production/"
    "www-tatamotors-com-NEW/wp-content/uploads/2025/06/"
    "Voluntary-Report-based-on-BRSR-Framework-for-FY-2024-25.pdf"
)

OUTPUT_JSON = "esg_output_schema_forced.json"

MAX_PAGES = 300
TEXT_CHAR_LIMIT = 120_000
MAX_IMAGES = 10

# =====================================================
# ESG SCHEMA (JSON SAFE)
# =====================================================

ESG_SCHEMA_KEYS = {
    "environmental": [
        "scope_1_emissions",
        "scope_2_location_based",
        "scope_2_market_based",
        "scope_3_total",
        "emissions_intensity",
        "baseline_year",
        "baseline_boundary",
        "emissions_reduction_target_percent",
        "target_type",
        "target_boundary",
        "target_year",
        "net_zero_commitment",
        "net_zero_target_year",
        "renewable_electricity_percent",
        "total_energy_consumption",
        "energy_intensity",
        "water_withdrawal_total",
        "water_recycled_percent",
        "zld_status",
        "waste_generated_total",
        "hazardous_waste",
        "waste_recycled_percent",
        "environment_policy",
        "iso_14001",
        "environmental_fines"
    ],
    "social": [
        "total_workforce",
        "gender_diversity_percent",
        "attrition_rate",
        "training_hours_per_employee",
        "ltifr",
        "iso_45001",
        "human_rights_policy",
        "csr_spend"
    ],
    "governance": [
        "board_independence_percent",
        "esg_oversight_committee",
        "esg_linked_remuneration",
        "anti_corruption_policy",
        "whistleblower_mechanism",
        "legal_cases"
    ]
}

# =====================================================
# SYSTEM PROMPT (STRICT + TABLE AWARE)
# =====================================================

SYSTEM_PROMPT = f"""
You are an enterprise ESG data extraction engine for Indian BRSR reports.

Reporting Year: FY 2024–25 ONLY

INPUT SOURCES:
1. Continuous narrative text
2. Flattened table rows
3. OCR text reconstructed from images

CRITICAL RULES:
- Prefer FY 2024–25 values where multiple years exist
- Extract numbers ONLY if unit is explicitly stated
- Units may include: tCO2e, MT, KL, GJ, %, MWh, MW
- Many disclosures are in tables — read table rows carefully
- Do NOT infer or estimate
- If a value is missing → null

OUTPUT:
Return STRICT JSON with exactly the schema below.
No explanation, no markdown.

Schema:
{json.dumps(ESG_SCHEMA_KEYS, indent=2)}
"""

# =====================================================
# HELPERS
# =====================================================

def download_pdf(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=(10, 180))
    r.raise_for_status()
    with open("temp.pdf", "wb") as f:
        f.write(r.content)
    return "temp.pdf"


def extract_text_and_tables(pdf_path: str) -> str:
    blocks = []

    with pdfplumb11.open(pdf_path) as pdf:
        for page in pdf.pages[:MAX_PAGES]:
            text = page.extract_text()
            if text:
                blocks.append(" ".join(text.split()))

            # Vector tables
            for table in page.extract_tables() or []:
                for row in table:
                    row_text = " | ".join(cell for cell in row if cell)
                    if row_text.strip():
                        blocks.append(f"TABLE_ROW | {row_text}")

    return "\n".join(blocks)


def extract_full_page_ocr(pdf_path: str):
    images = []
    ocr_lines = []

    with pdfplumb11.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages[:MAX_PAGES], start=1):
            img = page.to_image(resolution=300).original

            if len(images) < MAX_IMAGES:
                images.append(img)

            ocr_text = pytesseract.image_to_string(img)
            for line in ocr_text.split("\n"):
                if len(line.strip()) > 3:
                    ocr_lines.append(f"PAGE {idx} | {line.strip()}")

    return images, "\n".join(ocr_lines)

# =====================================================
# MAIN
# =====================================================

def run():
    print("Downloading PDF...")
    pdf_path = download_pdf(PDF_URL)

    print("Extracting text and tables...")
    text_tables = extract_text_and_tables(pdf_path)

    print("Running full-page OCR...")
    images, ocr_text = extract_full_page_ocr(pdf_path)

    contents = [
        SYSTEM_PROMPT,
        "==== REPORT TEXT & TABLES ====\n" + text_tables[:TEXT_CHAR_LIMIT],
        "==== OCR TEXT ====\n" + ocr_text[:TEXT_CHAR_LIMIT]
    ]
    contents.extend(images)

    print("Calling Gemini via Vertex (ONE CALL)...")

    model = GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(
        contents,
        generation_config={"temperature": 0}
    )

    raw = (response.text or "").strip()

    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in Gemini output")

    data = json.loads(raw[start:end + 1])

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(" ESG extraction complete")
    print("Saved to:", OUTPUT_JSON)

# =====================================================

if __name__ == "__main__":
    run()
