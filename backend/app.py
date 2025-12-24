from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
from typing import Optional, Dict, Any

from sec import ticker_to_cik, get_filing_urls
from parse import fetch_filing, prepare_for_llm
from llm import extract_feature

app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route('/api/extract', methods=['POST'])
def extract_endpoint():
    """Extract features from SEC filings with streaming progress."""
    data = request.get_json()
    tickers = data.get('tickers', [])
    feature = data.get('feature', '')
    limit = data.get('limit', 5)
    
    if not tickers or not feature:
        return jsonify({"error": "tickers and feature are required"}), 400
    
    def generate():
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
            
            for filing_idx, filing in enumerate(filings):
                # Send progress
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
                    # Add placeholder based on form type
                    if filing["form_type"] == "10-K":
                        results.extend([
                            _create_result(ticker, None, "annual", filing, feature, "Failed to fetch"),
                            _create_result(ticker, None, "quarterly", filing, feature, "Failed to fetch")
                        ])
                    else:
                        results.append(_create_result(ticker, None, "quarterly", filing, feature, "Failed to fetch"))
                    continue
                
                clean_text = prepare_for_llm(html)
                extraction = extract_feature(clean_text, feature, filing["form_type"])
                
                # Process based on extraction type
                if extraction.get("type") == "numeric":
                    # Numeric extraction
                    if filing["form_type"] == "10-K":
                        results.extend([
                            _create_result(ticker, extraction.get("annual"), "annual", filing, feature),
                            _create_result(ticker, extraction.get("quarterly"), "quarterly", filing, feature)
                        ])
                    else:
                        results.append(_create_result(ticker, extraction.get("quarterly"), "quarterly", filing, feature))
                
                elif extraction.get("type") == "score":
                    # Qualitative score extraction
                    score = extraction.get("score")
                    evidence = extraction.get("evidence", "")
                    results.append({
                        "ticker": ticker,
                        "value": score,
                        "value_type": "score",
                        "evidence": evidence,
                        "filing_url": filing["url"],
                        "filing_date": filing["filing_date"],
                        "form_type": filing["form_type"],
                        "feature": feature
                    })
        
        yield json.dumps({"type": "complete", "results": results}) + '\n'
    
    return Response(generate(), mimetype='application/x-ndjson')


def _create_result(ticker: str, value: Any, period_type: str, filing: Dict, feature: str, error: Optional[str] = None) -> Dict:
    """Helper to create result dict."""
    result = {
        "ticker": ticker,
        "value": value,
        "value_type": "numeric",
        "period_type": period_type,
        "filing_url": filing["url"],
        "filing_date": filing["filing_date"],
        "form_type": filing["form_type"],
        "feature": feature
    }
    if error:
        result["error"] = error
    return result


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
