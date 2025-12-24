import os
import json
import re
from typing import Optional, Any, Dict, Union
from perplexity import Perplexity
from dotenv import load_dotenv

load_dotenv()


def extract_feature(filing_text: str, feature_name: str, form_type: str) -> Dict[str, Any]:
    """
    Auto-detect and extract either numeric or qualitative features.
    
    Returns:
        Numeric: {"type": "numeric", "annual": X, "quarterly": Y}
        Qualitative: {"type": "score", "score": X, "evidence": "..."}
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
    
    client = Perplexity(api_key=api_key)
    
    # Step 1: Detect if feature is numeric or qualitative
    feature_type = _detect_feature_type(client, feature_name)
    
    # Step 2: Extract based on type
    if feature_type == "numeric":
        return _extract_numeric(client, filing_text, feature_name, form_type)
    else:
        return _extract_qualitative(client, filing_text, feature_name, form_type)


def _detect_feature_type(client: Perplexity, feature_name: str) -> str:
    """Detect if feature is numeric or qualitative."""
    prompt = f"""Is "{feature_name}" a numeric financial metric or a qualitative assessment?

Examples of NUMERIC: revenue, book value, total assets, cash flow, R&D spending, number of employees
Examples of QUALITATIVE: AI exposure, crypto involvement, ESG commitment, recession risk, innovation focus

Answer with ONLY one word: "numeric" or "qualitative"

Feature: {feature_name}
Answer:"""
    
    try:
        response = client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are a classification assistant. Answer with one word only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        result = result.strip().lower()
        
        return "numeric" if "numeric" in result else "qualitative"
    except Exception:
        return "numeric"  # Default to numeric on error


def _extract_numeric(client: Perplexity, filing_text: str, feature_name: str, form_type: str) -> Dict[str, Any]:
    """Extract numeric feature."""
    if form_type == "10-Q":
        prompt = _build_10q_numeric_prompt(feature_name, filing_text)
    elif form_type == "10-K":
        prompt = _build_10k_numeric_prompt(feature_name, filing_text)
    else:
        return {"type": "numeric"}
    
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
        
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        values = _parse_numeric_response(result.strip(), form_type)
        
        return {"type": "numeric", **values}
    except Exception as e:
        print(f"Error extracting numeric: {e}")
        return {"type": "numeric", "quarterly": None} if form_type == "10-Q" else {"type": "numeric", "annual": None, "quarterly": None}


def _extract_qualitative(client: Perplexity, filing_text: str, feature_name: str, form_type: str) -> Dict[str, Any]:
    """Extract qualitative score with evidence."""
    prompt = f"""Assess the company's exposure to "{feature_name}" in this SEC filing.

Return ONLY valid JSON in this exact format:
{{"score": <integer 1-10>, "evidence": "<brief supporting facts>"}}

Scoring guide:
1-2: Not mentioned or negligible
3-4: Minor mentions
5-6: Moderate focus
7-8: Significant strategic focus
9-10: Core to business model

Keep evidence under 100 words, focus on facts and numbers.

Filing text:
{filing_text[:30000]}

JSON:"""
    
    result = ""  # Initialize result to avoid "possibly unbound" error
    try:
        response = client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are a financial analysis assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=200
        )
        
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        result = result.strip()
        
        # Extract JSON if wrapped in markdown code blocks
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        
        data = json.loads(result)
        return {
            "type": "score",
            "score": int(data.get("score", 5)),
            "evidence": data.get("evidence", "No evidence provided")[:200]
        }
    except Exception as e:
        print(f"Error extracting qualitative: {e}")
        print(f"Raw response: {result}")
        return {"type": "score", "score": None, "evidence": "Extraction failed"}


def _build_10q_numeric_prompt(feature: str, text: str) -> str:
    """Build numeric extraction prompt for 10-Q."""
    return f"""Extract "{feature}" from this 10-Q quarterly filing.

Return ONLY valid JSON: {{"quarterly": <numeric_value>}}

Rules:
- Extract the quarterly value for the period covered
- Convert thousands/millions/billions to actual numbers
- If not found, use null
- Return ONLY the JSON

Filing text:
{text[:30000]}

JSON:"""


def _build_10k_numeric_prompt(feature: str, text: str) -> str:
    """Build numeric extraction prompt for 10-K."""
    return f"""Extract "{feature}" from this 10-K annual filing.

Return ONLY valid JSON: {{"annual": <full_year_value>, "quarterly": <Q4_value_or_null>}}

Rules:
- "annual": Full fiscal year total/value
- "quarterly": Q4 value if stated, else null
- For balance sheet items, both may be same
- Convert thousands/millions/billions to actual numbers
- Return ONLY the JSON

Filing text:
{text[:30000]}

JSON:"""


def _parse_numeric_response(response: str, form_type: str) -> Dict[str, Optional[float]]:
    """Parse numeric JSON response."""
    try:
        data = json.loads(response)
        if form_type == "10-Q":
            return {"quarterly": _clean_number(data.get("quarterly"))}
        else:
            return {
                "annual": _clean_number(data.get("annual")),
                "quarterly": _clean_number(data.get("quarterly"))
            }
    except json.JSONDecodeError:
        numbers = re.findall(r'[-+]?\d+\.?\d*(?:e[-+]?\d+)?', response.replace(",", ""))
        if form_type == "10-Q":
            return {"quarterly": float(numbers[0]) if numbers else None}
        else:
            if len(numbers) >= 2:
                return {"annual": float(numbers[0]), "quarterly": float(numbers[1])}
            elif len(numbers) == 1:
                return {"annual": float(numbers[0]), "quarterly": None}
            return {"annual": None, "quarterly": None}


def _clean_number(value: Any) -> Optional[float]:
    """Convert value to float."""
    if value is None or (isinstance(value, str) and value.lower() == "null"):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
