"""Tests for tools/jina_reader.py — mock HTTP, verify Markdown output."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from config.settings import Settings
from tools.jina_reader import JinaReaderTool

_FAKE_REQUEST = httpx.Request("GET", "https://fake")


def _make_settings(**overrides) -> Settings:
    defaults = {"jina_api_key": "jina-test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


class TestJinaReaderTool:
    @pytest.mark.asyncio
    async def test_read_returns_markdown(self):
        tool = JinaReaderTool(settings=_make_settings())
        markdown = "# Hello World\n\nThis is the main content."

        mock_resp = httpx.Response(200, text=markdown, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            result = await tool.read("https://example.com")

        assert result == markdown
        assert "# Hello World" in result
        await tool.close()

    @pytest.mark.asyncio
    async def test_read_sends_correct_url(self):
        tool = JinaReaderTool(settings=_make_settings())
        captured_url = {}

        async def mock_get(url, **kwargs):
            captured_url["url"] = url
            return httpx.Response(200, text="ok", request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.read("https://solar-company.com/products")

        assert captured_url["url"] == "https://r.jina.ai/https://solar-company.com/products"
        await tool.close()

    @pytest.mark.asyncio
    async def test_read_sends_auth_header(self):
        tool = JinaReaderTool(settings=_make_settings(jina_api_key="my-key"))
        captured_headers = {}

        async def mock_get(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, text="ok", request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.read("https://example.com")

        assert captured_headers["Authorization"] == "Bearer my-key"
        await tool.close()

    @pytest.mark.asyncio
    async def test_read_no_auth_when_key_empty(self):
        tool = JinaReaderTool(settings=_make_settings(jina_api_key=""))
        captured_headers = {}

        async def mock_get(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return httpx.Response(200, text="ok", request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.read("https://example.com")

        assert "Authorization" not in captured_headers
        await tool.close()

    @pytest.mark.asyncio
    async def test_read_http_error_raises(self):
        tool = JinaReaderTool(settings=_make_settings())
        mock_resp = httpx.Response(500, text="error", request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(httpx.HTTPStatusError):
                await tool.read("https://example.com")
        await tool.close()

    @pytest.mark.asyncio
    async def test_close(self):
        tool = JinaReaderTool(settings=_make_settings())
        mock_resp = httpx.Response(200, text="ok", request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            await tool.read("https://example.com")

        assert tool._client is not None
        await tool.close()
        assert tool._client is None
