"""Google Search tool — search via Serper API."""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def _is_retryable_error(e: BaseException) -> bool:
    """Check if the exception is retryable (5xx, 429, or network error)."""
    if isinstance(e, httpx.HTTPStatusError):
        return e.response.status_code == 429 or e.response.status_code >= 500
    if isinstance(e, (httpx.RequestError, httpx.TimeoutException)):
        return True
    return False


class GoogleSearchTool:
    """Search Google via Serper API and return structured results.

    Each result contains: title, link, snippet, position.
    """

    SERPER_URL = "https://google.serper.dev/search"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @retry(
        retry=retry_if_exception(_is_retryable_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def search(
        self,
        query: str,
        *,
        num: int = 10,
        gl: str = "",
        hl: str = "",
    ) -> list[dict]:
        """Execute a Google search via Serper API.

        Args:
            query: Search query string.
            num: Number of results to return (max 100).
            gl: Country code for geolocation (e.g. "us", "de").
            hl: Language code (e.g. "en", "de").

        Returns:
            List of result dicts with keys: title, link, snippet, position.
        """
        client = await self._get_client()

        body: dict = {"q": query, "num": num}
        if gl:
            body["gl"] = gl
        if hl:
            body["hl"] = hl

        resp = await client.post(
            self.SERPER_URL,
            headers={
                "X-API-KEY": self._settings.serper_api_key,
                "Content-Type": "application/json",
            },
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

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
