"""Extraction orchestration: XBRL-first, then retrieve + closed-context LLM."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

from config import get_settings
from llm import classify_feature, extract_from_prepared
from metrics import resolve_xbrl_tags
from models import (
    ExtractRequest,
    ExtractResult,
    FeatureKind,
    Filing,
    NumericExtraction,
    ScoreExtraction,
)
from parse import PreparedFiling, fetch_and_prepare
from sec import get_filing_urls, ticker_to_cik
from xbrl import lookup_xbrl_value

logger = logging.getLogger(__name__)


def run_extraction(req: ExtractRequest) -> Iterator[dict]:
    settings = get_settings()
    try:
        kind = classify_feature(req.feature)
        logger.info("Feature %r classified as %s", req.feature, kind.value)
    except Exception as exc:
        logger.exception("Classification failed: %s", exc)
        yield {"type": "error", "error": "Failed to classify feature"}
        return

    xbrl_tags = resolve_xbrl_tags(req.feature) if kind is FeatureKind.NUMERIC else []
    results: list[dict] = []

    try:
        for ticker_idx, ticker in enumerate(req.tickers):
            cik = ticker_to_cik(ticker)
            if not cik:
                results.append(
                    ExtractResult(ticker=ticker, feature=req.feature, error="Ticker not found").to_dict()
                )
                continue

            filings = get_filing_urls(cik, limit=req.limit)
            if not filings:
                results.append(
                    ExtractResult(ticker=ticker, feature=req.feature, error="No filings found").to_dict()
                )
                continue

            # Progress for XBRL phase
            xbrl_hits: dict[str, ExtractResult] = {}
            need_llm: list[Filing] = []

            for filing_idx, filing in enumerate(filings):
                yield {
                    "type": "progress",
                    "ticker": ticker,
                    "current": filing_idx + 1,
                    "total": len(filings),
                    "ticker_current": ticker_idx + 1,
                    "ticker_total": len(req.tickers),
                    "stage": "xbrl" if xbrl_tags else "llm",
                }

                if xbrl_tags:
                    fact = lookup_xbrl_value(
                        cik=cik,
                        feature=req.feature,
                        form_type=filing.form_type,
                        filing_date=filing.filing_date,
                    )
                    if fact is not None:
                        period = "annual" if filing.form_type == "10-K" else "quarterly"
                        xbrl_hits[filing.url] = ExtractResult(
                            ticker=ticker,
                            feature=req.feature,
                            value=fact.value,
                            period_type=period,
                            filing_url=filing.url,
                            filing_date=filing.filing_date,
                            form_type=filing.form_type,
                            unit=fact.unit,
                            period_end=fact.period_end,
                            label_matched=fact.label or fact.tag,
                            quote=f"XBRL {fact.taxonomy}:{fact.tag}",
                            confidence=0.95,
                            source="xbrl",
                            evidence=f"{fact.taxonomy}:{fact.tag} ({fact.frame or fact.fp})",
                        )
                        continue
                need_llm.append(filing)

            prepared_map: dict[str, PreparedFiling | None] = {}
            if need_llm:
                prepared_map = _fetch_filings_parallel(need_llm, settings.fetch_workers)

            llm_results = _extract_filings_parallel(
                ticker=ticker,
                feature=req.feature,
                kind=kind,
                filings=need_llm,
                prepared=prepared_map,
                workers=settings.llm_workers,
            )

            # Preserve filing order
            llm_by_url = {r.filing_url: r for r in llm_results}
            for filing in filings:
                if filing.url in xbrl_hits:
                    results.append(xbrl_hits[filing.url].to_dict())
                elif filing.url in llm_by_url:
                    results.append(llm_by_url[filing.url].to_dict())

        yield {"type": "complete", "results": results}
    except Exception as exc:
        logger.exception("Extraction failed: %s", exc)
        yield {"type": "error", "error": "Extraction failed"}


def _fetch_filings_parallel(
    filings: list[Filing], workers: int
) -> dict[str, PreparedFiling | None]:
    prepared: dict[str, PreparedFiling | None] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(fetch_and_prepare, f.url): f.url for f in filings}
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                prepared[url] = fut.result()
            except Exception as exc:
                logger.error("Fetch failed for %s: %s", url, exc)
                prepared[url] = None
    return prepared


def _extract_filings_parallel(
    *,
    ticker: str,
    feature: str,
    kind: FeatureKind,
    filings: list[Filing],
    prepared: dict[str, PreparedFiling | None],
    workers: int,
) -> list[ExtractResult]:
    if not filings:
        return []

    ordered: list[ExtractResult | None] = [None] * len(filings)

    def work(index: int, filing: Filing) -> ExtractResult:
        doc = prepared.get(filing.url)
        if not doc:
            period = "annual" if filing.form_type == "10-K" else "quarterly"
            return ExtractResult(
                ticker=ticker,
                feature=feature,
                period_type=period,
                filing_url=filing.url,
                filing_date=filing.filing_date,
                form_type=filing.form_type,
                error="Failed to fetch",
            )
        extraction = extract_from_prepared(doc, feature, filing.form_type, kind)
        return _to_result(ticker, feature, filing, extraction)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(work, i, f): i for i, f in enumerate(filings)}
        for fut in as_completed(futures):
            ordered[futures[fut]] = fut.result()

    return [r for r in ordered if r is not None]


def _to_result(
    ticker: str,
    feature: str,
    filing: Filing,
    extraction: NumericExtraction | ScoreExtraction,
) -> ExtractResult:
    base = dict(
        ticker=ticker,
        feature=feature,
        filing_url=filing.url,
        filing_date=filing.filing_date,
        form_type=filing.form_type,
    )
    if isinstance(extraction, NumericExtraction):
        period = extraction.period_type or ("annual" if filing.form_type == "10-K" else "quarterly")
        return ExtractResult(
            **base,
            value=extraction.value,
            period_type=period,
            unit=extraction.unit,
            period_end=extraction.period_end,
            label_matched=extraction.label_matched,
            quote=extraction.quote,
            confidence=extraction.confidence,
            source=extraction.source,
            evidence=extraction.statement,
        )

    return ExtractResult(
        **base,
        value=extraction.score,
        value_type="score",
        evidence=extraction.evidence,
        quote=extraction.quote,
        confidence=extraction.confidence,
        source=extraction.source,
    )
