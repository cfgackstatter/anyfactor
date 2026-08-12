"""Keyword / section-aware passage retrieval for closed-document extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass

from metrics import feature_synonyms
from models import FeatureKind
from parse import Passage

# Preferred sections by feature kind / topic.
_NUMERIC_SECTION_BOOST = {
    "8": 8.0,   # Financial Statements
    "7": 5.0,   # MD&A
    "1": 1.5,
}
_QUAL_SECTION_BOOST = {
    "1": 6.0,
    "1A": 7.0,
    "7": 5.0,
    "7A": 3.0,
    "8": 1.0,
}


@dataclass(frozen=True)
class RankedPassage:
    passage: Passage
    score: float


def retrieve_passages(
    passages: list[Passage],
    feature: str,
    feature_kind: FeatureKind,
    *,
    limit: int = 5,
    max_chars: int = 14_000,
) -> list[Passage]:
    if not passages:
        return []

    terms = [t.lower() for t in feature_synonyms(feature)]
    term_res = [re.compile(rf"\b{re.escape(t)}\b", re.I) for t in terms if len(t) >= 2]

    ranked: list[RankedPassage] = []
    for passage in passages:
        score = _score(passage, term_res, feature_kind)
        if score > 0:
            ranked.append(RankedPassage(passage=passage, score=score))

    ranked.sort(key=lambda r: r.score, reverse=True)

    selected: list[Passage] = []
    used = 0
    for item in ranked:
        text_len = len(item.passage.text)
        if selected and used + text_len > max_chars:
            continue
        selected.append(item.passage)
        used += text_len
        if len(selected) >= limit:
            break

    if feature_kind is FeatureKind.NUMERIC and not any(p.kind == "table" for p in selected):
        for item in ranked:
            if item.passage.kind == "table":
                selected.append(item.passage)
                break

    if selected:
        return selected

    # Fallback when keywords miss: prefer financial sections/tables.
    if feature_kind is FeatureKind.NUMERIC:
        preferred = [
            p for p in passages
            if p.kind == "table" or p.section_id.replace("Item ", "").upper() in {"7", "8"}
        ]
    else:
        preferred = [
            p for p in passages
            if p.section_id.replace("Item ", "").upper() in {"1", "1A", "7", "7A"}
        ]
    return (preferred or passages)[:limit]


def format_context(passages: list[Passage]) -> str:
    blocks: list[str] = []
    for i, p in enumerate(passages, 1):
        header = f"[Excerpt {i} | {p.section_id} | {p.title} | {p.kind}]"
        blocks.append(f"{header}\n{p.text}")
    return "\n\n----\n\n".join(blocks)


def _score(passage: Passage, term_res: list[re.Pattern[str]], kind: FeatureKind) -> float:
    text = passage.text
    lowered = text.lower()
    score = 0.0

    for cre in term_res:
        hits = cre.findall(text)
        if hits:
            score += min(12.0, 3.0 * len(hits))

    # Light token presence for multi-word features
    if not score:
        return 0.0

    item_key = passage.section_id.replace("Item ", "").upper()
    boosts = _QUAL_SECTION_BOOST if kind is FeatureKind.QUALITATIVE else _NUMERIC_SECTION_BOOST
    score += boosts.get(item_key, 0.0)

    if passage.kind == "table" and kind is FeatureKind.NUMERIC:
        score += 4.0
    if passage.kind == "section" and kind is FeatureKind.QUALITATIVE:
        score += 2.0

    # Mild preference for denser matches
    score += min(3.0, lowered.count("$") * 0.05)
    return score
