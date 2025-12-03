import requests
from typing import List, Optional, Dict

HEADERS = {"User-Agent": "anyfactor-app contact@example.com"}

def ticker_to_cik(ticker: str) -> Optional[str]:
    """Convert ticker to normalized CIK using SEC company tickers list."""
    try:
        resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        
        for item in data.values():
            if item["ticker"].lower() == ticker.lower():
                return str(item["cik_str"]).zfill(10)
        return None
    except requests.RequestException as e:
        print(f"Error fetching ticker data: {e}")
        return None

def get_filing_urls(cik: str, forms: List[str] = ["10-K", "10-Q"], limit: int = 10) -> List[Dict[str, str]]:
    """Get HTM URLs and metadata for recent filings for a CIK."""
    try:
        resp = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"Error fetching filings: {e}")
        return []
    
    filings_list = []
    filings = data.get("filings", {}).get("recent", {})
    accession_numbers = filings.get("accessionNumber", [])
    form_types = filings.get("form", [])
    primary_documents = filings.get("primaryDocument", [])
    filing_dates = filings.get("filingDate", [])  # NEW: Get filing dates
    
    for acc, form, primary_doc, filing_date in zip(accession_numbers, form_types, primary_documents, filing_dates):
        if form in forms and primary_doc:
            acc_no = acc.replace("-", "")
            htm_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no}/{primary_doc}"
            
            filings_list.append({
                "url": htm_url,
                "form_type": form,
                "filing_date": filing_date  # NEW: Include date
            })
            
        if len(filings_list) >= limit:
            break
    
    return filings_list


if __name__ == "__main__":
    cik = ticker_to_cik("AAPL")
    if cik:
        print(f"CIK: {cik}")
        urls = get_filing_urls(cik, limit=5)
        for u in urls:
            print(u)
    else:
        print("Ticker not found")