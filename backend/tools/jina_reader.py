"""Jina Reader tool — scrape web pages and convert to clean Markdown."""

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


class JinaReaderTool:
    """Fetch a URL via Jina Reader API and return clean Markdown content.

    Jina Reader (r.jina.ai) strips ads, navigation, and boilerplate,
    returning only the main content as Markdown — ideal for LLM consumption.
    """

    JINA_BASE_URL = "https://r.jina.ai/"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    @retry(
        retry=retry_if_exception(_is_retryable_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def read(self, url: str) -> str:
        """Scrape a URL and return Markdown content.

        Args:
            url: The target URL to scrape.

        Returns:
            Markdown string of the page's main content.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        client = await self._get_client()
        headers = {
            "Accept": "text/markdown",
        }
        if self._settings.jina_api_key:
            headers["Authorization"] = f"Bearer {self._settings.jina_api_key}"

        resp = await client.get(
            f"{self.JINA_BASE_URL}{url}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.text

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
