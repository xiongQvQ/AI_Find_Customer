"""Baidu Qianfan web search tool — 百度千帆 AppBuilder AI Search API.

API endpoint: POST https://qianfan.baidubce.com/v2/ai_search/web_search
Auth header:  X-Appbuilder-Authorization: Bearer <API_KEY>

Returns web page references with title, url, content snippet, and date.
Used for domestic China (内贸) searches where Baidu indexes are more relevant
than Google for finding Chinese B2B companies and distributors.

Docs: https://ai.baidu.com/ai-doc/AppBuilder/pmaxd1hvy
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_BAIDU_SEARCH_URL = "https://qianfan.baidubce.com/v2/ai_search/web_search"
_DEFAULT_TOP_K = 10
_TIMEOUT_SECONDS = 15


class BaiduSearchTool:
    """Baidu Qianfan web search — wraps the AppBuilder AI Search API.

    Returns results in the same format as GoogleSearchTool so they can be
    merged seamlessly in SearchAgent:
        {"title": str, "link": str, "snippet": str, "position": int}

    Usage:
        tool = BaiduSearchTool(api_key="your_key")
        results = await tool.search("太阳能逆变器经销商 北京")
        await tool.close()
    """

    def __init__(self, api_key: str, *, top_k: int = _DEFAULT_TOP_K) -> None:
        self._api_key = api_key
        self._top_k = top_k
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=_TIMEOUT_SECONDS)
        return self._client

    async def search(self, query: str, *, top_k: int | None = None) -> list[dict[str, Any]]:
        """Search Baidu and return results in GoogleSearch-compatible format.

        Args:
            query: Search query string (Chinese or English).
            top_k: Number of results to request (overrides instance default).

        Returns:
            List of dicts with keys: title, link, snippet, position, source.
            Returns empty list on error (logged as warning).
        """
        if not query.strip():
            return []

        n = top_k if top_k is not None else self._top_k
        payload = {
            "messages": [{"content": query, "role": "user"}],
            "search_source": "baidu_search_v2",
            "resource_type_filter": [{"type": "web", "top_k": n}],
        }
        headers = {
            "X-Appbuilder-Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            client = self._get_client()
            resp = await client.post(_BAIDU_SEARCH_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(
                "[BaiduSearch] HTTP %d for query=%r: %s",
                e.response.status_code, query, e.response.text[:200],
            )
            return []
        except Exception as e:
            logger.warning("[BaiduSearch] Request failed for query=%r: %s", query, e)
            return []

        references = data.get("references", [])
        results: list[dict[str, Any]] = []

        for i, ref in enumerate(references):
            url = ref.get("url", "")
            title = ref.get("title", "") or ref.get("web_anchor", "")
            snippet = ref.get("content", "")
            if not url:
                continue
            results.append({
                "title": title,
                "link": url,
                "snippet": snippet,
                "position": i + 1,
                "source": "baidu",
            })

        logger.info("[BaiduSearch] query=%r → %d results", query, len(results))
        return results

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
