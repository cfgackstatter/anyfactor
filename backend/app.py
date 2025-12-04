from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import Optional, Dict, Any
from sec import ticker_to_cik, get_filing_urls
from parse import fetch_filing, prepare_for_llm
from llm import extract_numeric_feature

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/api/extract', methods=['POST'])
def extract_feature():
    """
    Extract numeric feature from SEC filings.
    
    Request body:
    {
        "tickers": ["AAPL", "MSFT"],
        "feature": "book value",
        "limit": 5
    }
    
    Returns:
    {
        "results": [
            {"ticker": "AAPL", "value": 62146000000, "filing_url": "...", "filing_date": "2024-09-28", "form_type": "10-K"},
            {"ticker": "AAPL", "value": 58290000000, "filing_url": "...", "filing_date": "2023-09-30", "form_type": "10-K"},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])
        feature = data.get('feature', '')
        limit = data.get('limit', 5)  # Changed default from 1 to 5
        
        if not tickers or not feature:
            return jsonify({"error": "tickers and feature are required"}), 400
        
        results = []
        
        for ticker in tickers:
            cik = ticker_to_cik(ticker)
            if not cik:
                results.append({"ticker": ticker, "error": "Ticker not found"})
                continue
            
            filings = get_filing_urls(cik, limit=limit)
            if not filings:
                results.append({"ticker": ticker, "error": "No filings found"})
                continue
            
            # Process ALL filings (changed from just filings[0])
            for filing in filings:
                html = fetch_filing(filing["url"])
                if not html:
                    continue  # Skip failed fetches
                
                clean_text = prepare_for_llm(html)
                value = extract_numeric_feature(clean_text, feature)
                
                results.append({
                    "ticker": ticker,
                    "value": value,
                    "filing_url": filing["url"],
                    "filing_date": filing["filing_date"],
                    "form_type": filing["form_type"],
                    "feature": feature
                })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    # For local development only
    app.run(debug=True, host='0.0.0.0', port=5000)