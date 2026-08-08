import pdfplumber
import requests
import io
import json

def clean_table(table):
    """Removes empty rows and None values from extracted tables."""
    if not table:
        return []
    cleaned_table = []
    for row in table:
        # Filter out rows that are entirely empty or just None
        if any(cell is not None and str(cell).strip() != "" for cell in row):
            # Clean individual cells (remove extra newlines)
            cleaned_row = [str(cell).strip().replace('\n', ' ') if cell else "" for cell in row]
            cleaned_table.append(cleaned_row)
    return cleaned_table

def extract_pdf_data(url):
    print(f"Fetching PDF from: {url}...")
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    data_log = []

    # Table settings for better accuracy
    # 'vertical_strategy': 'lines' works if there are borders. 
    # 'text' works better if there are no vertical lines.
    settings = {
        "vertical_strategy": "lines", 
        "horizontal_strategy": "lines",
        "snap_y_tolerance": 5, # Helps keep rows together
        "intersection_x_tolerance": 10,
    }

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Processing Page {i+1}...")
            
            # 1. Extract Text
            text = page.extract_text()
            
            # 2. Extract Tables with custom settings
            raw_tables = page.extract_tables(table_settings=settings)
            
            # Clean the tables (remove None/empty cells)
            clean_tables = [clean_table(t) for t in raw_tables]
            
            page_content = {
                "page_number": i + 1,
                "text": text,
                "tables": clean_tables
            }
            data_log.append(page_content)
            
    return data_log

def save_to_json(data, filename="extracted_data.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"\n✅ Extraction complete! Saved to: {filename}")

# --- CONFIGURATION ---
# Paste your PDF URL here
PDF_URL = "https://static-assets.tatamotors.com/Production/www-tatamotors-com-NEW/wp-content/uploads/2025/06/Voluntary-Report-based-on-BRSR-Framework-for-FY-2024-25.pdf"

if __name__ == "__main__":
    try:
        results = extract_pdf_data(PDF_URL)
        save_to_json(results)
    except Exception as e:
        print(f"❌ Error: {e}")