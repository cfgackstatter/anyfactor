"""Shared HTTP session for SEC requests (connection pooling)."""

from __future__ import annotations

import threading

import requests

from config import get_settings

_lock = threading.Lock()
_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is not None:
        return _session
    with _lock:
        if _session is None:
            session = requests.Session()
            session.headers.update({"User-Agent": get_settings().sec_user_agent})
            _session = session
    return _session
