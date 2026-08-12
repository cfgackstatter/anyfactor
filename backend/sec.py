"""SEC EDGAR helpers."""

from __future__ import annotations

import logging
import time
from typing import Iterable

import requests

from config import get_settings
from http_client import get_session
from models import Filing

logger = logging.getLogger(__name__)

_ticker_cache: dict[str, object] = {"map": None, "fetched_at": 0.0}


def _load_ticker_map() -> dict[str, str]:
    settings = get_settings()
    now = time.monotonic()
    cached = _ticker_cache.get("map")
    fetched_at = float(_ticker_cache.get("fetched_at") or 0)
    if isinstance(cached, dict) and (now - fetched_at) < settings.sec_ticker_cache_ttl:
        return cached

    resp = get_session().get(
        "https://www.sec.gov/files/company_tickers.json",
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    ticker_map = {
        item["ticker"].upper(): str(item["cik_str"]).zfill(10)
        for item in data.values()
        if item.get("ticker") is not None and item.get("cik_str") is not None
    }
    _ticker_cache["map"] = ticker_map
    _ticker_cache["fetched_at"] = now
    return ticker_map


def warm_ticker_cache() -> None:
    """Best-effort preload of the ticker map."""
    try:
        _load_ticker_map()
        logger.info("SEC ticker cache warmed (%s tickers)", len(_ticker_cache["map"] or {}))
    except requests.RequestException as exc:
        logger.warning("Could not warm SEC ticker cache: %s", exc)


def ticker_to_cik(ticker: str) -> str | None:
    try:
        return _load_ticker_map().get(ticker.upper())
    except requests.RequestException as exc:
        logger.error("Error fetching ticker data: %s", exc)
        return None


def get_filing_urls(
    cik: str,
    forms: Iterable[str] = ("10-K", "10-Q"),
    limit: int = 10,
) -> list[Filing]:
    form_set = set(forms)
    try:
        resp = get_session().get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error("Error fetching filings for CIK %s: %s", cik, exc)
        return []

    recent = data.get("filings", {}).get("recent", {})
    rows = zip(
        recent.get("accessionNumber", []),
        recent.get("form", []),
        recent.get("primaryDocument", []),
        recent.get("filingDate", []),
        strict=False,
    )

    filings: list[Filing] = []
    for accession, form, primary_doc, filing_date in rows:
        if form not in form_set or not primary_doc:
            continue
        acc_no = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no}/{primary_doc}"
        filings.append(Filing(url=url, form_type=form, filing_date=filing_date))
        if len(filings) >= limit:
            break
    return filings
