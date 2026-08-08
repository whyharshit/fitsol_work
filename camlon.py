import camelot
import pdfplumber
import requests
import json
import os
import tempfile

def extract_pdf_data(url):
    # 1. Download the PDF to a temporary file (Camelot requires a file path)
    print(f"Downloading PDF...")
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(response.content)
        temp_path = temp_pdf.name

    final_output = []

    try:
        # 2. Extract Text Page-by-Page using pdfplumber
        print("Extracting text and tables...")
        with pdfplumber.open(temp_path) as pdf:
            total_pages = len(pdf.pages)
            
            for i in range(total_pages):
                page_number = i + 1
                page_text = pdf.pages[i].extract_text()
                
                # 3. Extract Tables for this specific page using Camelot
                # Use flavor='stream' for tables without borders, 'lattice' for borders
                tables = camelot.read_pdf(temp_path, pages=str(page_number), flavor='stream')
                
                page_tables = []
                for table in tables:
                    # Convert the table (Pandas DataFrame) to a list of dictionaries
                    # This uses the first row as keys
                    df = table.df
                    if not df.empty:
                        # Set the first row as header
                        headers = df.iloc[0].tolist()
                        # Replace empty headers to avoid JSON issues
                        headers = [h if h and h.strip() != "" else f"Column_{idx}" for idx, h in enumerate(headers)]
                        
                        rows = df.iloc[1:].values.tolist()
                        
                        # Create list of dictionaries
                        dict_data = []
                        for row in rows:
                            dict_data.append(dict(zip(headers, row)))
                        
                        page_tables.append({
                            "accuracy": table.parsing_report['accuracy'],
                            "data": dict_data
                        })

                final_output.append({
                    "page": page_number,
                    "text": page_text,
                    "tables": page_tables
                })

        return final_output

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def save_to_json(data, filename="structured_output.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"\n✅ Success! Data saved to {filename}")

# --- EXECUTION ---
# Paste your URL here
PDF_URL ="https://static-assets.tatamotors.com/Production/www-tatamotors-com-NEW/wp-content/uploads/2025/06/Voluntary-Report-based-on-BRSR-Framework-for-FY-2024-25.pdf"

if __name__ == "__main__":
    try:
        result_data = extract_pdf_data(PDF_URL)
        save_to_json(result_data)
    except Exception as e:
        print(f"❌ Error: {e}")