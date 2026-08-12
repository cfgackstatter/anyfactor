"""Closed-document LLM classification and extraction (Perplexity and/or Ollama)."""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from typing import Any

import requests
from perplexity import Perplexity

from config import get_settings
from metrics import feature_synonyms, heuristic_feature_kind
from models import FeatureKind, NumericExtraction, ScoreExtraction
from parse import Passage, PreparedFiling
from retrieve import format_context, retrieve_passages

logger = logging.getLogger(__name__)

Extraction = NumericExtraction | ScoreExtraction

_SYSTEM_EXTRACT = (
    "You extract facts ONLY from the provided SEC filing excerpts. "
    "Do not use outside knowledge or the web. "
    "If the excerpts do not contain the answer, return null fields. "
    "Return valid JSON only."
)


@lru_cache(maxsize=1)
def _perplexity() -> Perplexity | None:
    key = get_settings().perplexity_api_key
    if not key:
        return None
    return Perplexity(api_key=key)


def classify_feature(feature_name: str) -> FeatureKind:
    hinted = heuristic_feature_kind(feature_name)
    if hinted == "qualitative":
        return FeatureKind.QUALITATIVE
    if hinted == "numeric":
        return FeatureKind.NUMERIC

    prompt = (
        'Classify this feature as NUMERIC or QUALITATIVE.\n'
        "NUMERIC = measurable quantity in filings/financials.\n"
        "QUALITATIVE = descriptive assessment without a specific number.\n"
        f'Feature: "{feature_name}"\n'
        "Answer with ONLY one word: NUMERIC or QUALITATIVE"
    )
    try:
        text = _chat(
            system="Answer with only one word: NUMERIC or QUALITATIVE",
            user=prompt,
            max_tokens=16,
        ).upper()
        if "QUALITATIVE" in text:
            return FeatureKind.QUALITATIVE
    except Exception as exc:
        logger.warning("Classification error, defaulting to numeric: %s", exc)
    return FeatureKind.NUMERIC


def extract_from_prepared(
    prepared: PreparedFiling,
    feature_name: str,
    form_type: str,
    feature_kind: FeatureKind,
) -> Extraction:
    passages = retrieve_passages(
        prepared.passages,
        feature_name,
        feature_kind,
        limit=get_settings().retrieve_limit,
        max_chars=get_settings().retrieve_max_chars,
    )
    context = format_context(passages)
    logger.info(
        "Retrieved %s passages (%s chars) for %r",
        len(passages),
        len(context),
        feature_name,
    )

    if feature_kind is FeatureKind.NUMERIC:
        return _extract_numeric(feature_name, form_type, context, passages)
    return _extract_qualitative(feature_name, context)


def _extract_numeric(
    feature: str,
    form_type: str,
    context: str,
    passages: list[Passage],
) -> NumericExtraction:
    period = "annual" if form_type == "10-K" else "quarterly"
    synonyms = ", ".join(feature_synonyms(feature)[:8])
    user = f"""Feature to extract: "{feature}"
Synonyms to consider: {synonyms}
Form: {form_type}
Period type wanted: {period}

Rules:
- Use ONLY the excerpts below.
- Use the MOST RECENT reporting period column; ignore prior-year comparatives.
- Convert M/B/K abbreviations to full numbers (scale applied into value).
- Prefer consolidated totals over segment breakouts unless asked for a segment.
- If not clearly present, return nulls.

Return JSON:
{{
  "value": <number|null>,
  "unit": <"USD"|"shares"|"count"|string|null>,
  "scale": <1|1000|1000000|...>,
  "period_end": <YYYY-MM-DD|null>,
  "statement": <string|null>,
  "label_matched": <string|null>,
  "quote": <short verbatim excerpt|null>,
  "confidence": <0-1>
}}

Excerpts:
{context}
"""
    try:
        data = _parse_json(_chat(system=_SYSTEM_EXTRACT, user=user, max_tokens=300))
    except Exception as exc:
        logger.error("Numeric LLM extract failed: %s", exc)
        return NumericExtraction(period_type=period, source="llm")

    value = _to_float(data.get("value"))
    scale = _to_float(data.get("scale")) or 1.0
    if value is not None and scale not in (0, 1, None):
        # If model returned unscaled display number with scale hint, apply it.
        # Heuristic: only apply when |value| looks like a short display figure.
        if abs(value) < 1_000_000 and scale >= 1000:
            value *= scale

    quote = _clean_str(data.get("quote"))
    conf = _to_float(data.get("confidence"))
    if value is not None and quote and not _quote_in_context(quote, context):
        # Quote not grounded → downgrade confidence; keep value but flag.
        conf = min(conf or 0.5, 0.4)

    if value is None:
        return NumericExtraction(period_type=period, source="llm", confidence=conf)

    return NumericExtraction(
        value=value,
        period_type=period,
        unit=_clean_str(data.get("unit")),
        scale=scale,
        period_end=_clean_str(data.get("period_end")),
        statement=_clean_str(data.get("statement")),
        label_matched=_clean_str(data.get("label_matched")),
        quote=quote,
        confidence=conf,
        source="llm",
    )


