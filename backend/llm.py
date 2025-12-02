import os
from typing import Optional, Any
from perplexity import Perplexity
from dotenv import load_dotenv

load_dotenv()

def extract_numeric_feature(filing_text: str, feature_name: str) -> Optional[float]:
    """
    Use Perplexity API to extract a numeric feature from SEC filing text.
    
    Args:
        filing_text: Cleaned filing text
        feature_name: User-specified feature (e.g., "book value", "number of employees")
    
    Returns:
        Extracted numeric value or None if extraction fails
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
    
    client = Perplexity(api_key=api_key)
    
    prompt = f"""Extract the "{feature_name}" from this SEC filing.
Return ONLY a single numeric value with no units, explanations, or additional text.
If the value is in thousands/millions/billions, convert to the actual number.
If the value cannot be found or extracted, return "null".

Filing text:
{filing_text}

Numeric value:"""
    
    try:
        response = client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are a precise financial data extraction assistant. Return only numeric values."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        # Handle structured content response
        content: Any = response.choices[0].message.content
        result = "".join(getattr(item, 'text', str(item)) for item in content) if isinstance(content, list) else str(content)
        result = result.strip()
        
        if result.lower() == "null" or not result:
            return None
        
        # Remove formatting and convert to float
        result = result.replace(",", "").replace("$", "").strip()
        return float(result)
    
    except Exception as e:
        print(f"Error extracting feature: {e}")
        return None


if __name__ == "__main__":
    test_text = """
    Apple Inc. Financial Summary
    Total Assets: $352,755,000,000
    Total Liabilities: $290,437,000,000
    Book Value (Stockholders' Equity): $62,146,000,000
    164,000 people work at the company worldwide.
    """
    
    value = extract_numeric_feature(test_text, "book value")
    print(f"Extracted book value: {value}")
    
    employees = extract_numeric_feature(test_text, "number of employees")
    print(f"Extracted employees: {employees}")