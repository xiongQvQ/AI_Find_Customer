"""Google Maps Search tool backed by the Scavio API (https://scavio.dev).

Optional: used only when MAPS_SEARCH_PROVIDER=scavio. Returns the same place rows
as GoogleMapsSearchTool, so the search agent treats both the same way.
"""

from __future__ import annotations

from typing import Optional

import httpx

from config.settings import Settings, get_settings

# A country-wide map view per gl code the search agent sends. Scavio places a Maps
# search by map position, and with gl alone it centres on one major city of that
# country, which outranks a city named in the keyword ("distributor Munich" with
# gl=de comes back mostly from Berlin). A country-wide view keeps a keyword with a
# city in that city and a keyword without one inside the country.
COUNTRY_VIEWS: dict[str, str] = {
    "ae": "@24.0000,54.0000,7z",
    "at": "@47.6000,14.1000,7z",
    "au": "@-25.3000,133.8000,4z",
    "be": "@50.6000,4.6000,8z",
    "br": "@-14.2000,-51.9000,4z",
    "ca": "@56.1000,-106.3000,4z",
    "ch": "@46.8000,8.2000,8z",
    "cn": "@35.9000,104.2000,4z",
    "cz": "@49.8000,15.5000,7z",
    "de": "@51.1657,10.4515,6z",
    "dk": "@56.0000,10.0000,7z",
    "es": "@40.4000,-3.7000,6z",
    "fi": "@64.0000,26.0000,5z",
    "fr": "@46.6000,2.2000,6z",
    "gb": "@54.0000,-2.5000,6z",
    "gr": "@39.1000,22.0000,6z",
    "hu": "@47.2000,19.5000,7z",
    "id": "@-2.5000,118.0000,4z",
    "in": "@22.0000,79.0000,5z",
    "it": "@42.5000,12.6000,6z",
    "jp": "@36.2000,138.3000,5z",
    "kr": "@36.5000,127.9000,7z",
    "mx": "@23.6000,-102.6000,5z",
    "my": "@4.2000,102.0000,6z",
    "nl": "@52.1000,5.3000,8z",
    "no": "@64.5000,11.5000,5z",
    "nz": "@-41.0000,174.0000,5z",
    "ph": "@12.9000,121.8000,6z",
    "pl": "@51.9000,19.1000,6z",
    "pt": "@39.6000,-8.0000,7z",
    "ro": "@45.9000,25.0000,7z",
    "ru": "@61.5000,105.3000,3z",
    "sa": "@23.9000,45.1000,5z",
    "se": "@62.0000,15.0000,5z",
    "sg": "@1.3500,103.8200,11z",
    "th": "@15.9000,101.0000,6z",
    "tr": "@39.0000,35.2000,6z",
    "ua": "@48.4000,31.2000,6z",
    "us": "@39.8283,-98.5795,4z",
    "vn": "@16.0000,107.8000,5z",
    "za": "@-29.0000,24.7000,5z",
}

# The search agent uses "uk"; Google's country code is "gb".
_GL_ALIASES = {"uk": "gb"}


class ScavioMapsSearchTool:
    """Search Google Maps through the Scavio API and return normalized place rows."""

    SCAVIO_MAPS_URL = "https://api.scavio.dev/api/v2/google/maps/search"
    # A Maps search takes 20-40 seconds upstream.
    TIMEOUT_SECONDS = 90.0
    # One request returns up to 20 places (1 credit). There is no second request.
    MAX_RESULTS = 20

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS)
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
        """Execute a Google Maps search via Scavio. One call, no retries (calls are billed)."""
        if not self._settings.scavio_api_key:
            raise RuntimeError("SCAVIO_API_KEY is required when MAPS_SEARCH_PROVIDER=scavio.")

        country = _GL_ALIASES.get(gl.lower(), gl.lower())
        body: dict[str, object] = {"query": query}
        if hl:
            body["hl"] = hl
        view = ll or COUNTRY_VIEWS.get(country, "")
        if view:
            body["ll"] = view
            if country:
                body["gl"] = country
        # A gl without a known view is not sent: alone it would centre the search on
        # one major city of that country.

        client = await self._get_client()
        resp = await client.post(
            self.SCAVIO_MAPS_URL,
            headers={
                "Authorization": f"Bearer {self._settings.scavio_api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        if resp.status_code == 401:
            raise RuntimeError("Scavio rejected SCAVIO_API_KEY (HTTP 401).")
        if resp.status_code == 402:
            raise RuntimeError("Scavio account is out of credits (HTTP 402).")
        resp.raise_for_status()
        data = resp.json()

        places = data.get("local_results")
        if not isinstance(places, list):
            raise RuntimeError("Scavio Maps response has no local_results list.")

        results = []
        for item in places[: max(0, min(num, self.MAX_RESULTS))]:
            coords = item.get("gps_coordinates") or {}
            types = item.get("types") or []
            results.append(
                {
                    "title": item.get("title", ""),
                    "address": item.get("address", ""),
                    "website": item.get("website", ""),
                    "phone_number": item.get("phone", ""),
                    "rating": item.get("rating", 0),
                    "rating_count": item.get("reviews", 0),
                    "type": item.get("type", ""),
                    "types": types,
                    "description": item.get("description", ""),
                    "email": "",
                    "latitude": coords.get("latitude", 0),
                    "longitude": coords.get("longitude", 0),
                    "cid": item.get("data_cid", ""),
                    "place_id": item.get("place_id", ""),
                }
            )
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
