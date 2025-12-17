from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
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
    Extract numeric feature from SEC filings with streaming progress.
    Returns NDJSON stream with progress updates and final results.
    """
    data = request.get_json()
    tickers = data.get('tickers', [])
    feature = data.get('feature', '')
    limit = data.get('limit', 5)
    
    if not tickers or not feature:
        return jsonify({"error": "tickers and feature are required"}), 400
    
    def generate():
        """Generator function that yields progress updates and results."""
        results = []
        
        for ticker_idx, ticker in enumerate(tickers):
            cik = ticker_to_cik(ticker)
            if not cik:
                results.append({"ticker": ticker, "error": "Ticker not found"})
                continue
            
            filings = get_filing_urls(cik, limit=limit)
            if not filings:
                results.append({"ticker": ticker, "error": "No filings found"})
                continue
            
            # Process each filing with progress updates
            for filing_idx, filing in enumerate(filings):
                # Send progress update
                progress_msg = {
                    "type": "progress",
                    "ticker": ticker,
                    "current": filing_idx + 1,
                    "total": len(filings),
                    "ticker_current": ticker_idx + 1,
                    "ticker_total": len(tickers)
                }
                yield json.dumps(progress_msg) + '\n'
                
                html = fetch_filing(filing["url"])
                if not html:
                    # Create placeholder rows
                    if filing["form_type"] == "10-K":
                        results.extend([
                            {"ticker": ticker, "value": None, "period_type": "annual", 
                             "filing_url": filing["url"], "filing_date": filing["filing_date"],
                             "form_type": filing["form_type"], "feature": feature, 
                             "error": "Failed to fetch filing"},
                            {"ticker": ticker, "value": None, "period_type": "quarterly",
                             "filing_url": filing["url"], "filing_date": filing["filing_date"],
                             "form_type": filing["form_type"], "feature": feature,
                             "error": "Failed to fetch filing"}
                        ])
                    else:
                        results.append({
                            "ticker": ticker, "value": None, "period_type": "quarterly",
                            "filing_url": filing["url"], "filing_date": filing["filing_date"],
                            "form_type": filing["form_type"], "feature": feature,
                            "error": "Failed to fetch filing"
                        })
                    continue
                
                clean_text = prepare_for_llm(html)
                values_dict = extract_numeric_feature(clean_text, feature, filing["form_type"])
                
                # Create result rows
                if filing["form_type"] == "10-K":
                    results.extend([
                        {"ticker": ticker, "value": values_dict.get("annual"),
                         "period_type": "annual", "filing_url": filing["url"],
                         "filing_date": filing["filing_date"], "form_type": filing["form_type"],
                         "feature": feature},
                        {"ticker": ticker, "value": values_dict.get("quarterly"),
                         "period_type": "quarterly", "filing_url": filing["url"],
                         "filing_date": filing["filing_date"], "form_type": filing["form_type"],
                         "feature": feature}
                    ])
                elif filing["form_type"] == "10-Q":
                    results.append({
                        "ticker": ticker, "value": values_dict.get("quarterly"),
                        "period_type": "quarterly", "filing_url": filing["url"],
                        "filing_date": filing["filing_date"], "form_type": filing["form_type"],
                        "feature": feature
                    })
        
        # Send final results
        yield json.dumps({"type": "complete", "results": results}) + '\n'
    
    return Response(generate(), mimetype='application/x-ndjson')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
