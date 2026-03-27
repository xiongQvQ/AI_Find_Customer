"""Compare customs-page fetch strategies: raw fetch vs Jina Reader vs Playwright.

Run:
    cd backend
    python scripts/customs_fetch_strategy_demo.py --url "https://example.com/page"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from tools.jina_reader import JinaReaderTool

TRADE_TERMS = [
    "import", "imports", "importer", "export", "exports", "exporter",
    "shipment", "shipments", "bill of lading", "customs", "trade data",
    "hs code", "consignee", "shipper",
]


def analyze_text(text: str, company_name: str = "") -> dict[str, Any]:
    """Return simple extractability metrics for fetched content."""
    lower = text.lower()
    trade_hits = [term for term in TRADE_TERMS if term in lower]
    years = re.findall(r"\b(20\d{2})\b", text)
    hs_codes = re.findall(r"(?:hs|hsn)\s*(?:code)?\s*[:#-]?\s*([0-9]{6,10})", text, re.IGNORECASE)

    company_tokens = [t for t in re.findall(r"[a-z0-9]+", company_name.lower()) if len(t) >= 3]
    company_hits = [t for t in company_tokens if t in lower]

    return {
        "chars": len(text),
        "non_whitespace_chars": len(re.sub(r"\s+", "", text)),
        "trade_terms_found": trade_hits,
        "trade_term_count": len(trade_hits),
        "years_found": sorted(set(years)),
        "hs_codes_found": sorted(set(hs_codes)),
        "company_token_hits": company_hits,
        "has_structured_trade_signal": bool(trade_hits and (years or hs_codes)),
        "preview": text[:500],
    }


async def fetch_raw(url: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 AIHunterDemo/1.0"})
            resp.raise_for_status()
            text = resp.text
        return {"method": "raw_fetch", "ok": True, "elapsed_ms": round((time.perf_counter() - start) * 1000, 1), "text": text}
    except Exception as e:
        return {"method": "raw_fetch", "ok": False, "elapsed_ms": round((time.perf_counter() - start) * 1000, 1), "error": str(e), "text": ""}


async def fetch_jina(url: str) -> dict[str, Any]:
    start = time.perf_counter()
    tool = JinaReaderTool(get_settings())
    try:
        text = await tool.read(url)
        return {"method": "jina_reader", "ok": True, "elapsed_ms": round((time.perf_counter() - start) * 1000, 1), "text": text}
    except Exception as e:
        return {"method": "jina_reader", "ok": False, "elapsed_ms": round((time.perf_counter() - start) * 1000, 1), "error": str(e), "text": ""}
    finally:
        await tool.close()


async def fetch_playwright(url: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        from playwright.async_api import async_playwright
    except Exception:
        return {"method": "playwright", "ok": False, "elapsed_ms": 0.0, "error": "playwright_not_installed", "text": ""}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=45000)
            text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            await browser.close()
        return {"method": "playwright", "ok": True, "elapsed_ms": round((time.perf_counter() - start) * 1000, 1), "text": text}
    except Exception as e:
        return {"method": "playwright", "ok": False, "elapsed_ms": round((time.perf_counter() - start) * 1000, 1), "error": str(e), "text": ""}


async def compare_fetchers(url: str, company_name: str = "") -> dict[str, Any]:
    results = await asyncio.gather(fetch_raw(url), fetch_jina(url), fetch_playwright(url))
    compared = []
    for item in results:
        analyzed = analyze_text(item.get("text", ""), company_name=company_name) if item.get("ok") else {}
        compared.append({
            "method": item["method"],
            "ok": item["ok"],
            "elapsed_ms": item["elapsed_ms"],
            "error": item.get("error", ""),
            "analysis": analyzed,
        })

    ranked = sorted(
        compared,
        key=lambda x: (
            1 if x["ok"] else 0,
            x.get("analysis", {}).get("has_structured_trade_signal", False),
            x.get("analysis", {}).get("trade_term_count", 0),
            x.get("analysis", {}).get("non_whitespace_chars", 0),
        ),
        reverse=True,
    )
    return {"url": url, "company_name": company_name, "results": compared, "best_method": ranked[0]["method"] if ranked else ""}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare customs-page fetch strategies")
    parser.add_argument("--url", action="append", required=True, help="URL to test (repeatable)")
    parser.add_argument("--company", default="", help="Optional company name for token-hit analysis")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    payload = []
    for url in args.url:
        payload.append(await compare_fetchers(url, company_name=args.company))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_main())
