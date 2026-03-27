"""Google Maps Search tool backed directly by the Serper Maps API."""

from __future__ import annotations

from typing import Optional

import httpx

from config.settings import Settings, get_settings


class GoogleMapsSearchTool:
    """Search Google Maps through Serper and return normalized place results."""

    SERPER_MAPS_URL = "https://google.serper.dev/maps"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

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
        ll: str = "",
    ) -> list[dict]:
        """Execute a Google Maps search via Serper."""
        if not self._settings.serper_api_key:
            raise RuntimeError("SERPER_API_KEY is required for Google Maps search.")

        body: dict[str, object] = {"q": query, "num": num}
        if gl:
            body["gl"] = gl
        if hl:
            body["hl"] = hl
        if ll:
            body["ll"] = ll

        client = await self._get_client()
        resp = await client.post(
            self.SERPER_MAPS_URL,
            headers={
                "X-API-KEY": self._settings.serper_api_key,
                "Content-Type": "application/json",
            },
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        places = data.get("places") or data.get("data", {}).get("places", [])
        results = []
        for item in places:
            results.append(
                {
                    "title": item.get("title", ""),
                    "address": item.get("address", ""),
                    "website": item.get("website", ""),
                    "phone_number": item.get("phoneNumber", ""),
                    "rating": item.get("rating", 0),
                    "rating_count": item.get("ratingCount", 0),
                    "type": item.get("type", ""),
                    "types": item.get("types", []),
                    "description": item.get("description", ""),
                    "email": item.get("email", ""),
                    "latitude": item.get("latitude", 0),
                    "longitude": item.get("longitude", 0),
                    "cid": item.get("cid", ""),
                    "place_id": item.get("placeId", ""),
                }
            )
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
