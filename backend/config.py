"""Central configuration loaded from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv()  # also allow process env / CWD override


def _csv(name: str, default: str) -> list[str]:
    return [part.strip() for part in os.getenv(name, default).split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    perplexity_api_key: str = field(default_factory=lambda: os.getenv("PERPLEXITY_API_KEY", "").strip())
    extract_api_key: str = field(default_factory=lambda: os.getenv("EXTRACT_API_KEY", "").strip())
    frontend_origins: list[str] = field(
        default_factory=lambda: _csv("FRONTEND_ORIGINS", "http://localhost:3000")
    )
    sec_user_agent: str = field(
        default_factory=lambda: os.getenv(
            "SEC_USER_AGENT",
            "AnyFactor research-tool (contact: set SEC_USER_AGENT in .env)",
        ).strip()
    )
    sec_ticker_cache_ttl: int = field(
        default_factory=lambda: int(os.getenv("SEC_TICKER_CACHE_TTL", "3600"))
    )
    flask_debug: bool = field(default_factory=lambda: os.getenv("FLASK_DEBUG", "0") == "1")
    flask_host: str = field(default_factory=lambda: os.getenv("FLASK_HOST", "127.0.0.1"))
    flask_port: int = field(default_factory=lambda: int(os.getenv("FLASK_PORT", "5000")))

    max_tickers: int = 10
    max_filings: int = 20
    max_feature_len: int = 200
    extract_rate_limit: str = "10 per hour"
    default_rate_limit: str = "120 per hour"

    # Parallelism for SEC fetch/parse and LLM calls
    fetch_workers: int = field(default_factory=lambda: int(os.getenv("FETCH_WORKERS", "4")))
    llm_workers: int = field(default_factory=lambda: int(os.getenv("LLM_WORKERS", "2")))

    # Retrieval
    retrieve_limit: int = field(default_factory=lambda: int(os.getenv("RETRIEVE_LIMIT", "5")))
    retrieve_max_chars: int = field(default_factory=lambda: int(os.getenv("RETRIEVE_MAX_CHARS", "14000")))

    # LLM provider: auto | perplexity | ollama
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "auto").strip().lower())
    perplexity_model: str = field(
        default_factory=lambda: os.getenv("PERPLEXITY_MODEL", "sonar-pro").strip()
    )
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "").strip())
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2").strip())

    chunk_size: int = 40_000
    max_chunks_to_search: int = 6


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
