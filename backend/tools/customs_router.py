"""Provider-aware customs data discovery for lead enrichment.

This module is intentionally code-first, not prompt-first:
- discover likely provider pages via search
- fetch them with provider-specific strategy
- extract concrete trade signals
- return structured evidence or an explicit no-data result
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from tools.google_search import GoogleSearchTool
from tools.jina_reader import JinaReaderTool

logger = logging.getLogger(__name__)

_PROVIDER_DOMAINS = {
    "importgenius": "importgenius.com",
    "volza": "volza.com",
    "trademo": "trademo.com",
    "panjiva": "panjiva.com",
    "exportgenius": "exportgenius.in",
    "zauba": "zauba.com",
    "tradeatlas": "tradeatlas.com",
}

_COUNTRY_WORDS = [
    "united states", "usa", "germany", "france", "italy", "spain", "poland", "netherlands",
    "belgium", "uk", "united kingdom", "china", "india", "turkey", "mexico", "brazil",
    "canada", "japan", "korea", "vietnam", "thailand", "indonesia", "malaysia", "uae",
]

_IGNORE_COMPANY_TOKENS = {
    "co", "company", "corp", "corporation", "inc", "llc", "ltd", "limited", "gmbh", "ag", "sa", "bv", "srl",
}

_INVALID_PAGE_HINTS = [
    "404",
    "not found",
    "performing security verification",
    "protect against malicious bots",
    "choose the largest & most trusted export-import trade data platform",
]


@dataclass
class CustomsEvidence:
    provider: str
    source_url: str
    source_title: str
    period: str
    trade_direction: str
    partner_countries: list[str]
    hs_codes: list[str]
    product_clues: list[str]
    fetch_method: str
    confidence: float

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "period": self.period,
            "trade_direction": self.trade_direction,
            "partner_countries": self.partner_countries,
            "hs_codes": self.hs_codes,
            "product_clues": self.product_clues,
            "fetch_method": self.fetch_method,
            "confidence": self.confidence,
        }


def _company_tokens(company_name: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", company_name.lower())
    out: list[str] = []
    for token in tokens:
        if len(token) < 3 or token in _IGNORE_COMPANY_TOKENS or token in out:
            continue
        out.append(token)
    return out


def _company_match_strength(company_name: str, title: str, link: str) -> float:
    tokens = _company_tokens(company_name)
    if not tokens:
        return 0.0
    hay = f"{title.lower()} {urlparse(link).path.lower()}"
    hits = sum(1 for token in tokens if token in hay)
    ratio = hits / len(tokens)
    if ratio >= 0.8:
        return 1.0
    if ratio >= 0.5:
        return 0.75
    if ratio > 0:
        return 0.35
    return 0.0


def _provider_for_url(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    for name, domain in _PROVIDER_DOMAINS.items():
        if domain in netloc:
            return name
    return ""


def build_customs_queries(
    company_name: str,
    *,
    website: str = "",
    country: str = "",
    product_keywords: list[str] | None = None,
) -> list[str]:
    product_keywords = [p.strip() for p in (product_keywords or []) if p and p.strip()]
    product_part = " ".join(product_keywords[:3])
    queries = [
        f'site:importgenius.com/importers "{company_name}"',
        f'site:importgenius.com/importers "{company_name}" "See Full Importer History"',
        f'site:volza.com/company-profile "{company_name}"',
        f'site:trademo.com "{company_name}" shipments',
        f'site:panjiva.com "{company_name}"',
        f'"{company_name}" customs data',
        f'"{company_name}" import export records',
        f'"{company_name}" bill of lading',
    ]
    if website:
        domain = urlparse(website).netloc.replace("www.", "")
        if domain:
            queries.append(f'"{company_name}" "{domain}" import export')
    if country:
        queries.append(f'"{company_name}" {country} importer')
    if product_part:
        queries.append(f'"{company_name}" {product_part} hs code shipments')
    return queries


def _extract_period(text: str) -> str:
    month_year = re.findall(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+20\d{2}\b", text, re.IGNORECASE)
    if month_year:
        return month_year[0]
    quarter = re.findall(r"\bQ[1-4]\s*20\d{2}\b", text, re.IGNORECASE)
    if quarter:
        return quarter[0].upper()
    years = [y for y in re.findall(r"\b(20\d{2})\b", text) if int(y) >= 2016]
    if len(years) >= 2:
        return f"{years[0]}-{years[-1]}"
    if years:
        return years[0]
    return ""


def _extract_direction(text: str) -> str:
    lower = text.lower()
    has_import = any(word in lower for word in ["import", "imports", "importer"])
    has_export = any(word in lower for word in ["export", "exports", "exporter"])
    if has_import and has_export:
        return "import_export"
    if has_import:
        return "import"
    if has_export:
        return "export"
    return "unknown"


def _extract_partner_countries(text: str) -> list[str]:
    lower = text.lower()
    contexts = re.findall(
        r"(?:from|to|imported from|exported to|shipped to|origin|destination)\s+([a-z\s]{3,40})",
        lower,
    )
    hay = " ".join(contexts) if contexts else lower
    found: list[str] = []
    for country in _COUNTRY_WORDS:
        normalized = "United States" if country == "usa" else "United Kingdom" if country == "uk" else country.title()
        if country in hay and normalized not in found:
            found.append(normalized)
    return found[:5]


def _extract_hs_codes(text: str) -> list[str]:
    codes = re.findall(r"(?:hs|hsn)\s*(?:code)?\s*[:#-]?\s*([0-9]{6,10})", text, re.IGNORECASE)
    out: list[str] = []
    for code in codes:
        if len(code) not in (6, 8, 10) or code in out:
            continue
        out.append(code)
    return out[:5]


def _extract_product_clues(text: str, product_keywords: list[str]) -> list[str]:
    lower = text.lower()
    clues: list[str] = []
    for kw in product_keywords:
        if kw.lower() in lower and kw not in clues:
            clues.append(kw)
    if clues:
        return clues[:5]
    fallback = re.findall(r"(?:shipments?|imports?|exports?)\s+of\s+([a-z0-9\-\s]{3,40})", lower)
    return [" ".join(item.split()) for item in fallback[:3] if item.strip()]


def _looks_invalid_page(text: str, *, company_name: str) -> str:
    lower = text.lower()
    if any(hint in lower for hint in _INVALID_PAGE_HINTS):
        return "provider_landing_or_challenge"
    tokens = _company_tokens(company_name)
    if tokens and not any(token in lower for token in tokens):
        return "company_not_present"
    return ""


def _extract_from_page(
    *,
    provider: str,
    source_url: str,
    source_title: str,
    text: str,
    company_name: str,
    product_keywords: list[str],
    fetch_method: str,
) -> CustomsEvidence | None:
    invalid_reason = _looks_invalid_page(text, company_name=company_name)
    if invalid_reason:
        logger.debug("[CustomsRouter] drop %s page %s: %s", provider, source_url, invalid_reason)
        return None

    period = _extract_period(text)
    direction = _extract_direction(text)
    partners = _extract_partner_countries(text)
    hs_codes = _extract_hs_codes(text)
    product_clues = _extract_product_clues(text, product_keywords)

    strong_dims = 0
    if period:
        strong_dims += 1
    if direction != "unknown":
        strong_dims += 1
    if partners:
        strong_dims += 1
    if hs_codes:
        strong_dims += 1
    if product_clues:
        strong_dims += 1
    if strong_dims < 2:
        return None

    confidence = min(1.0, 0.5 + strong_dims * 0.1)
    return CustomsEvidence(
        provider=provider,
        source_url=source_url,
        source_title=source_title,
        period=period,
        trade_direction=direction,
        partner_countries=partners,
        hs_codes=hs_codes,
        product_clues=product_clues,
        fetch_method=fetch_method,
        confidence=confidence,
    )


async def _fetch_raw(url: str) -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 AIHunter/1.0"})
            resp.raise_for_status()
            return resp.text, ""
    except Exception as e:
        return "", str(e)


async def _fetch_with_jina(jina: JinaReaderTool, url: str) -> tuple[str, str]:
    try:
        return await jina.read(url), ""
    except Exception as e:
        return "", str(e)


async def _fetch_provider_page(provider: str, url: str, jina: JinaReaderTool) -> tuple[str, str, str]:
    if provider == "importgenius":
        text, error = await _fetch_raw(url)
        if text:
            return text, "raw_fetch", ""
        text, error = await _fetch_with_jina(jina, url)
        return text, "jina_reader", error
    text, error = await _fetch_with_jina(jina, url)
    return text, "jina_reader", error


def _summarize(evidence: list[CustomsEvidence]) -> str:
    if not evidence:
        return "No concrete customs data found"
    best = evidence[0]
    parts = []
    if best.period:
        parts.append(f"period {best.period}")
    if best.trade_direction != "unknown":
        parts.append(best.trade_direction.replace("_", "/"))
    if best.partner_countries:
        parts.append(f"partners: {', '.join(best.partner_countries)}")
    if best.product_clues:
        parts.append(f"products: {', '.join(best.product_clues)}")
    if best.hs_codes:
        parts.append(f"HS: {', '.join(best.hs_codes)}")
    detail = "; ".join(parts) if parts else "customs/trade evidence found"
    return f"{best.provider}: {detail}. Source: {best.source_url}"


async def find_customs_data(
    *,
    company_name: str,
    google_search: GoogleSearchTool,
    jina_reader: JinaReaderTool,
    website: str = "",
    country: str = "",
    product_keywords: list[str] | None = None,
) -> dict:
    """Find concrete customs evidence for a company using provider-aware routing."""
    product_keywords = [p.strip() for p in (product_keywords or []) if p and p.strip()]
    queries = build_customs_queries(
        company_name,
        website=website,
        country=country,
        product_keywords=product_keywords,
    )

    raw_results: list[dict] = []
    for query in queries[:8]:
        try:
            raw_results.extend(await google_search.search(query, num=5))
        except Exception as e:
            logger.debug("[CustomsRouter] query failed %s: %s", query, e)

    ranked_candidates: list[tuple[float, str, dict]] = []
    for row in raw_results:
        link = str(row.get("link", ""))
        provider = _provider_for_url(link)
        if not provider:
            continue
        score = _company_match_strength(company_name, str(row.get("title", "")), link)
        if score < 0.5:
            continue
        ranked_candidates.append((score, provider, row))

    ranked_candidates.sort(key=lambda item: item[0], reverse=True)

    evidence: list[CustomsEvidence] = []
    seen_urls: set[str] = set()
    for _, provider, row in ranked_candidates[:4]:
        url = str(row.get("link", ""))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        text, fetch_method, error = await _fetch_provider_page(provider, url, jina_reader)
        if not text:
            logger.debug("[CustomsRouter] fetch failed %s via %s: %s", url, provider, error)
            continue
        item = _extract_from_page(
            provider=provider,
            source_url=url,
            source_title=str(row.get("title", "")),
            text=text,
            company_name=company_name,
            product_keywords=product_keywords,
            fetch_method=fetch_method,
        )
        if item:
            evidence.append(item)

    evidence.sort(key=lambda item: item.confidence, reverse=True)
    summary = _summarize(evidence)
    return {
        "status": "ok" if evidence else "no_data",
        "summary": summary,
        "company_name": company_name,
        "queries": queries,
        "evidence": [item.to_dict() for item in evidence[:5]],
    }
