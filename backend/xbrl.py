"""SEC XBRL companyfacts lookup for standard numeric metrics."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

from config import get_settings
from http_client import get_session
from metrics import TagCandidate, resolve_xbrl_tags

logger = logging.getLogger(__name__)

_facts_cache: dict[str, tuple[float, dict[str, Any]]] = {}


@dataclass(frozen=True)
class XbrlFact:
    value: float
    unit: str
    period_end: str | None
    filed: str | None
    form: str | None
    fy: int | None
    fp: str | None
    frame: str | None
    taxonomy: str
    tag: str
    label: str | None


def get_companyfacts(cik: str) -> dict[str, Any] | None:
    settings = get_settings()
    now = time.monotonic()
    cached = _facts_cache.get(cik)
    if cached and (now - cached[0]) < settings.sec_ticker_cache_ttl:
        return cached[1]

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    try:
        resp = get_session().get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        _facts_cache[cik] = (now, data)
        return data
    except requests.RequestException as exc:
        logger.error("companyfacts fetch failed for %s: %s", cik, exc)
        return None


def lookup_xbrl_value(
    *,
    cik: str,
    feature: str,
    form_type: str,
    filing_date: str,
) -> XbrlFact | None:
    tags = resolve_xbrl_tags(feature)
    if not tags:
        return None
    facts = get_companyfacts(cik)
    if not facts:
        return None
    return match_fact(facts, tags, form_type=form_type, filing_date=filing_date)


def match_fact(
    companyfacts: dict[str, Any],
    tags: list[TagCandidate],
    *,
    form_type: str,
    filing_date: str,
) -> XbrlFact | None:
    facts_root = companyfacts.get("facts", {})
    for candidate in tags:
        taxonomy = facts_root.get(candidate.taxonomy, {})
        concept = taxonomy.get(candidate.tag)
        if not concept:
            continue
        label = concept.get("label")
        units = concept.get("units") or {}
        # Prefer USD / shares / pure number units in that order.
        unit_keys = sorted(
            units.keys(),
            key=lambda u: (
                0 if u.upper() == "USD" else
                1 if "share" in u.lower() else
                2 if u.lower() in {"pure", "number"} else
                3
            ),
        )
        best: tuple[float, dict[str, Any], str] | None = None
        for unit in unit_keys:
            for point in units.get(unit, []):
                score = _score_point(point, form_type=form_type, filing_date=filing_date)
                if score < 0:
                    continue
                if best is None or score > best[0]:
                    best = (score, point, unit)
        if best is None:
            continue
        _, point, unit = best
        try:
            value = float(point["val"])
        except (KeyError, TypeError, ValueError):
            continue
        return XbrlFact(
            value=value,
            unit=unit,
            period_end=point.get("end"),
            filed=point.get("filed"),
            form=point.get("form"),
            fy=point.get("fy"),
            fp=point.get("fp"),
            frame=point.get("frame"),
            taxonomy=candidate.taxonomy,
            tag=candidate.tag,
            label=label,
        )
    return None


def _score_point(point: dict[str, Any], *, form_type: str, filing_date: str) -> float:
    form = (point.get("form") or "").upper()
    if not form.startswith(form_type.upper()):
        return -1.0

    filed = point.get("filed") or ""
    delta = _date_diff_days(filed, filing_date)
    if delta is None or delta > 40:
        return -1.0

    score = 50.0 - delta  # exact filing date preferred

    end = point.get("end") or ""
    end_ord = _date_ordinal(end)
    if end_ord is None:
        return -1.0
    # Prefer the most recent period end reported in this filing.
    score += end_ord / 1000.0

    fp = (point.get("fp") or "").upper()
    frame = point.get("frame") or ""
    duration = _duration_days(point)

    if form_type == "10-K":
        if fp == "FY":
            score += 20
        # Avoid quarterly comparative frames inside annual filings.
        if "Q" in frame and not frame.endswith("I"):
            score -= 40
        if duration is not None and duration >= 300:
            score += 25
        elif duration is None and frame.endswith("I"):
            # Balance-sheet instantaneous annual
            score += 15
        if not frame:
            score += 8
    else:  # 10-Q — prefer single-quarter duration facts
        if fp.startswith("Q"):
            score += 10
        if frame.endswith("I"):
            # Balance sheet point-in-time for the quarter
            score += 18
        elif frame and "Q" in frame:
            score += 22
        if duration is not None:
            if 60 <= duration <= 120:
                score += 30  # ~one quarter
            elif duration > 150:
                score -= 25  # YTD / multi-quarter rollup
        elif not frame:
            # YTD income statement often has frame=None and long duration missing start handling
            score -= 5

    return score


def _duration_days(point: dict[str, Any]) -> int | None:
    start = point.get("start")
    end = point.get("end")
    if not start or not end:
        return None
    return _date_diff_days(start, end)


def _date_ordinal(value: str) -> int | None:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").toordinal()
    except ValueError:
        return None


def _date_diff_days(a: str, b: str) -> int | None:
    try:
        da = datetime.strptime(a[:10], "%Y-%m-%d")
        db = datetime.strptime(b[:10], "%Y-%m-%d")
        return abs((da - db).days)
    except ValueError:
        return None
