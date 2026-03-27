"""Tests for tools/brave_search.py — mock Brave API, verify result parsing."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from tools.brave_search import BraveSearchTool

_FAKE_REQUEST = httpx.Request("GET", "https://fake")
_DEFAULT_KEY = "brave-test-key"


BRAVE_RESPONSE = {
    "web": {
        "results": [
            {
                "title": "SolarTech GmbH",
                "url": "https://solartech.de",
                "description": "Leading solar inverter manufacturer",
            },
            {
                "title": "PV Distributor",
                "url": "https://pvdist.com",
                "description": "PV panels and accessories",
            },
            {
                "title": "Green Energy Co",
                "url": "https://greenenergy.fr",
                "description": "Renewable energy solutions",
            },
        ]
    }
}


class TestBraveSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        tool = BraveSearchTool(api_key=_DEFAULT_KEY)
        mock_resp = httpx.Response(200, json=BRAVE_RESPONSE, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("solar inverter distributor")

        assert len(results) == 3
        assert results[0]["title"] == "SolarTech GmbH"
        assert results[0]["link"] == "https://solartech.de"
        assert results[0]["snippet"] == "Leading solar inverter manufacturer"
        assert results[0]["position"] == 1
        assert results[2]["position"] == 3
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_correct_params(self):
        tool = BraveSearchTool(api_key=_DEFAULT_KEY)
        captured_params = {}

        async def mock_get(url, **kwargs):
            captured_params.update(kwargs.get("params", {}))
            return httpx.Response(200, json={"web": {"results": []}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.search("test query", num=15, gl="de", hl="de")

        assert captured_params["q"] == "test query"
        assert captured_params["count"] == 15
        assert captured_params["country"] == "de"
        assert captured_params["search_lang"] == "de"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_api_key_header(self):
        tool = BraveSearchTool(api_key="my-brave-key")
        captured_headers = {}

        async def mock_get(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, json={"web": {"results": []}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.search("test")

        assert captured_headers["X-Subscription-Token"] == "my-brave-key"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        tool = BraveSearchTool(api_key=_DEFAULT_KEY)
        mock_resp = httpx.Response(200, json={"web": {"results": []}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("very obscure query")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_missing_web_key(self):
        tool = BraveSearchTool(api_key=_DEFAULT_KEY)
        mock_resp = httpx.Response(200, json={"query": {}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("test")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_caps_count_at_20(self):
        tool = BraveSearchTool(api_key=_DEFAULT_KEY)
        captured_params = {}

        async def mock_get(url, **kwargs):
            captured_params.update(kwargs.get("params", {}))
            return httpx.Response(200, json={"web": {"results": []}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.search("test", num=50)

        assert captured_params["count"] == 20
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_no_optional_params(self):
        tool = BraveSearchTool(api_key=_DEFAULT_KEY)
        captured_params = {}

        async def mock_get(url, **kwargs):
            captured_params.update(kwargs.get("params", {}))
            return httpx.Response(200, json={"web": {"results": []}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.search("test")

        assert "country" not in captured_params
        assert "search_lang" not in captured_params
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_http_error_raises(self):
        tool = BraveSearchTool(api_key=_DEFAULT_KEY)
        mock_resp = httpx.Response(429, json={"error": "rate limit"}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(httpx.HTTPStatusError):
                await tool.search("test")
        await tool.close()
