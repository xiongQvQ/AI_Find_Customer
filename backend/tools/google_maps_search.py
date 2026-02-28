"""Google Maps Search tool — search Google Maps via Serper API."""

from __future__ import annotations

from typing import Optional

import httpx

from config.settings import Settings, get_settings


class GoogleMapsSearchTool:
    """Search Google Maps via Serper API and return structured place results.

    Each result contains: title, address, website, phoneNumber, rating,
    ratingCount, type, latitude, longitude, cid, placeId.
    """

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
        """Execute a Google Maps search via Serper API.

        Args:
            query: Search query string (e.g. "solar panel distributor Berlin").
            num: Number of results to return (max 20).
            gl: Country code for geolocation (e.g. "us", "de").
            hl: Language code (e.g. "en", "de").
            ll: Latitude/longitude with zoom (e.g. "@40.7128,-74.0060,14z").

        Returns:
            List of place dicts with keys: title, address, website,
            phone_number, rating, rating_count, type, latitude, longitude,
            cid, place_id.
        """
        client = await self._get_client()

        body: dict = {"q": query, "num": num}
        if gl:
            body["gl"] = gl
        if hl:
            body["hl"] = hl
        if ll:
            body["ll"] = ll

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

        results = []
        for item in data.get("places", []):
            results.append({
                "title": item.get("title", ""),
                "address": item.get("address", ""),
                "website": item.get("website", ""),
                "phone_number": item.get("phoneNumber", ""),
                "rating": item.get("rating", 0),
                "rating_count": item.get("ratingCount", 0),
                "type": item.get("type", ""),
                "latitude": item.get("latitude", 0),
                "longitude": item.get("longitude", 0),
                "cid": item.get("cid", ""),
                "place_id": item.get("placeId", ""),
            })
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
