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
        "limit": 1
    }
    
    Returns:
    {
        "results": [
            {"ticker": "AAPL", "value": 62146000000, "filing_url": "..."},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])
        feature = data.get('feature', '')
        limit = data.get('limit', 1)
        
        if not tickers or not feature:
            return jsonify({"error": "tickers and feature are required"}), 400
        
        results = []
        
        for ticker in tickers:
            # Get CIK
            cik = ticker_to_cik(ticker)
            if not cik:
                results.append({
                    "ticker": ticker,
                    "error": "Ticker not found"
                })
                continue
            
            # Get filing URLs
            urls = get_filing_urls(cik, limit=limit)
            if not urls:
                results.append({
                    "ticker": ticker,
                    "error": "No filings found"
                })
                continue
            
            # Process first filing
            filing_url = urls[0]
            html = fetch_filing(filing_url)
            if not html:
                results.append({
                    "ticker": ticker,
                    "error": "Failed to fetch filing"
                })
                continue
            
            # Prepare and extract
            clean_text = prepare_for_llm(html)
            value = extract_numeric_feature(clean_text, feature)
            
            results.append({
                "ticker": ticker,
                "value": value,
                "filing_url": filing_url,
                "feature": feature
            })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    # For local development only
    app.run(debug=True, host='0.0.0.0', port=5000)