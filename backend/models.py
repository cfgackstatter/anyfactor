"""Shared domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class FeatureKind(str, Enum):
    NUMERIC = "numeric"
    QUALITATIVE = "qualitative"


class ValueType(str, Enum):
    NUMERIC = "numeric"
    SCORE = "score"


@dataclass(frozen=True)
class Filing:
    url: str
    form_type: str
    filing_date: str


@dataclass
class ExtractResult:
    ticker: str
    feature: str
    value: Any = None
    value_type: str = ValueType.NUMERIC.value
    period_type: str | None = None
    filing_url: str | None = None
    filing_date: str | None = None
    form_type: str | None = None
    evidence: str | None = None
    unit: str | None = None
    period_end: str | None = None
    label_matched: str | None = None
    quote: str | None = None
    confidence: float | None = None
    source: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {
            key: value
            for key, value in data.items()
            if key == "value" or value is not None
        }


@dataclass
class NumericExtraction:
    value: float | None = None
    period_type: str | None = None
    unit: str | None = None
    scale: float | None = 1.0
    period_end: str | None = None
    statement: str | None = None
    label_matched: str | None = None
    quote: str | None = None
    confidence: float | None = None
    source: str = "llm"

    @property
    def kind(self) -> str:
        return "numeric"

    # Back-compat aliases used by older helpers
    @property
    def annual(self) -> float | None:
        return self.value if self.period_type == "annual" else None

    @property
    def quarterly(self) -> float | None:
        return self.value if self.period_type == "quarterly" else None


@dataclass
class ScoreExtraction:
    score: int | None = None
    evidence: str = "Not found"
    quote: str | None = None
    confidence: float | None = None
    source: str = "llm"

    @property
    def kind(self) -> str:
        return "score"


@dataclass
class ExtractRequest:
    tickers: list[str]
    feature: str
    limit: int = 5
