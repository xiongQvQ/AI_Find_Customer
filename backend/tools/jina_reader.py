"""Jina Reader tool backed directly by the public r.jina.ai endpoint."""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from tenacity import before_sleep_log, retry, retry_if_exception, stop_after_attempt, wait_exponential

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def _is_retryable_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    if isinstance(exc, (httpx.RequestError, httpx.TimeoutException)):
        return True
    return False


class JinaReaderTool:
    """Fetch clean Markdown from r.jina.ai for a target URL."""

    JINA_BASE = "https://r.jina.ai/"

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
        """Read a URL through the Jina Reader service."""
        headers = {"Accept": "text/markdown"}
        if self._settings.jina_api_key:
            headers["Authorization"] = f"Bearer {self._settings.jina_api_key}"

        client = await self._get_client()
        resp = await client.get(f"{self.JINA_BASE}{url}", headers=headers)
        resp.raise_for_status()
        return resp.text

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
