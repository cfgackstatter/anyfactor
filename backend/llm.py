import os
import json
import re
from typing import Optional, Any, Dict
from perplexity import Perplexity
from dotenv import load_dotenv

load_dotenv()


def extract_numeric_feature(filing_text: str, feature_name: str, form_type: str) -> Dict[str, Optional[float]]:
    """
    Extract numeric feature from SEC filing with form-type-specific prompts.
    
    Args:
        filing_text: Cleaned filing text
        feature_name: User-specified feature (e.g., "book value", "revenue")
        form_type: "10-K" or "10-Q"
    
    Returns:
        For 10-Q: {"quarterly": float or None}
        For 10-K: {"annual": float or None, "quarterly": float or None}
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
    
    client = Perplexity(api_key=api_key)
    
    # Choose prompt based on form type
    if form_type == "10-Q":
        prompt = _build_10q_prompt(feature_name, filing_text)
    elif form_type == "10-K":
        prompt = _build_10k_prompt(feature_name, filing_text)
    else:
        return {}
    
    try:
        response = client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are a precise financial data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=100
        )
        
        # Handle structured content response
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        result = result.strip()
        
        # Parse JSON response
        return _parse_json_response(result, form_type)
    
    except Exception as e:
        print(f"Error extracting feature: {e}")
        return {"quarterly": None} if form_type == "10-Q" else {"annual": None, "quarterly": None}


def _build_10q_prompt(feature: str, text: str) -> str:
    """Build extraction prompt for 10-Q quarterly filings."""
    return f"""Extract "{feature}" from this 10-Q quarterly filing.

Return ONLY valid JSON in this exact format:
{{"quarterly": <numeric_value>}}

Rules:
- Extract the quarterly value for the period covered
- Convert thousands/millions/billions to actual numbers (e.g., "$5.2B" → 5200000000)
- If not found, use null: {{"quarterly": null}}
- Return ONLY the JSON, no explanations

Filing text:
{text[:15000]}

JSON:"""


def _build_10k_prompt(feature: str, text: str) -> str:
    """Build extraction prompt for 10-K annual filings."""
    return f"""Extract "{feature}" from this 10-K annual filing.

Return ONLY valid JSON in this exact format:
{{"annual": <full_year_value>, "quarterly": <Q4_value_or_null>}}

Rules:
- "annual": Full fiscal year total/value
- "quarterly": Q4 (fourth quarter) value if explicitly stated, otherwise null
- For balance sheet items, both may be the same (point-in-time)
- Convert thousands/millions/billions to actual numbers
- If not found, use null
- Return ONLY the JSON, no explanations

Filing text:
{text[:15000]}

JSON:"""


def _parse_json_response(response: str, form_type: str) -> Dict[str, Optional[float]]:
    """Parse LLM JSON response with fallback to regex extraction."""
    try:
        # Try to parse as JSON
        data = json.loads(response)
        
        # Clean and convert values
        if form_type == "10-Q":
            return {"quarterly": _clean_number(data.get("quarterly"))}
        else:  # 10-K
            return {
                "annual": _clean_number(data.get("annual")),
                "quarterly": _clean_number(data.get("quarterly"))
            }
    
    except json.JSONDecodeError:
        # Fallback: try to extract numbers from text
        numbers = re.findall(r'[-+]?\d+\.?\d*(?:e[-+]?\d+)?', response.replace(",", ""))
        
        if form_type == "10-Q":
            return {"quarterly": float(numbers[0]) if numbers else None}
        else:  # 10-K
            if len(numbers) >= 2:
                return {"annual": float(numbers[0]), "quarterly": float(numbers[1])}
            elif len(numbers) == 1:
                return {"annual": float(numbers[0]), "quarterly": None}
            return {"annual": None, "quarterly": None}


def _clean_number(value: Any) -> Optional[float]:
    """Convert value to float, handling None and string numbers."""
    if value is None or (isinstance(value, str) and value.lower() == "null"):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
