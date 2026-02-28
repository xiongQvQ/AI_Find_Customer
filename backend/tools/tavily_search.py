"""Tavily Search tool — web search via Tavily API (tavily-python SDK)."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class TavilySearchTool:
    """Search the web via Tavily API and return structured results.

    Each result contains: title, link, snippet, position.
    Free tier: 1,000 queries/month.

    Uses the tavily-python SDK. Since TavilyClient.search() is synchronous,
    we wrap it with asyncio.to_thread() to avoid blocking the event loop.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None  # Lazy-init TavilyClient

    def _get_client(self):
        """Lazy-initialize the Tavily client."""
        if self._client is None:
            try:
                from tavily import TavilyClient
            except ImportError:
                raise ImportError(
                    "tavily-python is required for TavilySearchTool. "
                    "Install it with: pip install tavily-python"
                )
            self._client = TavilyClient(self._settings.tavily_api_key)
        return self._client

    async def search(
        self,
        query: str,
        *,
        num: int = 10,
        gl: str = "",
        hl: str = "",
    ) -> list[dict]:
        """Execute a web search via Tavily API.

        Args:
            query: Search query string.
            num: Number of results to return (max 20).
            gl: Country code — appended to query as region hint (Tavily has
                no native country param).
            hl: Language code — not used directly by Tavily, ignored.

        Returns:
            List of result dicts with keys: title, link, snippet, position.
        """
        client = self._get_client()

        # Tavily doesn't have native geo params. If gl is specified,
        # append it as a region hint to the query for better targeting.
        effective_query = query
        if gl:
            effective_query = f"{query} site:.{gl}" if len(gl) == 2 else query

        def _sync_search():
            return client.search(
                query=effective_query,
                search_depth="basic",
                max_results=min(num, 20),
            )

        response = await asyncio.to_thread(_sync_search)

        results = []
        for i, item in enumerate(response.get("results", []), start=1):
            content = item.get("content", "")
            # Truncate long content snippets
            snippet = content[:300] + "..." if len(content) > 300 else content
            results.append({
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": snippet,
                "position": i,
            })
        return results

    async def close(self) -> None:
        """No-op — TavilyClient has no close method."""
        self._client = None
