"""Tests for tools/google_search.py — mock Serper API, verify result parsing."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from config.settings import Settings
from tools.google_search import GoogleSearchTool

_FAKE_REQUEST = httpx.Request("POST", "https://fake")


def _make_settings(**overrides) -> Settings:
    defaults = {"serper_api_key": "serper-test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


SERPER_RESPONSE = {
    "organic": [
        {"title": "SolarTech GmbH", "link": "https://solartech.de", "snippet": "Leading solar...", "position": 1},
        {"title": "PV Distributor", "link": "https://pvdist.com", "snippet": "PV panels...", "position": 2},
        {"title": "Green Energy Co", "link": "https://greenenergy.fr", "snippet": "Renewable...", "position": 3},
    ]
}


class TestGoogleSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        tool = GoogleSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json=SERPER_RESPONSE, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("solar inverter distributor")

        assert len(results) == 3
        assert results[0]["title"] == "SolarTech GmbH"
        assert results[0]["link"] == "https://solartech.de"
        assert results[0]["snippet"] == "Leading solar..."
        assert results[0]["position"] == 1
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_correct_body(self):
        tool = GoogleSearchTool(settings=_make_settings())
        captured_body = {}

        async def mock_post(url, **kwargs):
            captured_body.update(kwargs.get("json", {}))
            return httpx.Response(200, json={"organic": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test query", num=20, gl="de", hl="de")

        assert captured_body["q"] == "test query"
        assert captured_body["num"] == 20
        assert captured_body["gl"] == "de"
        assert captured_body["hl"] == "de"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_api_key_header(self):
        tool = GoogleSearchTool(settings=_make_settings(serper_api_key="my-serper-key"))
        captured_headers = {}

        async def mock_post(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, json={"organic": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test")

        assert captured_headers["X-API-KEY"] == "my-serper-key"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        tool = GoogleSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json={"organic": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("very obscure query")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_missing_organic_key(self):
        tool = GoogleSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json={"searchParameters": {}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("test")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_no_optional_params(self):
        tool = GoogleSearchTool(settings=_make_settings())
        captured_body = {}

        async def mock_post(url, **kwargs):
            captured_body.update(kwargs.get("json", {}))
            return httpx.Response(200, json={"organic": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
            await tool.search("test")

        assert "gl" not in captured_body
        assert "hl" not in captured_body
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_http_error_raises(self):
        tool = GoogleSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(403, json={"error": "forbidden"}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(httpx.HTTPStatusError):
                await tool.search("test")
        await tool.close()
