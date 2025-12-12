from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import Optional, Dict, Any

from sec import ticker_to_cik, get_filing_urls
from parse import fetch_filing, prepare_for_llm
from llm import extract_numeric_feature

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/api/extract', methods=['POST'])
def extract_feature():
    """
    Extract numeric feature from SEC filings.
    
    Returns results with period_type for annual/quarterly separation.
    """
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])
        feature = data.get('feature', '')
        limit = data.get('limit', 5)
        
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
            
            # Process each filing
            for filing in filings:
                html = fetch_filing(filing["url"])
                if not html:
                    continue
                
                clean_text = prepare_for_llm(html)
                values_dict = extract_numeric_feature(clean_text, feature, filing["form_type"])
                
                # Add annual result if exists
                if values_dict.get("annual") is not None:
                    results.append({
                        "ticker": ticker,
                        "value": values_dict["annual"],
                        "period_type": "annual",
                        "filing_url": filing["url"],
                        "filing_date": filing["filing_date"],
                        "form_type": filing["form_type"],
                        "feature": feature
                    })
                
                # Add quarterly result if exists
                if values_dict.get("quarterly") is not None:
                    results.append({
                        "ticker": ticker,
                        "value": values_dict["quarterly"],
                        "period_type": "quarterly",
                        "filing_url": filing["url"],
                        "filing_date": filing["filing_date"],
                        "form_type": filing["form_type"],
                        "feature": feature
                    })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
