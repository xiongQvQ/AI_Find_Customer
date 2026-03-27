"""Google Search tool backed directly by the Serper API."""

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


class GoogleSearchTool:
    """Search Google through Serper and return normalized organic results."""

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
        """Execute a Google search via Serper."""
        if not self._settings.serper_api_key:
            raise RuntimeError("SERPER_API_KEY is required for Google search.")

        body: dict[str, object] = {"q": query, "num": num}
        if gl:
            body["gl"] = gl
        if hl:
            body["hl"] = hl

        client = await self._get_client()
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
            results.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", 0),
                }
            )
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
