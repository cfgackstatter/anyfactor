import requests
from bs4 import BeautifulSoup, Tag
from typing import Optional

HEADERS = {"User-Agent": "anyfactor-app contact@example.com"}

def fetch_filing(url: str) -> Optional[str]:
    """Fetch HTML content from filing URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    
def table_to_markdown(table: Tag) -> str:
    """Convert HTML table to markdown format."""
    rows = []
    for tr in table.find_all('tr'):
        cells = [cell.get_text(strip=True) for cell in tr.find_all(['td', 'th'])]
        if cells:
            rows.append('| ' + ' | '.join(cells) + ' |')
    
    # Add separator after header row
    if rows:
        num_cols = len(rows[0].split('|')) - 2
        rows.insert(1, '| ' + ' | '.join(['---'] * num_cols) + ' |')
    
    return '\n'.join(rows)
    
def clean_html(html: str) -> str:
    """Extract clean text from SEC filing with tables as markdown."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script, style, and header elements
    for tag in soup(['script', 'style', 'meta', 'link']):
        tag.decompose()
    
    # Convert tables to markdown
    for table in soup.find_all('table'):
        md_table = table_to_markdown(table)
        table.replace_with(f"\n{md_table}\n")
    
    # Extract text and clean whitespace
    text = soup.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    return '\n'.join(lines)

def prepare_for_llm(html: str, max_chars: int = 50000) -> str:
    """Prepare filing for LLM by cleaning and truncating if needed."""
    clean = clean_html(html)
    
    if len(clean) > max_chars:
        clean = clean[:max_chars] + "\n[TRUNCATED]"
    
    return clean


if __name__ == "__main__":
    test_html = """
    <html>
    <body>
        <h1>Financial Statement</h1>
        <p>Total Revenue: $100,000,000</p>
        <table class="financial">
            <tr><th>Item</th><th>Value</th></tr>
            <tr><td>Assets</td><td>$500M</td></tr>
            <tr><td>Liabilities</td><td>$300M</td></tr>
        </table>
    </body>
    </html>
    """
    
    cleaned = prepare_for_llm(test_html)
    print(cleaned)