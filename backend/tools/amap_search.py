"""Amap (高德地图) POI search tool — search Chinese businesses via Amap Web API.

Uses the Amap POI 2.0 keyword search endpoint:
https://restapi.amap.com/v5/place/text

Returns structured place results including company name, address, location,
phone number, and business info — ideal for finding B2B companies in China.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class AmapSearchTool:
    """Search Amap (高德地图) POI via Web API and return structured place results.

    Each result contains: name, address, location (lng,lat), phone,
    type, city, province, district, website, business_area.
    """

    AMAP_URL = "https://restapi.amap.com/v5/place/text"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search(
        self,
        keywords: str,
        *,
        region: str = "",
        city_limit: bool = False,
        types: str = "",
        page_size: int = 25,
        page_num: int = 1,
        show_fields: str = "business",
    ) -> list[dict]:
        """Execute an Amap POI keyword search.

        Args:
            keywords: Search text (company name, address, or keyword).
            region: City or region name to focus search (e.g. "北京市", "上海").
            city_limit: If True, strictly limit results to the region.
            types: POI type codes separated by "|" (see Amap POI typecode table).
            page_size: Results per page (1-25).
            page_num: Page number.
            show_fields: Extra fields to return. "business" includes tel, rating, etc.

        Returns:
            List of place dicts with keys: name, id, address, location,
            phone, type, typecode, province, city, district, business_area.
        """
        api_key = self._settings.amap_api_key
        if not api_key:
            logger.warning("[AmapSearch] No amap_api_key configured, skipping search")
            return []

        client = await self._get_client()

        params: dict = {
            "key": api_key,
            "keywords": keywords,
            "page_size": str(page_size),
            "page_num": str(page_num),
            "show_fields": show_fields,
        }
        if region:
            params["region"] = region
        if city_limit:
            params["city_limit"] = "true"
        if types:
            params["types"] = types

        logger.info("[AmapSearch] query=%r region=%s city_limit=%s",
                    keywords, region or "(all)", city_limit)

        resp = await client.get(self.AMAP_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "1":
            logger.warning("[AmapSearch] API error: info=%s infocode=%s",
                           data.get("info"), data.get("infocode"))
            return []

        results = []
        for poi in data.get("pois", []):
            # Extract phone from business info
            business = poi.get("business", {}) or {}
            phone = business.get("tel", "") or ""

            # Parse location "lng,lat"
            location = poi.get("location", "")
            lng, lat = 0.0, 0.0
            if location and "," in location:
                parts = location.split(",")
                try:
                    lng, lat = float(parts[0]), float(parts[1])
                except (ValueError, IndexError):
                    pass

            results.append({
                "name": poi.get("name", ""),
                "id": poi.get("id", ""),
                "address": poi.get("address", ""),
                "location": location,
                "longitude": lng,
                "latitude": lat,
                "phone": phone,
                "type": poi.get("type", ""),
                "typecode": poi.get("typecode", ""),
                "province": poi.get("pname", ""),
                "city": poi.get("cityname", ""),
                "district": poi.get("adname", ""),
                "business_area": business.get("business_area", ""),
                "rating": business.get("rating", ""),
            })

        logger.info("[AmapSearch] query=%r → %d POIs found", keywords, len(results))
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
