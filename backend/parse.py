"""Section-aware filing parsing and passage building."""

from __future__ import annotations

import logging
import re
import warnings
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning

from http_client import get_session

logger = logging.getLogger(__name__)

SEC_PREFIX = "https://www.sec.gov/"
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

_ITEM_SPLIT = re.compile(
    r"(?is)(?=(?:^|\n)\s*item\s+\d{1,2}[a-z]?\b)"
)
_ITEM_HEADER = re.compile(
    r"(?is)^\s*item\s+(\d{1,2}[a-z]?)\s*[.\-:—]?\s*(.*)$"
)


@dataclass(frozen=True)
class Passage:
    section_id: str
    title: str
    text: str
    kind: str  # section | table | block


@dataclass(frozen=True)
class PreparedFiling:
    raw_text: str
    passages: list[Passage]


def fetch_filing(url: str) -> str | None:
    if not url.startswith(SEC_PREFIX):
        logger.warning("Refusing non-SEC URL: %s", url)
        return None
    try:
        resp = get_session().get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.error("Error fetching %s: %s", url, exc)
        return None


def _table_to_markdown(table: Tag) -> str:
    rows: list[str] = []
    for tr in table.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
        if cells:
            rows.append("| " + " | ".join(cells) + " |")
    if rows:
        num_cols = max(len(rows[0].split("|")) - 2, 1)
        rows.insert(1, "| " + " | ".join(["---"] * num_cols) + " |")
    return "\n".join(rows)


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    for table in soup.find_all("table"):
        table.replace_with(f"\n{_table_to_markdown(table)}\n")

    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    # Drop obvious TOC-only noise lines that are just dotted leaders
    cleaned = [ln for ln in lines if not re.fullmatch(r"[.\s]+", ln)]
    return "\n".join(cleaned)


def split_sections(text: str) -> list[Passage]:
    parts = _ITEM_SPLIT.split(text)
    passages: list[Passage] = []
    if len(parts) <= 1:
        return passages

    for part in parts:
        part = part.strip()
        if not part:
            continue
        first_line, _, rest = part.partition("\n")
        match = _ITEM_HEADER.match(first_line.strip())
        if not match:
            continue
        item_id = match.group(1).upper()
        title = (match.group(2) or "").strip() or f"Item {item_id}"
        body = rest.strip()
        if len(body) < 80:
            continue
        passages.append(
            Passage(section_id=f"Item {item_id}", title=title, text=body[:60_000], kind="section")
        )
    return passages


def _block_passages(text: str, max_chars: int = 3500) -> list[Passage]:
    """Fallback sliding windows when Item headers are missing."""
    passages: list[Passage] = []
    step = max_chars - 400
    for i, start in enumerate(range(0, len(text), step)):
        chunk = text[start : start + max_chars].strip()
        if len(chunk) < 120:
            continue
        passages.append(
            Passage(section_id=f"block-{i}", title="Filing excerpt", text=chunk, kind="block")
        )
        if i >= 40:
            break
    return passages


def _table_passages(text: str) -> list[Passage]:
    passages: list[Passage] = []
    # Markdown tables separated by blank lines
    chunks = re.split(r"\n{2,}", text)
    for i, chunk in enumerate(chunks):
        if "|" not in chunk or chunk.count("|") < 6:
            continue
        if len(chunk) < 80:
            continue
        passages.append(
            Passage(
                section_id=f"table-{i}",
                title="Financial table",
                text=chunk[:8_000],
                kind="table",
            )
        )
        if len(passages) >= 80:
            break
    return passages


def prepare_filing(html: str) -> PreparedFiling:
    raw = clean_html(html)
    sections = split_sections(raw)
    tables = _table_passages(raw)
    passages = [*sections, *tables]
    if not passages:
        passages = _block_passages(raw)
    return PreparedFiling(raw_text=raw, passages=passages)


def fetch_and_prepare(url: str) -> PreparedFiling | None:
    html = fetch_filing(url)
    if not html:
        return None
    return prepare_filing(html)


# Back-compat helpers used by older call sites / tests
def prepare_for_llm(html: str) -> str:
    return clean_html(html)
