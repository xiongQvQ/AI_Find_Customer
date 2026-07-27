"""You.com Search tool — web search via You.com Search API."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import requests

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

YOUCOM_SEARCH_URL = "https://ydc-index.io/v1/search"


class YoucomSearchTool:
    """Search the web via You.com Search API and return structured results.

    Each result contains: title, link, snippet, position.

    Uses native HTTP POST via requests (no extra SDK needed).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        """Lazy-initialize a requests session."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _get_api_key(self) -> str:
        """Return the You.com API key from settings."""
        return self._settings.youcom_api_key

    async def search(
        self,
        query: str,
        *,
        num: int = 10,
        gl: str = "",
        hl: str = "",
    ) -> list[dict]:
        """Execute a web search via You.com Search API.

        Args:
            query: Search query string.
            num: Number of results to return (max 20).
            gl: Country code — appended as site:.{gl} hint to query.
            hl: Language code — not used directly, ignored.

        Returns:
            List of result dicts with keys: title, link, snippet, position.
        """
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("YOUCOM_API_KEY is not configured")

        # You.com doesn't have native geo params — append as site hint like Tavily does
        effective_query = query
        if gl and len(gl) == 2:
            effective_query = f"{query} site:.{gl}"

        def _sync_search() -> dict:
            session = self._get_session()
            headers = {
                "Accept": "application/json",
                "X-API-Key": api_key,
            }
            payload = {"query": effective_query, "count": min(num, 20)}
            resp = session.post(
                YOUCOM_SEARCH_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )
            if resp.status_code == 429:
                raise RuntimeError("You.com Search rate limit exceeded (429)")
            if resp.status_code == 401:
                raise RuntimeError("You.com API Key is invalid or expired")
            if resp.status_code == 403:
                raise RuntimeError("You.com API Key has insufficient permissions")
            if resp.status_code != 200:
                raise RuntimeError(f"You.com Search request failed (Status {resp.status_code})")
            return resp.json()

        response = await asyncio.to_thread(_sync_search)

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

    async def close(self) -> None:
        """Close the requests session."""
        if self._session:
            self._session.close()
            self._session = None
