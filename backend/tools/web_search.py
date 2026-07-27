"""WebSearchTool — unified web search with multi-backend round-robin.

Google Search and Google Maps are configured separately through `SERPER_API_KEY`.
This tool supports Tavily and You.com backends, each with multi-key round-robin.

Multi-key support (per backend):
    TAVILY_API_KEY=key1,key2
    YOUCOM_API_KEY=key1,key2

Keys are rotated in round-robin per-process using a thread-safe atomic counter,
so concurrent searches spread load evenly across all configured keys.
"""

from __future__ import annotations

import itertools
import logging
import threading
from typing import Optional

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


# ── Key pool helpers ──────────────────────────────────────────────────────────

def _parse_keys(raw: str) -> list[str]:
    """Split a comma-separated key string into a list of non-empty keys."""
    return [k.strip() for k in raw.split(",") if k.strip()]


class _RoundRobinPool:
    """Thread-safe round-robin key pool."""

    def __init__(self, keys: list[str]) -> None:
        self._keys = keys
        self._cycle = itertools.cycle(keys)
        self._lock = threading.Lock()

    def next_key(self) -> str:
        with self._lock:
            return next(self._cycle)

    def __len__(self) -> int:
        return len(self._keys)

    def __bool__(self) -> bool:
        return bool(self._keys)


# ── Per-backend search implementations ───────────────────────────────────────

def _is_invalid_country_error(exc: Exception) -> bool:
    """Return True when the Tavily error is specifically about an unsupported country code."""
    return "invalid country" in str(exc).lower()


def _parse_tavily_response(response: dict) -> list[dict]:
    results = []
    for i, item in enumerate(response.get("results", []), start=1):
        content = item.get("content", "")
        snippet = content[:400] + "..." if len(content) > 400 else content
        results.append({
            "title": item.get("title", ""),
            "link": item.get("url", ""),
            "snippet": snippet,
            "position": i,
        })
    return results


async def _tavily_search(
    api_key: str,
    query: str,
    num: int,
    gl: str,
) -> list[dict]:
    import asyncio

    try:
        from tavily import TavilyClient
    except ImportError:
        raise ImportError("tavily-python is required. Install: pip install tavily-python")

    client = TavilyClient(api_key)
    max_results = min(num, 20)

    def _sync_with_country():
        return client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            country=gl,
        )

    def _sync_no_country():
        return client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
        )

    use_country = bool(gl and len(gl) == 2)

    if use_country:
        try:
            response = await asyncio.to_thread(_sync_with_country)
            return _parse_tavily_response(response)
        except Exception as e:
            if _is_invalid_country_error(e):
                # Tavily doesn't support this country code — retry without it
                logger.warning(
                    "[WebSearch] Tavily: unsupported country=%r, retrying without country param", gl
                )
                response = await asyncio.to_thread(_sync_no_country)
                return _parse_tavily_response(response)
            raise
    else:
        response = await asyncio.to_thread(_sync_no_country)
        return _parse_tavily_response(response)


async def _youcom_search(
    api_key: str,
    query: str,
    num: int,
    gl: str,
) -> list[dict]:
    import asyncio

    import requests

    YOUCOM_SEARCH_URL = "https://ydc-index.io/v1/search"

    # You.com doesn't have native geo params — append as site hint
    effective_query = query
    if gl and len(gl) == 2:
        effective_query = f"{query} site:.{gl}"

    def _sync():
        resp = requests.post(
            YOUCOM_SEARCH_URL,
            headers={
                "Accept": "application/json",
                "X-API-Key": api_key,
            },
            json={"query": effective_query, "count": min(num, 20)},
            timeout=30,
        )
        if resp.status_code == 429:
            raise RuntimeError("You.com Search rate limit exceeded (429)")
        if resp.status_code == 401:
            raise RuntimeError("You.com API Key is invalid or expired")
        if resp.status_code == 403:
            raise RuntimeError("You.com API Key has insufficient permissions")
        if resp.status_code != 200:
            raise RuntimeError(f"You.com Search failed (Status {resp.status_code})")
        return resp.json()

    response = await asyncio.to_thread(_sync)

    results = []
    for i, item in enumerate(response.get("results", []), start=1):
        snippets = item.get("snippets", [])
        snippet_raw = (
            snippets[0]
            if isinstance(snippets, list) and snippets
            else item.get("description", "")
        )
        snippet = snippet_raw[:300] + "..." if len(snippet_raw) > 300 else snippet_raw
        results.append({
            "title": item.get("title", ""),
            "link": item.get("url", ""),
            "snippet": snippet,
            "position": i,
        })
    return results


class WebSearchTool:
    """Unified web search tool with multi-backend round-robin.

    Supports Tavily and You.com backends simultaneously.
    Keys from each backend are rotated in round-robin independently.

    Usage:
        tool = WebSearchTool()
        results = await tool.search("solar panel distributor Germany", gl="de", hl="de")
        await tool.close()
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

        self._tavily_pool = _RoundRobinPool(_parse_keys(self._settings.tavily_api_key))
        self._youcom_pool = _RoundRobinPool(_parse_keys(self._settings.youcom_api_key))

        backends = []
        if self._tavily_pool:
            backends.append(f"Tavily({len(self._tavily_pool)} key(s))")
        if self._youcom_pool:
            backends.append(f"You.com({len(self._youcom_pool)} key(s))")

        if not backends:
            raise ValueError(
                "No general web search API key configured. Set TAVILY_API_KEY and/or YOUCOM_API_KEY."
            )

        self._backends = backends
        logger.info("[WebSearch] Backends: %s", ", ".join(backends))

    @property
    def backend(self) -> str:
        """Comma-separated active backend names."""
        return ", ".join(self._backends)

    async def search(
        self,
        query: str,
        *,
        num: int = 10,
        gl: str = "",
        hl: str = "",
    ) -> list[dict]:
        """Execute a general web search.

        Chooses a backend using round-robin across all available backends.
        Within each backend, keys are also rotated round-robin.

        Args:
            query: Search query string.
            num: Number of results (max 20).
            gl: Country code (e.g. "de", "us").
            hl: Language code (e.g. "de", "en").

        Returns:
            List of dicts with keys: title, link, snippet, position.
        """
        # Round-robin across backends
        with threading.Lock():
            if not hasattr(self, "_backend_cycle"):
                self._backend_cycle = itertools.cycle(self._backends)
            backend_name = next(self._backend_cycle)

        if backend_name.startswith("You.com") and self._youcom_pool:
            key = self._youcom_pool.next_key()
            return await _youcom_search(key, query, num, gl)
        elif self._tavily_pool:
            key = self._tavily_pool.next_key()
            return await _tavily_search(key, query, num, gl)
        elif self._youcom_pool:
            # Tavily pool empty but You.com available
            key = self._youcom_pool.next_key()
            return await _youcom_search(key, query, num, gl)
        else:
            raise ValueError("No search backend available")

    async def close(self) -> None:
        return None
