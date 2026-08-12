"""Request payload validation."""

from __future__ import annotations

import re
from typing import Any

from flask import jsonify

from config import get_settings
from models import ExtractRequest

_TICKER_RE = re.compile(r"^[A-Z0-9.-]{1,10}$")


def parse_extract_request(data: Any) -> tuple[ExtractRequest | None, tuple | None]:
    settings = get_settings()

    if not isinstance(data, dict):
        return None, (jsonify({"error": "JSON body required"}), 400)

    feature = data.get("feature", "")
    if not isinstance(feature, str) or not feature.strip():
        return None, (jsonify({"error": "feature is required"}), 400)
    feature = feature.strip()
    if len(feature) > settings.max_feature_len:
        return None, (
            jsonify({"error": f"feature must be <= {settings.max_feature_len} characters"}),
            400,
        )

    tickers = data.get("tickers", [])
    if not isinstance(tickers, list) or not tickers:
        return None, (jsonify({"error": "tickers are required"}), 400)
    if len(tickers) > settings.max_tickers:
        return None, (
            jsonify({"error": f"at most {settings.max_tickers} tickers allowed"}),
            400,
        )

    normalized: list[str] = []
    for raw in tickers:
        if not isinstance(raw, str) or not raw.strip():
            return None, (jsonify({"error": "each ticker must be a non-empty string"}), 400)
        ticker = raw.strip().upper()
        if not _TICKER_RE.fullmatch(ticker):
            return None, (jsonify({"error": f"invalid ticker: {raw}"}), 400)
        if ticker not in normalized:
            normalized.append(ticker)

    try:
        limit = int(data.get("limit", 5))
    except (TypeError, ValueError):
        return None, (jsonify({"error": "limit must be an integer"}), 400)
    if not 1 <= limit <= settings.max_filings:
        return None, (
            jsonify({"error": f"limit must be between 1 and {settings.max_filings}"}),
            400,
        )

    return ExtractRequest(tickers=normalized, feature=feature, limit=limit), None
