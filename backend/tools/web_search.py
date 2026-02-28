"""WebSearchTool — unified general web search with multi-key round-robin rotation.

Priority: Tavily > Serper (Google fallback).
Google Maps search is handled separately by GoogleMapsSearchTool (always Serper).

Multi-key support:
    TAVILY_API_KEY=key1,key2

Keys are rotated in round-robin per-process using a thread-safe atomic counter,
so concurrent searches spread load evenly across all configured keys.
"""

from __future__ import annotations

import itertools
import logging
import threading
from typing import Optional

import httpx

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


async def _serper_search(
    client: httpx.AsyncClient,
    api_key: str,
    query: str,
    num: int,
    gl: str,
    hl: str,
) -> list[dict]:
    body: dict = {"q": query, "num": num}
    if gl:
        body["gl"] = gl
    if hl:
        body["hl"] = hl

    resp = await client.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=body,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "position": item.get("position", 0),
        })
    return results


# ── Main tool ─────────────────────────────────────────────────────────────────

class WebSearchTool:
    """Unified general web search tool with multi-key round-robin rotation.

    Priority: Tavily > Serper (fallback).
    Google Maps is NOT handled here — use GoogleMapsSearchTool directly.

    Usage:
        tool = WebSearchTool()
        results = await tool.search("solar panel distributor Germany", gl="de", hl="de")
        await tool.close()
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

        # Build key pools
        self._tavily_pool = _RoundRobinPool(_parse_keys(self._settings.tavily_api_key))
        self._serper_key = self._settings.serper_api_key.strip()

        # Determine active backend
        if self._tavily_pool:
            self._backend = "tavily"
            logger.info(
                "[WebSearch] Backend: Tavily (%d key(s))", len(self._tavily_pool)
            )
        elif self._serper_key:
            self._backend = "serper"
            logger.info("[WebSearch] Backend: Serper (Google) — fallback")
        else:
            raise ValueError(
                "No general web search API key configured. "
                "Set at least one of: TAVILY_API_KEY, SERPER_API_KEY"
            )

    @property
    def backend(self) -> str:
        """Active backend name: 'brave', 'tavily', or 'serper'."""
        return self._backend

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search(
        self,
        query: str,
        *,
        num: int = 10,
        gl: str = "",
        hl: str = "",
    ) -> list[dict]:
        """Execute a general web search.

        Automatically picks the next key from the round-robin pool.
        Falls through to the next backend if the current one fails.

        Args:
            query: Search query string.
            num: Number of results (max 20).
            gl: Country code (e.g. "de", "us").
            hl: Language code (e.g. "de", "en").

        Returns:
            List of dicts with keys: title, link, snippet, position.
        """
        client = await self._get_client()

        if self._backend == "tavily":
            key = self._tavily_pool.next_key()
            try:
                return await _tavily_search(key, query, num, gl)
            except Exception as e:
                logger.warning("[WebSearch] Tavily failed (%s), trying Serper fallback: %s", key[:8] + "...", e)
                if self._serper_key:
                    return await _serper_search(client, self._serper_key, query, num, gl, hl)
                raise

        # serper fallback
        return await _serper_search(client, self._serper_key, query, num, gl, hl)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
