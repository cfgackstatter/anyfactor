import os
import json
import re
from typing import Optional, Dict, Any, Callable
from perplexity import Perplexity
from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE = 40000

def extract_feature(filing_text: str, feature_name: str, form_type: str) -> Dict[str, Any]:
    """Auto-detect and extract either numeric or qualitative features."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY not found")
    
    client = Perplexity(api_key=api_key)
    feature_type = _classify_feature(client, feature_name)
    
    if feature_type == "numeric":
        return _extract_iteratively(client, filing_text, feature_name, form_type, 
                                    _build_numeric_prompt, _parse_numeric)
    else:
        return _extract_iteratively(client, filing_text, feature_name, form_type,
                                    _build_qualitative_prompt, _parse_qualitative)


def _classify_feature(client: Perplexity, feature_name: str) -> str:
    """Fast classification: numeric vs qualitative."""
    prompt = f"""Is "{feature_name}" numeric or qualitative?
Numeric: revenue, assets, employees, spending
Qualitative: AI exposure, ESG, innovation
Answer:"""
    
    try:
        response = client.chat.completions.create(
            model="sonar",
            messages=[{"role": "system", "content": "One word only."}, 
                     {"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=5, top_p=0.1
        )
        result = _extract_text(response.choices[0].message.content).lower()
        return "numeric" if "numeric" in result else "qualitative"
    except Exception:
        return "numeric"


def _extract_iteratively(client: Perplexity, filing_text: str, feature_name: str, 
                         form_type: str, prompt_builder: Callable, parser: Callable) -> Dict[str, Any]:
    """Search filing in chunks until data found."""
    chunks = [filing_text[i:i+CHUNK_SIZE] for i in range(0, len(filing_text), CHUNK_SIZE)]
    priority = _get_chunk_priority(len(chunks))
    
    print(f"Searching {len(chunks)} chunks for '{feature_name}'")
    
    for idx in priority:
        if idx >= len(chunks):
            continue
        
        print(f"  Chunk {idx+1}...")
        result = _extract_from_chunk(client, chunks[idx], feature_name, form_type, 
                                     prompt_builder, parser)
        
        if _has_data(result):
            print(f"  ✓ Found in chunk {idx+1}")
            return result
    
    print(f"  ✗ Not found")
    return _empty_result(form_type, parser)


def _extract_from_chunk(client: Perplexity, chunk: str, feature_name: str, 
                        form_type: str, prompt_builder: Callable, parser: Callable) -> Dict[str, Any]:
    """Extract from single chunk."""
    try:
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "system", "content": "Return only valid JSON."},
                     {"role": "user", "content": prompt_builder(feature_name, chunk, form_type)}],
            temperature=0.0, max_tokens=200, top_p=1.0
        )
        return parser(_extract_text(response.choices[0].message.content), form_type)
    except Exception as e:
        print(f"    Error: {e}")
        return _empty_result(form_type, parser)


def _build_numeric_prompt(feature: str, text: str, form_type: str) -> str:
    """Build numeric extraction prompt."""
    if form_type == "10-Q":
        return f"""Extract "{feature}" from this 10-Q section.
Return JSON: {{"quarterly": <number>}}
Convert M/B to actual numbers. Use null if not found.
Text: {text}
JSON:"""
    else:
        return f"""Extract "{feature}" from this 10-K section.
Return JSON: {{"annual": <number>, "quarterly": <number>}}
annual = full year, quarterly = Q4 (or null). Convert M/B.
Text: {text}
JSON:"""


def _build_qualitative_prompt(feature: str, text: str, form_type: str) -> str:
    """Build qualitative extraction prompt."""
    return f"""Assess "{feature}" in this filing section.
Return JSON: {{"score": <1-10>, "evidence": "<brief facts>"}}
Score: 1-2=none, 3-4=minor, 5-6=moderate, 7-8=significant, 9-10=core
Text: {text}
JSON:"""


def _parse_numeric(response: str, form_type: str) -> Dict[str, Any]:
    """Parse numeric JSON response."""
    data = _parse_json(response)
    if form_type == "10-Q":
        return {"type": "numeric", "quarterly": _to_float(data.get("quarterly"))}
    else:
        return {"type": "numeric", 
                "annual": _to_float(data.get("annual")), 
                "quarterly": _to_float(data.get("quarterly"))}


def _parse_qualitative(response: str, form_type: str) -> Dict[str, Any]:
    """Parse qualitative JSON response."""
    data = _parse_json(response)
    return {"type": "score",
            "score": int(data.get("score", 5)),
            "evidence": str(data.get("evidence", "No evidence"))[:200]}


def _parse_json(response: str) -> Dict:
    """Extract and parse JSON from response."""
    text = response.strip()
    if text.startswith("```"):
        text = text.split("```")[1].lstrip("json").strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _get_chunk_priority(num_chunks: int) -> list:
    """Smart chunk ordering: financial data typically in middle chunks."""
    if num_chunks > 4:
        return [2, 3, 4, 1] + list(range(5, num_chunks)) + [0]
    elif num_chunks > 1:
        return list(range(1, num_chunks)) + [0]
    return [0]


def _has_data(result: Dict) -> bool:
    """Check if result contains data."""
    if result.get("type") == "numeric":
        return result.get("annual") is not None or result.get("quarterly") is not None
    elif result.get("type") == "score":
        return result.get("score") is not None
    return False


def _empty_result(form_type: str, parser: Callable) -> Dict[str, Any]:
    """Return empty result based on type."""
    if parser == _parse_numeric:
        return {"type": "numeric", "quarterly": None} if form_type == "10-Q" else \
               {"type": "numeric", "annual": None, "quarterly": None}
    else:
        return {"type": "score", "score": None, "evidence": "Not found"}


def _extract_text(content: Any) -> str:
    """Extract text from Perplexity response content."""
    if isinstance(content, list):
        return "".join(getattr(item, 'text', str(item)) for item in content)
    return str(content)


def _to_float(value: Any) -> Optional[float]:
    """Convert value to float."""
    if value is None or (isinstance(value, str) and value.lower() == "null"):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