def _extract_qualitative(feature: str, context: str) -> ScoreExtraction:
    synonyms = ", ".join(feature_synonyms(feature)[:8])
    user = f"""Assess "{feature}" using ONLY the excerpts.
Related terms: {synonyms}

Return JSON:
{{
  "score": <1-10|null>,
  "evidence": <brief facts|null>,
  "quote": <short verbatim excerpt|null>,
  "confidence": <0-1>
}}
Score guide: 1-2=none, 3-4=minor, 5-6=moderate, 7-8=significant, 9-10=core.
If no relevant evidence, all fields null.

Excerpts:
{context}
"""
    try:
        data = _parse_json(_chat(system=_SYSTEM_EXTRACT, user=user, max_tokens=300))
    except Exception as exc:
        logger.error("Qualitative LLM extract failed: %s", exc)
        return ScoreExtraction()

    raw = data.get("score")
    if raw is None:
        return ScoreExtraction()
    try:
        score = int(raw)
    except (TypeError, ValueError):
        return ScoreExtraction()
    if not 1 <= score <= 10:
        return ScoreExtraction()

    evidence = _clean_str(data.get("evidence")) or ""
    quote = _clean_str(data.get("quote"))
    if not evidence and not quote:
        return ScoreExtraction()
    if quote and not _quote_in_context(quote, context):
        quote = None

    return ScoreExtraction(
        score=score,
        evidence=(evidence or quote or "Not found")[:400],
        quote=quote,
        confidence=_to_float(data.get("confidence")),
        source="llm",
    )


def _chat(*, system: str, user: str, max_tokens: int) -> str:
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "ollama" or (provider == "auto" and settings.ollama_base_url and not settings.perplexity_api_key):
        return _chat_ollama(system=system, user=user, max_tokens=max_tokens)

    if provider in {"perplexity", "auto"}:
        text = _chat_perplexity(system=system, user=user, max_tokens=max_tokens)
        if text is not None:
            return text

    if settings.ollama_base_url:
        return _chat_ollama(system=system, user=user, max_tokens=max_tokens)

    raise RuntimeError("No LLM provider available (set PERPLEXITY_API_KEY or OLLAMA_BASE_URL)")


def _chat_perplexity(*, system: str, user: str, max_tokens: int) -> str | None:
    client = _perplexity()
    if client is None:
        return None
    settings = get_settings()
    # sonar models may still browse; instructions forbid it. Prefer configured model.
    response = client.chat.completions.create(
        model=settings.perplexity_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
        max_tokens=max(16, max_tokens),
        top_p=1.0,
    )
    return _choice_text(response)


def _chat_ollama(*, system: str, user: str, max_tokens: int) -> str:
    settings = get_settings()
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "options": {"temperature": 0, "num_predict": max_tokens},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    resp = requests.post(url, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    return str((data.get("message") or {}).get("content") or "")


def _parse_json(response: str) -> dict[str, Any]:
    text = response.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _choice_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    choice = choices[0]
    message = choice.get("message") if isinstance(choice, dict) else getattr(choice, "message", None)
    if message is None:
        return ""
    content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
    if isinstance(content, list):
        return "".join(getattr(item, "text", str(item)) for item in content)
    return str(content or "")


def _to_float(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and value.lower() in {"null", "none", ""}):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none"}:
        return None
    return text[:500]


def _quote_in_context(quote: str, context: str) -> bool:
    q = re.sub(r"\s+", " ", quote).strip().lower()
    c = re.sub(r"\s+", " ", context).lower()
    if len(q) < 8:
        return q in c
    # Allow minor whitespace/punctuation drift: check a significant substring
    core = q[:80]
    return core in c
