"""Tests for tools/google_maps_search.py using direct Serper Maps requests."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from config.settings import Settings
from tools.google_maps_search import GoogleMapsSearchTool

_FAKE_REQUEST = httpx.Request("POST", "https://google.serper.dev/maps")


def _make_settings(**overrides) -> Settings:
    defaults = {"serper_api_key": "serper-test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


SERPER_MAPS_RESPONSE = {
    "places": [
        {
            "position": 1,
            "title": "SolarTech Berlin GmbH",
            "address": "Friedrichstr. 100, 10117 Berlin",
            "latitude": 52.5200,
            "longitude": 13.4050,
            "rating": 4.5,
            "ratingCount": 120,
            "type": "Solar energy company",
            "types": ["Solar energy company", "Energy supplier"],
            "website": "https://solartech-berlin.de",
            "phoneNumber": "+49 30 12345678",
            "description": "Leading solar panel distributor in Berlin.",
            "cid": "12345678901234567890",
            "placeId": "ChIJ_test_place_id_1",
        }
    ]
}


class TestGoogleMapsSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_places(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json=SERPER_MAPS_RESPONSE, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("solar panel distributor Berlin")

        assert len(results) == 1
        assert results[0]["title"] == "SolarTech Berlin GmbH"
        assert results[0]["website"] == "https://solartech-berlin.de"
        assert results[0]["place_id"] == "ChIJ_test_place_id_1"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_correct_body(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        captured_body = {}

        async def mock_post(url, **kwargs):
            captured_body.update(kwargs.get("json", {}))
            return httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test query", num=20, gl="de", hl="de", ll="@52.5200,13.4050,14z")

        assert captured_body["q"] == "test query"
        assert captured_body["num"] == 20
        assert captured_body["gl"] == "de"
        assert captured_body["hl"] == "de"
        assert captured_body["ll"] == "@52.5200,13.4050,14z"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_api_key_header(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        captured_headers = {}

        async def mock_post(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test")

        assert captured_headers["X-API-KEY"] == "serper-test-key"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_raises_when_key_missing(self):
        tool = GoogleMapsSearchTool(settings=_make_settings(serper_api_key=""))
        with pytest.raises(RuntimeError, match="SERPER_API_KEY"):
            await tool.search("test")
        await tool.close()
