"""Tests for tools/google_maps_search.py — mock Serper Maps API, verify result parsing."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from config.settings import Settings
from tools.google_maps_search import GoogleMapsSearchTool

_FAKE_REQUEST = httpx.Request("POST", "https://fake")


def _make_settings(**overrides) -> Settings:
    defaults = {"serper_api_key": "serper-test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


SERPER_MAPS_RESPONSE = {
    "ll": "@52.5200,13.4050,14z",
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
        },
        {
            "position": 2,
            "title": "GreenPower Solutions",
            "address": "Alexanderplatz 5, 10178 Berlin",
            "latitude": 52.5219,
            "longitude": 13.4132,
            "rating": 4.2,
            "ratingCount": 85,
            "type": "Energy supplier",
            "types": ["Energy supplier"],
            "website": "https://greenpower.de",
            "phoneNumber": "+49 30 87654321",
            "cid": "09876543210987654321",
            "placeId": "ChIJ_test_place_id_2",
        },
        {
            "position": 3,
            "title": "PV Panels Direct",
            "address": "Kurfürstendamm 200, 10719 Berlin",
            "latitude": 52.5035,
            "longitude": 13.3320,
            "rating": 3.8,
            "ratingCount": 42,
            "type": "Solar energy company",
            "website": "https://pvpanels.de",
            "phoneNumber": "+49 30 11223344",
            "cid": "11223344556677889900",
            "placeId": "ChIJ_test_place_id_3",
        },
    ],
}


class TestGoogleMapsSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_places(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json=SERPER_MAPS_RESPONSE, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("solar panel distributor Berlin")

        assert len(results) == 3
        assert results[0]["title"] == "SolarTech Berlin GmbH"
        assert results[0]["address"] == "Friedrichstr. 100, 10117 Berlin"
        assert results[0]["website"] == "https://solartech-berlin.de"
        assert results[0]["phone_number"] == "+49 30 12345678"
        assert results[0]["rating"] == 4.5
        assert results[0]["rating_count"] == 120
        assert results[0]["type"] == "Solar energy company"
        assert results[0]["latitude"] == 52.5200
        assert results[0]["longitude"] == 13.4050
        assert results[0]["cid"] == "12345678901234567890"
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
            await tool.search("test query", num=20, gl="de", hl="de")

        assert captured_body["q"] == "test query"
        assert captured_body["num"] == 20
        assert captured_body["gl"] == "de"
        assert captured_body["hl"] == "de"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_ll_param(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        captured_body = {}

        async def mock_post(url, **kwargs):
            captured_body.update(kwargs.get("json", {}))
            return httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test", ll="@52.5200,13.4050,14z")

        assert captured_body["ll"] == "@52.5200,13.4050,14z"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_api_key_header(self):
        tool = GoogleMapsSearchTool(settings=_make_settings(serper_api_key="my-serper-key"))
        captured_headers = {}

        async def mock_post(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test")

        assert captured_headers["X-API-KEY"] == "my-serper-key"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_posts_to_maps_endpoint(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        captured_url = None

        async def mock_post(url, **kwargs):
            nonlocal captured_url
            captured_url = url
            return httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test")

        assert captured_url == "https://google.serper.dev/maps"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("very obscure query")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_missing_places_key(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json={"searchParameters": {}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("test")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_no_optional_params(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        captured_body = {}

        async def mock_post(url, **kwargs):
            captured_body.update(kwargs.get("json", {}))
            return httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test")

        assert "gl" not in captured_body
        assert "hl" not in captured_body
        assert "ll" not in captured_body
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_http_error_raises(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(403, json={"error": "forbidden"}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(httpx.HTTPStatusError):
                await tool.search("test")
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_handles_missing_fields(self):
        """Places with missing optional fields should get defaults."""
        tool = GoogleMapsSearchTool(settings=_make_settings())
        sparse_response = {
            "places": [
                {"title": "Minimal Place", "position": 1},
            ]
        }
        mock_resp = httpx.Response(200, json=sparse_response, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("test")

        assert len(results) == 1
        assert results[0]["title"] == "Minimal Place"
        assert results[0]["address"] == ""
        assert results[0]["website"] == ""
        assert results[0]["phone_number"] == ""
        assert results[0]["rating"] == 0
        assert results[0]["rating_count"] == 0
        assert results[0]["type"] == ""
        assert results[0]["latitude"] == 0
        assert results[0]["longitude"] == 0
        await tool.close()

    @pytest.mark.asyncio
    async def test_close(self):
        tool = GoogleMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json={"places": []}, request=_FAKE_REQUEST)
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            await tool.search("test")

        assert tool._client is not None
        await tool.close()
        assert tool._client is None
