import os
import json
import re
from typing import Optional, Any, Dict
from perplexity import Perplexity
from dotenv import load_dotenv

load_dotenv()

# Chunk size for iterative search
CHUNK_SIZE = 40000

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
    
    # Step 1: Fast classification with optimized parameters
    feature_type = _detect_feature_type(client, feature_name)
    
    # Step 2: Extract based on type
    if feature_type == "numeric":
        return _extract_numeric_iterative(client, filing_text, feature_name, form_type)
    else:
        return _extract_qualitative(client, filing_text, feature_name, form_type)


def _detect_feature_type(client: Perplexity, feature_name: str) -> str:
    """Fast classification: numeric vs qualitative."""
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
                {"role": "system", "content": "Answer with one word only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5,      # ⭐ Optimized: just need 1 word
            top_p=0.1          # ⭐ Optimized: focus on most likely answer
        )
        
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        result = result.strip().lower()
        
        return "numeric" if "numeric" in result else "qualitative"
    except Exception as e:
        print(f"Classification error: {e}")
        return "numeric"  # Default to numeric


def _extract_numeric_iterative(client: Perplexity, filing_text: str, feature_name: str, form_type: str) -> Dict[str, Any]:
    """Extract numeric feature by searching chunks iteratively until found."""
    # Create chunks
    chunks = [filing_text[i:i+CHUNK_SIZE] for i in range(0, len(filing_text), CHUNK_SIZE)]
    
    # Smart chunk ordering: financial statements typically appear mid-to-late filing
    # Skip chunk 0 (usually cover page), prioritize chunks 2-4 (where Item 6/8 typically are)
    num_chunks = len(chunks)
    if num_chunks > 4:
        priority_order = [2, 3, 4, 1, 5, 6, 7, 8, 9] + list(range(10, num_chunks))
    elif num_chunks > 1:
        priority_order = list(range(1, num_chunks)) + [0]
    else:
        priority_order = [0]
    
    print(f"Searching {num_chunks} chunks for '{feature_name}' (40k chars each)")
    
    for chunk_idx in priority_order:
        if chunk_idx >= num_chunks:
            continue
        
        print(f"  Chunk {chunk_idx + 1}/{num_chunks}...")
        result = _extract_numeric_from_chunk(client, chunks[chunk_idx], feature_name, form_type)
        
        # Stop if we found data
        if form_type == "10-Q":
            if result.get("quarterly") is not None:
                print(f"  ✓ Found in chunk {chunk_idx + 1}")
                return {"type": "numeric", **result}
        else:  # 10-K
            if result.get("annual") is not None or result.get("quarterly") is not None:
                print(f"  ✓ Found in chunk {chunk_idx + 1}")
                return {"type": "numeric", **result}
    
    # Not found in any chunk
    print(f"  ✗ Not found in any chunk")
    if form_type == "10-Q":
        return {"type": "numeric", "quarterly": None}
    else:
        return {"type": "numeric", "annual": None, "quarterly": None}


def _extract_numeric_from_chunk(client: Perplexity, chunk_text: str, feature_name: str, form_type: str) -> Dict[str, Optional[float]]:
    """Extract numeric feature from a single chunk."""
    if form_type == "10-Q":
        prompt = _build_10q_numeric_prompt(feature_name, chunk_text)
    elif form_type == "10-K":
        prompt = _build_10k_numeric_prompt(feature_name, chunk_text)
    else:
        return {}
    
    try:
        response = client.chat.completions.create(
            model="sonar-pro",      # ⭐ Better accuracy for financial data
            messages=[
                {"role": "system", "content": "You are a precise financial data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50,          # Just need JSON with 1-2 numbers
            top_p=1.0               # Default for flexibility with rare formats
        )
        
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        return _parse_numeric_response(result.strip(), form_type)
    except Exception as e:
        print(f"    Error: {e}")
        return {"quarterly": None} if form_type == "10-Q" else {"annual": None, "quarterly": None}


def _extract_qualitative(client: Perplexity, filing_text: str, feature_name: str, form_type: str) -> Dict[str, Any]:
    """Extract qualitative score with evidence from beginning of filing."""
    # For qualitative: business narrative is early in filing (Item 1)
    # Use first 80k chars (covers Item 1 and Item 1A typically)
    text_chunk = filing_text[:80000]
    
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
{text_chunk}

JSON:"""
    
    result = ""
    try:
        response = client.chat.completions.create(
            model="sonar-pro",      # ⭐ Better reasoning for qualitative assessment
            messages=[
                {"role": "system", "content": "You are a financial analysis assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=200,         # Score + detailed evidence
            top_p=1.0               # Need creativity for evidence synthesis
        )
        
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        result = result.strip()
        
        # Extract JSON if wrapped in markdown
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
    return f"""Extract "{feature}" from this 10-Q quarterly filing section.

Return ONLY valid JSON: {{"quarterly": <number>}}

Rules:
- Extract the quarterly value for the period covered
- Convert thousands/millions/billions to actual numbers (e.g., "$5.2M" → 5200000)
- If not found in this section, use null
- Return ONLY the JSON, no explanation

Filing section:
{text}

JSON:"""


def _build_10k_numeric_prompt(feature: str, text: str) -> str:
    """Build numeric extraction prompt for 10-K."""
    return f"""Extract "{feature}" from this 10-K annual filing section.

Return ONLY valid JSON: {{"annual": <number>, "quarterly": <number>}}

Rules:
- "annual": Full fiscal year total/value
- "quarterly": Q4 value if separately stated, else null
- For balance sheet items (assets, liabilities), both may be the same
- Convert thousands/millions/billions to actual numbers
- If not found in this section, use null
- Return ONLY the JSON, no explanation

Filing section:
{text}

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
        # Fallback: extract numbers from text
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
