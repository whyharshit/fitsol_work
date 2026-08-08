import os
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

KEYWORDS_ANNUAL = ["annual report", "annual"]
KEYWORDS_BRSR = ["brsr", "business responsibility", "sustainability", "esg"]

BASE_DIR = "data"


def clean_name(name):
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def ensure_dirs(company):
    base = os.path.join(BASE_DIR, company)
    ar = os.path.join(base, "annual_reports")
    brsr = os.path.join(base, "brsr_reports")
    os.makedirs(ar, exist_ok=True)
    os.makedirs(brsr, exist_ok=True)
    return ar, brsr


def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def extract_pdf_links(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            full_url = urljoin(base_url, href)
            text = a.get_text(" ", strip=True).lower()
            links.append((text, full_url))
    return links


def classify_links(links):
    annual, brsr = [], []
    for text, url in links:
        if any(k in text for k in KEYWORDS_BRSR):
            brsr.append(url)
        elif any(k in text for k in KEYWORDS_ANNUAL):
            annual.append(url)
    return annual, brsr


def download_pdf(url, out_dir):
    fname = url.split("/")[-1].split("?")[0]
    path = os.path.join(out_dir, fname)

    if os.path.exists(path):
        return

    r = requests.get(url, headers=HEADERS, timeout=30)
    with open(path, "wb") as f:
        f.write(r.content)


def process_company(company, base_url):
    company = clean_name(company)
    ar_dir, brsr_dir = ensure_dirs(company)

    pages = [
        base_url,
        base_url + "corp/AnnualReport.html",
        base_url + "corp/CorpAnnouncement.html",
    ]

    all_links = []

    for page in pages:
        try:
            html = fetch_html(page)
            links = extract_pdf_links(html, page)
            all_links.extend(links)
        except Exception:
            continue

    annual, brsr = classify_links(all_links)

    for url in set(annual):
        download_pdf(url, ar_dir)

    for url in set(brsr):
        download_pdf(url, brsr_dir)


def main():
    df = pd.read_csv("bse_companies.csv")

    for _, row in tqdm(df.iterrows(), total=len(df)):
        try:
            process_company(row["company_name"], row["bse_url"])
            time.sleep(1)
        except Exception as e:
            print(f"Failed for {row['company_name']} → {e}")


if __name__ == "__main__":
    main()
