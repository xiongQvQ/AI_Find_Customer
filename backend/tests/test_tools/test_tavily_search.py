"""Tests for tools/tavily_search.py — mock TavilyClient, verify result parsing."""

from unittest.mock import patch, MagicMock

import pytest

from config.settings import Settings
from tools.tavily_search import TavilySearchTool


def _make_settings(**overrides) -> Settings:
    defaults = {"tavily_api_key": "tvly-test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


TAVILY_RESPONSE = {
    "query": "solar inverter",
    "results": [
        {
            "url": "https://solartech.de",
            "title": "SolarTech GmbH",
            "content": "Leading solar inverter manufacturer in Europe with 20 years experience.",
            "score": 0.99,
        },
        {
            "url": "https://pvdist.com",
            "title": "PV Distributor",
            "content": "PV panels and accessories for wholesale.",
            "score": 0.95,
        },
    ],
    "response_time": 1.1,
}


class TestTavilySearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        tool = TavilySearchTool(settings=_make_settings())

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value=TAVILY_RESPONSE)

        with patch("tools.tavily_search.TavilySearchTool._get_client", return_value=mock_client):
            results = await tool.search("solar inverter")

        assert len(results) == 2
        assert results[0]["title"] == "SolarTech GmbH"
        assert results[0]["link"] == "https://solartech.de"
        assert "Leading solar" in results[0]["snippet"]
        assert results[0]["position"] == 1
        assert results[1]["position"] == 2
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_truncates_long_content(self):
        tool = TavilySearchTool(settings=_make_settings())

        long_content = "A" * 500
        response = {
            "results": [{
                "url": "https://example.com",
                "title": "Example",
                "content": long_content,
                "score": 0.9,
            }],
        }
        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value=response)

        with patch("tools.tavily_search.TavilySearchTool._get_client", return_value=mock_client):
            results = await tool.search("test")

        assert len(results[0]["snippet"]) == 303  # 300 + "..."
        assert results[0]["snippet"].endswith("...")
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        tool = TavilySearchTool(settings=_make_settings())

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value={"results": []})

        with patch("tools.tavily_search.TavilySearchTool._get_client", return_value=mock_client):
            results = await tool.search("obscure query")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_passes_max_results(self):
        tool = TavilySearchTool(settings=_make_settings())

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value={"results": []})

        with patch("tools.tavily_search.TavilySearchTool._get_client", return_value=mock_client):
            await tool.search("test", num=15)

        call_kwargs = mock_client.search.call_args
        assert call_kwargs.kwargs["max_results"] == 15

    @pytest.mark.asyncio
    async def test_search_caps_at_20(self):
        tool = TavilySearchTool(settings=_make_settings())

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value={"results": []})

        with patch("tools.tavily_search.TavilySearchTool._get_client", return_value=mock_client):
            await tool.search("test", num=50)

        call_kwargs = mock_client.search.call_args
        assert call_kwargs.kwargs["max_results"] == 20

    @pytest.mark.asyncio
    async def test_search_with_gl_appends_site(self):
        """gl param should be appended as site: hint to the query."""
        tool = TavilySearchTool(settings=_make_settings())

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value={"results": []})

        with patch("tools.tavily_search.TavilySearchTool._get_client", return_value=mock_client):
            await tool.search("solar panels", gl="de")

        call_kwargs = mock_client.search.call_args
        assert "site:.de" in call_kwargs.kwargs["query"]

    @pytest.mark.asyncio
    async def test_close_clears_client(self):
        tool = TavilySearchTool(settings=_make_settings())
        tool._client = MagicMock()
        await tool.close()
        assert tool._client is None

    @pytest.mark.asyncio
    async def test_missing_tavily_package_raises(self):
        """When tavily package is not installed, _get_client should raise ImportError."""
        tool = TavilySearchTool(settings=_make_settings())
        with patch.dict("sys.modules", {"tavily": None}):
            with pytest.raises(ImportError, match="tavily-python"):
                tool._get_client()
