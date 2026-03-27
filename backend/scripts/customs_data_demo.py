"""Customs data discovery demo.

Purpose:
- Probe likely customs/import-export evidence from web search results.
- Extract structured signals (period, direction, partner countries, HS clues, source URL).
- Provide a concrete summary that can be plugged into LeadExtractAgent later.

Run:
    cd backend
    python scripts/customs_data_demo.py --company "ABC GmbH" --country Germany --product "micro switch"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

# Ensure `backend/` is on sys.path when running as a script:
#   python scripts/customs_data_demo.py ...
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from tools.google_search import GoogleSearchTool

_CUSTOMS_SITES = [
    "panjiva.com",
    "importgenius.com",
    "volza.com",
    "trademo.com",
    "exportgenius.in",
    "zauba.com",
    "tradeatlas.com",
]

_COUNTRY_WORDS = [
    "united states", "usa", "germany", "france", "italy", "spain", "poland", "netherlands",
    "belgium", "uk", "united kingdom", "china", "india", "turkey", "mexico", "brazil",
    "canada", "japan", "korea", "vietnam", "thailand", "indonesia", "malaysia", "uae",
]

_IGNORE_COMPANY_TOKENS = {
    "co", "company", "corp", "corporation", "inc", "llc", "ltd", "limited", "gmbh", "ag", "sa", "bv", "srl",
}

_GENERIC_DIRECTORY_HINTS = [
    "/companies", "/importers", "/exporters", "/importers_exporters",
    "/directory", "/business-directory", "/category/",
]


@dataclass
class CustomsSignal:
    source_url: str
    source_title: str
    period: str
    trade_direction: str
    partner_countries: list[str]
    hs_codes: list[str]
    product_clues: list[str]
    confidence: float


def build_customs_queries(company_name: str, country: str = "", product_keywords: Iterable[str] | None = None) -> list[str]:
    """Build targeted queries to maximize customs-data hit rate."""
    product_keywords = list(product_keywords or [])
    product_part = " ".join(product_keywords[:3]).strip()
    base = [
        f'"{company_name}" customs data',
        f'"{company_name}" import export records',
        f'"{company_name}" bill of lading',
        f'"{company_name}" shipment records',
        f'"{company_name}" importer',
        f'"{company_name}" exporter',
        f'"{company_name}" hs code',
        f'"{company_name}" shipments from',
    ]
    if country:
        base.append(f'"{company_name}" {country} import export')
    if product_part:
        base.append(f'"{company_name}" {product_part} hs code shipments')

    site_queries = [f'site:{d} "{company_name}"' for d in _CUSTOMS_SITES]
    return base + site_queries


def _company_tokens(company_name: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", company_name.lower())
    filtered = [t for t in tokens if len(t) >= 3 and t not in _IGNORE_COMPANY_TOKENS]
    # keep stable unique order
    out: list[str] = []
    for t in filtered:
        if t not in out:
            out.append(t)
    return out


def _company_match_strength(company_name: str, title: str, link: str) -> float:
    """Return company-match score [0,1] based on token overlap in title/snippet/url path."""
    tokens = _company_tokens(company_name)
    if not tokens:
        return 0.0
    # IMPORTANT: do NOT use snippet for entity match; snippets often contain query echoes.
    hay = f"{title.lower()} {urlparse(link).path.lower()}"
    hit = sum(1 for t in tokens if t in hay)
    ratio = hit / max(len(tokens), 1)
    if ratio >= 0.8:
        return 1.0
    if ratio >= 0.5:
        return 0.7
    if ratio > 0:
        return 0.35
    return 0.0


def _is_company_specific_page(link: str) -> bool:
    p = urlparse(link).path.lower()
    if not p or p == "/":
        return False
    return not any(h in p for h in _GENERIC_DIRECTORY_HINTS)


def _extract_period(text: str) -> str:
    years = re.findall(r"\b(20\d{2})\b", text)
    ym = re.findall(r"\b(20\d{2}[-/](?:0?[1-9]|1[0-2]))\b", text)
    month_year = re.findall(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+20\d{2}\b", text, re.IGNORECASE)
    quarter = re.findall(r"\bQ[1-4]\s*20\d{2}\b", text, re.IGNORECASE)
    if month_year:
        return month_year[0]
    if quarter:
        return quarter[0].upper().replace("  ", " ")
    if ym:
        if len(ym) >= 2:
            return f"{ym[0]} to {ym[-1]}"
        return ym[0]
    valid_years = [y for y in years if int(y) >= 2016]
    if len(valid_years) >= 2:
        return f"{valid_years[0]}-{valid_years[-1]}"
    if valid_years:
        return valid_years[0]
    return ""


def _extract_direction(text: str) -> str:
    t = text.lower()
    has_import = any(k in t for k in ["import", "imports", "importer"])
    has_export = any(k in t for k in ["export", "exports", "exporter"])
    if has_import and has_export:
        return "import_export"
    if has_import:
        return "import"
    if has_export:
        return "export"
    return "unknown"


def _extract_partner_countries(text: str) -> list[str]:
    t = text.lower()
    # Prefer contextual matches only (from/to/exported to/imported from/shipped to)
    contexts = re.findall(
        r"(?:from|to|imported from|exported to|shipped to|origin|destination)\s+([a-z\s]{3,40})",
        t,
    )
    context_text = " ".join(contexts)
    hay = context_text if context_text.strip() else t
    found = [c.title() for c in _COUNTRY_WORDS if c in hay]
    # normalize short names
    normalized = []
    for c in found:
        if c == "Usa":
            c = "United States"
        elif c == "Uk":
            c = "United Kingdom"
        if c not in normalized:
            normalized.append(c)
    return normalized[:5]


def _extract_hs_codes(text: str) -> list[str]:
    # Strict: only take codes around explicit HS context.
    hs_context = re.findall(
        r"(?:hs|hsn)\s*(?:code)?\s*[:#-]?\s*([0-9]{6,10})",
        text,
        re.IGNORECASE,
    )
    out: list[str] = []
    for code in hs_context:
        # Drop obvious noise: long IDs or unlikely codes with leading zeros spam.
        if len(code) not in (6, 8, 10):
            continue
        if code not in out:
            out.append(code)
    return out[:5]


def _extract_product_clues(text: str, product_keywords: Iterable[str]) -> list[str]:
    t = text.lower()
    clues: list[str] = []
    for kw in product_keywords:
        k = kw.strip().lower()
        if k and k in t and kw not in clues:
            clues.append(kw)
    # fallback nouns around shipment words
    if not clues:
        m = re.findall(r"(?:shipments?|imports?|exports?)\s+of\s+([a-z0-9\-\s]{3,40})", t)
        for x in m[:3]:
            cleaned = " ".join(x.split())
            if cleaned and cleaned not in clues:
                clues.append(cleaned)
    return clues[:5]


def extract_signal_from_result(
    result: dict,
    company_name: str,
    product_keywords: Iterable[str],
    country_hint: str = "",
) -> CustomsSignal | None:
    """Extract a customs signal from one search result row."""
    title = str(result.get("title", ""))
    link = str(result.get("link", ""))
    snippet = str(result.get("snippet", ""))
    text = f"{title} {snippet}"

    # must contain at least one customs/trade cue
    t = text.lower()
    if not any(k in t for k in ["import", "export", "shipment", "bill of lading", "customs", "trade data"]):
        return None

    company_score = _company_match_strength(company_name, title, link)
    if company_score < 0.5:
        return None
    if not _is_company_specific_page(link):
        return None

    period = _extract_period(text)
    direction = _extract_direction(text)
    partners = _extract_partner_countries(text)
    hs_codes = _extract_hs_codes(text)
    clues = _extract_product_clues(text, product_keywords)
    country_hit = bool(country_hint and country_hint.lower() in text.lower())

    # hard gate: at least two strong evidence dimensions
    strong_dims = 0
    if period:
        strong_dims += 1
    if direction != "unknown":
        strong_dims += 1
    if partners:
        strong_dims += 1
    if hs_codes:
        strong_dims += 1
    if clues:
        strong_dims += 1
    if country_hit:
        strong_dims += 1
    if strong_dims < 2:
        return None

    # heuristic confidence
    conf = 0.1 + (0.35 * company_score)
    if any(site in link.lower() for site in _CUSTOMS_SITES):
        conf += 0.3
    if period:
        conf += 0.15
    if direction != "unknown":
        conf += 0.15
    if partners:
        conf += 0.1
    if hs_codes:
        conf += 0.1
    if clues:
        conf += 0.1
    if country_hit:
        conf += 0.05

    return CustomsSignal(
        source_url=link,
        source_title=title,
        period=period,
        trade_direction=direction,
        partner_countries=partners,
        hs_codes=hs_codes,
        product_clues=clues,
        confidence=min(conf, 1.0),
    )


def summarize_signals(signals: list[CustomsSignal]) -> dict:
    if not signals:
        return {
            "status": "no_data",
            "summary": "No concrete customs data found",
            "evidence": [],
        }

    best = sorted(signals, key=lambda s: s.confidence, reverse=True)[:5]

    periods = [s.period for s in best if s.period]
    directions = [s.trade_direction for s in best if s.trade_direction != "unknown"]
    partners: list[str] = []
    for s in best:
        for p in s.partner_countries:
            if p not in partners:
                partners.append(p)

    summary = {
        "status": "ok",
        "period_hint": periods[0] if periods else "",
        "direction_hint": directions[0] if directions else "unknown",
        "partner_countries": partners[:8],
        "evidence": [
            {
                "source_url": s.source_url,
                "source_title": s.source_title,
                "period": s.period,
                "trade_direction": s.trade_direction,
                "partner_countries": s.partner_countries,
                "hs_codes": s.hs_codes,
                "product_clues": s.product_clues,
                "confidence": round(s.confidence, 3),
            }
            for s in best
        ],
    }
    return summary


async def run_customs_demo(company_name: str, country: str = "", product_keywords: list[str] | None = None) -> dict:
    settings = get_settings()
    tool = GoogleSearchTool(settings)
    product_keywords = product_keywords or []

    queries = build_customs_queries(company_name, country=country, product_keywords=product_keywords)
    all_results: list[dict] = []
    try:
        for q in queries:
            rows = await tool.search(q, num=5)
            all_results.extend(rows)
    finally:
        await tool.close()

    seen = set()
    uniq = []
    for r in all_results:
        link = r.get("link", "")
        if link and link not in seen:
            seen.add(link)
            uniq.append(r)

    signals: list[CustomsSignal] = []
    for r in uniq:
        sig = extract_signal_from_result(r, company_name=company_name, product_keywords=product_keywords, country_hint=country)
        if sig is not None:
            signals.append(sig)

    return {
        "company": company_name,
        "queries": queries,
        "raw_result_count": len(uniq),
        "signals_count": len(signals),
        "customs_summary": summarize_signals(signals),
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Customs discovery demo")
    p.add_argument("--company", required=True, help="Company name")
    p.add_argument("--country", default="", help="Country hint")
    p.add_argument("--product", action="append", default=[], help="Product keyword (repeatable)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    data = asyncio.run(run_customs_demo(args.company, country=args.country, product_keywords=args.product))
    print(json.dumps(data, ensure_ascii=False, indent=2))
