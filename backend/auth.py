"""Request auth helpers."""

from __future__ import annotations

import secrets

from flask import Request, jsonify

from config import get_settings

_PLACEHOLDERS = {"", "change-me-to-a-long-random-string", "your_api_key_here"}


def require_api_key(req: Request):
    expected = get_settings().extract_api_key
    if expected in _PLACEHOLDERS:
        return jsonify({"error": "Server misconfigured: set EXTRACT_API_KEY"}), 503

    provided = req.headers.get("X-API-Key", "")
    if (
        not provided
        or len(provided) != len(expected)
        or not secrets.compare_digest(provided, expected)
    ):
        return jsonify({"error": "Unauthorized"}), 401
    return None
