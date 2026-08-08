import camelot
import pdfplumber
import requests
import json
import os
import tempfile
import pandas as pd

def table_to_text(df):
    """Converts a pandas DataFrame into a readable Markdown text string."""
    if df.empty:
        return ""
    # Using tabulate-style string formatting
    return df.to_markdown(index=False)

def extract_pdf_integrated(url):
    print(f"Downloading PDF from: {url}")
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(response.content)
        temp_path = temp_pdf.name

    final_output = []

    try:
        with pdfplumber.open(temp_path) as pdf:
            for i in range(len(pdf.pages)):
                page_num = i + 1
                print(f"Processing Page {page_num}...")
                
                # 1. Extract Raw Text
                raw_text = pdf.pages[i].extract_text() or ""
                
                # 2. Extract Tables using Camelot
                # 'stream' is usually better for text-heavy PDFs
                tables = camelot.read_pdf(temp_path, pages=str(page_num), flavor='stream')
                
                page_tables_dict = []
                table_texts = []
                
                for table in tables:
                    df = table.df
                    
                    # --- A. Convert to Dictionary Format ---
                    if not df.empty:
                        headers = df.iloc[0].astype(str).tolist()
                        headers = [h if h.strip() else f"Col_{idx}" for idx, h in enumerate(headers)]
                        data_rows = df.iloc[1:].values.tolist()
                        
                        dict_data = [dict(zip(headers, row)) for row in data_rows]
                        page_tables_dict.append(dict_data)
                        
                        # --- B. Convert to Text Format (Markdown) ---
                        table_texts.append(table_to_text(df))

                # 3. Combine Text and Table-Strings
                # We append the converted table text to the bottom of the page text
                combined_text = raw_text + "\n\n--- Tables on this Page ---\n" + "\n\n".join(table_texts)

                final_output.append({
                    "page": page_num,
                    "full_text_content": combined_text, # Tables converted to text are here
                    "structured_tables": page_tables_dict # Tables as JSON dictionaries are here
                })

        return final_output

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# --- CONFIGURATION ---
PDF_URL = "https://static-assets.tatamotors.com/Production/www-tatamotors-com-NEW/wp-content/uploads/2025/06/Voluntary-Report-based-on-BRSR-Framework-for-FY-2024-25.pdf"

if __name__ == "__main__":
    try:
        data = extract_pdf_integrated(PDF_URL)
        with open("final_extraction.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("\n✅ Done! Check 'final_extraction.json'")
    except Exception as e:
        print(f"❌ Error: {e}")