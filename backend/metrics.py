"""Feature → XBRL tag aliases and synonym expansion."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Ordered candidates: first match with data wins.
# Each entry is (taxonomy, tag).
FEATURE_TAG_MAP: dict[str, list[tuple[str, str]]] = {
    "revenue": [
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "SalesRevenueNet"),
        ("us-gaap", "Revenues"),
        ("us-gaap", "SalesRevenueGoodsNet"),
        ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
    ],
    "total revenue": [
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "SalesRevenueNet"),
        ("us-gaap", "Revenues"),
    ],
    "net sales": [
        ("us-gaap", "SalesRevenueNet"),
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "Revenues"),
    ],
    "net income": [
        ("us-gaap", "NetIncomeLoss"),
        ("us-gaap", "ProfitLoss"),
    ],
    "earnings": [
        ("us-gaap", "NetIncomeLoss"),
        ("us-gaap", "ProfitLoss"),
    ],
    "assets": [
        ("us-gaap", "Assets"),
    ],
    "total assets": [
        ("us-gaap", "Assets"),
    ],
    "liabilities": [
        ("us-gaap", "Liabilities"),
    ],
    "total liabilities": [
        ("us-gaap", "Liabilities"),
    ],
    "book value": [
        ("us-gaap", "StockholdersEquity"),
        ("us-gaap", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    ],
    "stockholders equity": [
        ("us-gaap", "StockholdersEquity"),
    ],
    "shareholders equity": [
        ("us-gaap", "StockholdersEquity"),
    ],
    "equity": [
        ("us-gaap", "StockholdersEquity"),
    ],
    "cash": [
        ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
        ("us-gaap", "Cash"),
    ],
    "cash and cash equivalents": [
        ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
    ],
    "long term debt": [
        ("us-gaap", "LongTermDebt"),
        ("us-gaap", "LongTermDebtNoncurrent"),
    ],
    "debt": [
        ("us-gaap", "LongTermDebt"),
        ("us-gaap", "DebtCurrent"),
        ("us-gaap", "LongTermDebtAndCapitalLeaseObligations"),
    ],
    "research and development": [
        ("us-gaap", "ResearchAndDevelopmentExpense"),
    ],
    "r&d": [
        ("us-gaap", "ResearchAndDevelopmentExpense"),
    ],
    "rd spending": [
        ("us-gaap", "ResearchAndDevelopmentExpense"),
    ],
    "operating income": [
        ("us-gaap", "OperatingIncomeLoss"),
    ],
    "gross profit": [
        ("us-gaap", "GrossProfit"),
    ],
    "cost of revenue": [
        ("us-gaap", "CostOfRevenue"),
        ("us-gaap", "CostOfGoodsAndServicesSold"),
    ],
    "employees": [
        ("dei", "EntityNumberOfEmployees"),
    ],
    "number of employees": [
        ("dei", "EntityNumberOfEmployees"),
    ],
    "headcount": [
        ("dei", "EntityNumberOfEmployees"),
    ],
    "shares outstanding": [
        ("dei", "EntityCommonStockSharesOutstanding"),
    ],
    "common shares outstanding": [
        ("dei", "EntityCommonStockSharesOutstanding"),
    ],
    "eps": [
        ("us-gaap", "EarningsPerShareDiluted"),
        ("us-gaap", "EarningsPerShareBasic"),
    ],
    "earnings per share": [
        ("us-gaap", "EarningsPerShareDiluted"),
        ("us-gaap", "EarningsPerShareBasic"),
    ],
    "diluted eps": [
        ("us-gaap", "EarningsPerShareDiluted"),
    ],
    "capex": [
        ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
    ],
    "capital expenditures": [
        ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
    ],
}

# Synonyms used for passage retrieval / prompt hints.
FEATURE_SYNONYMS: dict[str, list[str]] = {
    "revenue": ["net sales", "total revenue", "sales", "net revenue"],
    "total revenue": ["revenue", "net sales", "sales"],
    "net sales": ["revenue", "total net sales"],
    "book value": ["stockholders' equity", "shareholders' equity", "total equity", "stockholders equity"],
    "employees": ["number of employees", "headcount", "full-time equivalent", "workforce"],
    "number of employees": ["employees", "headcount", "workforce"],
    "r&d": ["research and development", "research & development"],
    "research and development": ["r&d", "product development"],
    "debt": ["long-term debt", "borrowings", "notes payable"],
    "cash": ["cash and cash equivalents", "cash equivalents"],
    "net income": ["net earnings", "profit", "net loss"],
    "ai exposure": ["artificial intelligence", "machine learning", "generative ai", "AI"],
    "esg": ["environmental", "social", "governance", "sustainability", "climate"],
}

QUALITATIVE_HINTS = (
    "exposure",
    "strategy",
    "commitment",
    "focus",
    "involvement",
    "assessment",
    "risk culture",
    "esg",
    "sustainability",
    "innovation",
    "digital transformation",
    "ai strategy",
    "crypto",
    "recession",
)

NUMERIC_HINTS = (
    "revenue",
    "sales",
    "income",
    "assets",
    "liabilities",
    "equity",
    "cash",
    "debt",
    "employees",
    "headcount",
    "earnings",
    "profit",
    "loss",
    "capex",
    "expense",
    "eps",
    "shares",
    "book value",
    "r&d",
    "margin",
)


@dataclass(frozen=True)
class TagCandidate:
    taxonomy: str
    tag: str


def normalize_feature(feature: str) -> str:
    text = feature.lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def resolve_xbrl_tags(feature: str) -> list[TagCandidate]:
    key = normalize_feature(feature)
    if key in FEATURE_TAG_MAP:
        return [TagCandidate(t, tag) for t, tag in FEATURE_TAG_MAP[key]]

    # Fuzzy: any map key contained in feature or vice versa.
    hits: list[TagCandidate] = []
    seen: set[tuple[str, str]] = set()
    for map_key, tags in FEATURE_TAG_MAP.items():
        if map_key in key or key in map_key:
            for taxonomy, tag in tags:
                item = (taxonomy, tag)
                if item not in seen:
                    seen.add(item)
                    hits.append(TagCandidate(taxonomy, tag))
    return hits


def feature_synonyms(feature: str) -> list[str]:
    key = normalize_feature(feature)
    syns = [feature, key, *FEATURE_SYNONYMS.get(key, [])]
    # Also pull synonyms for partial keys.
    for map_key, values in FEATURE_SYNONYMS.items():
        if map_key in key or key in map_key:
            syns.extend(values)
            syns.append(map_key)
    # de-dupe preserve order
    out: list[str] = []
    seen: set[str] = set()
    for s in syns:
        s2 = s.strip()
        low = s2.lower()
        if s2 and low not in seen:
            seen.add(low)
            out.append(s2)
    return out


def heuristic_feature_kind(feature: str) -> str | None:
    """Return 'numeric' / 'qualitative' if confident, else None."""
    key = normalize_feature(feature)
    if key in FEATURE_TAG_MAP:
        return "numeric"
    if any(h in key for h in QUALITATIVE_HINTS):
        return "qualitative"
    if any(h in key for h in NUMERIC_HINTS):
        return "numeric"
    return None
