"""
Unified search client — supports Serper.dev and Tavily interchangeably.

Configuration (.env):
    SEARCH_PROVIDER=serper   # default — uses SERPER_API_KEY
    SEARCH_PROVIDER=tavily   # uses TAVILY_API_KEY

Both providers return a list of dicts with the same schema:
    {
        "title":       str,
        "url":         str,
        "domain":      str,
        "snippet":     str,
        "score":       float,   # relevance score (0-1); Serper = 1.0 (not provided)
        "provider":    str,     # "serper" | "tavily"
    }
"""

from __future__ import annotations

import logging
import os
import re
import time
import random
import requests
from typing import List, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Public API ────────────────────────────────────────────────────────────


def get_search_provider() -> str:
    """Return the configured SEARCH_PROVIDER ('serper' or 'tavily')."""
    return os.getenv("SEARCH_PROVIDER", "serper").strip().lower()


def is_search_available() -> bool:
    """Return True if the configured search provider has an API key."""
    provider = get_search_provider()
    if provider == "tavily":
        return bool(os.getenv("TAVILY_API_KEY"))
    return bool(os.getenv("SERPER_API_KEY"))


def search(
    query: str,
    num_results: int = 10,
    gl: str = "us",
    retries: int = 3,
) -> List[Dict]:
    """
    Execute a web search and return a normalised result list.

    Args:
        query:       Search query string.
        num_results: Maximum number of results to return.
        gl:          Geographic locale code (Serper only; Tavily ignores it).
        retries:     Number of retry attempts on transient errors.

    Returns:
        List of result dicts (title, url, domain, snippet, score, provider).

    Raises:
        ValueError:  If no API key is configured.
        RuntimeError: If all retry attempts fail.
    """
    provider = get_search_provider()
    if provider == "tavily":
        return _search_tavily(query, num_results, retries)
    return _search_serper(query, num_results, gl, retries)


# ── Serper ────────────────────────────────────────────────────────────────

_SERPER_URL = "https://google.serper.dev/search"


def _search_serper(query: str, num_results: int, gl: str, retries: int) -> List[Dict]:
    api_key = os.getenv("SERPER_API_KEY", "")
    if not api_key:
        raise ValueError("SERPER_API_KEY is not set")

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "gl": gl, "num": min(num_results, 20)}

    last_exc: Exception = RuntimeError("Unknown error")
    for attempt in range(retries):
        try:
            resp = requests.post(_SERPER_URL, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            return _normalise_serper(data, num_results)
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep((2 ** attempt) * random.uniform(0.5, 1.5))

    raise RuntimeError(f"Serper search failed after {retries} retries: {last_exc}") from last_exc


def _normalise_serper(data: dict, limit: int) -> List[Dict]:
    results = []
    for item in data.get("organic", [])[:limit]:
        url = item.get("link", "")
        results.append({
            "title":    item.get("title", ""),
            "url":      url,
            "domain":   _extract_domain(url),
            "snippet":  item.get("snippet", ""),
            "score":    1.0,
            "provider": "serper",
        })
    return results


# ── Tavily ────────────────────────────────────────────────────────────────

def _search_tavily(query: str, num_results: int, retries: int) -> List[Dict]:
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set")

    try:
        from tavily import TavilyClient  # lazy import
    except ImportError as exc:
        raise RuntimeError(
            "tavily-python is not installed. Run: pip install tavily-python"
        ) from exc

    client = TavilyClient(api_key=api_key)

    last_exc: Exception = RuntimeError("Unknown error")
    for attempt in range(retries):
        try:
            resp = client.search(
                query=query,
                max_results=min(num_results, 20),
                search_depth="basic",
            )
            return _normalise_tavily(resp, num_results)
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep((2 ** attempt) * random.uniform(0.5, 1.5))

    raise RuntimeError(f"Tavily search failed after {retries} retries: {last_exc}") from last_exc


def _normalise_tavily(resp: dict, limit: int) -> List[Dict]:
    results = []
    for item in resp.get("results", [])[:limit]:
        url = item.get("url", "")
        results.append({
            "title":    item.get("title", ""),
            "url":      url,
            "domain":   _extract_domain(url),
            "snippet":  item.get("content", ""),
            "score":    float(item.get("score", 0.0)),
            "provider": "tavily",
        })
    return results


# ── Helpers ────────────────────────────────────────────────────────────────

_DOMAIN_RE = re.compile(r"https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")


def _extract_domain(url: str) -> str:
    m = _DOMAIN_RE.search(url)
    return m.group(1) if m else ""
