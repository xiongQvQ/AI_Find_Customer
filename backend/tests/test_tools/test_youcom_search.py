"""Tests for tools/youcom_search.py — mock requests, verify result parsing."""

from unittest.mock import patch, MagicMock

import pytest

from config.settings import Settings
from tools.youcom_search import YoucomSearchTool


def _make_settings(**overrides) -> Settings:
    defaults = {"youcom_api_key": "ydc-test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


YOUCOM_RESPONSE = {
    "results": [
        {
            "title": "SolarTech GmbH",
            "url": "https://solartech.de",
            "snippets": ["Leading solar inverter manufacturer in Europe with 20 years experience."],
        },
        {
            "title": "PV Distributor",
            "url": "https://pvdist.com",
            "snippets": ["PV panels and accessories for wholesale."],
        },
    ],
}


class TestYoucomSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        tool = YoucomSearchTool(settings=_make_settings())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = YOUCOM_RESPONSE

        with patch("tools.youcom_search.YoucomSearchTool._get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_resp
            mock_get_session.return_value = mock_session
            results = await tool.search("solar inverter")

        assert len(results) == 2
        assert results[0]["title"] == "SolarTech GmbH"
        assert results[0]["link"] == "https://solartech.de"
        assert "Leading solar" in results[0]["snippet"]
        assert results[0]["position"] == 1
        assert results[1]["position"] == 2
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_truncates_long_snippet(self):
        tool = YoucomSearchTool(settings=_make_settings())

        long_snippet = "A" * 500
        response = {
            "results": [{
                "title": "Example",
                "url": "https://example.com",
                "snippets": [long_snippet],
            }],
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response

        with patch("tools.youcom_search.YoucomSearchTool._get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_resp
            mock_get_session.return_value = mock_session
            results = await tool.search("test")

        assert len(results[0]["snippet"]) == 303  # 300 + "..."
        assert results[0]["snippet"].endswith("...")
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        tool = YoucomSearchTool(settings=_make_settings())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}

        with patch("tools.youcom_search.YoucomSearchTool._get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_resp
            mock_get_session.return_value = mock_session
            results = await tool.search("obscure query")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_caps_at_20(self):
        tool = YoucomSearchTool(settings=_make_settings())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}

        with patch("tools.youcom_search.YoucomSearchTool._get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_resp
            mock_get_session.return_value = mock_session
            await tool.search("test", num=50)

            call_payload = mock_session.post.call_args
            assert call_payload.kwargs["json"]["count"] == 20
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_with_gl_appends_site_hint(self):
        tool = YoucomSearchTool(settings=_make_settings())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}

        with patch("tools.youcom_search.YoucomSearchTool._get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_resp
            mock_get_session.return_value = mock_session
            await tool.search("solar panels", gl="de")

            call_payload = mock_session.post.call_args
            assert "site:." in call_payload.kwargs["json"]["query"]
        await tool.close()

    @pytest.mark.asyncio
    async def test_missing_api_key_raises(self):
        tool = YoucomSearchTool(settings=_make_settings(youcom_api_key=""))

        with pytest.raises(ValueError, match="YOUCOM_API_KEY"):
            await tool.search("test")
        await tool.close()

    @pytest.mark.asyncio
    async def test_rate_limit_error_raises(self):
        tool = YoucomSearchTool(settings=_make_settings())

        mock_resp = MagicMock()
        mock_resp.status_code = 429

        with patch("tools.youcom_search.YoucomSearchTool._get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_resp
            mock_get_session.return_value = mock_session
            with pytest.raises(RuntimeError, match="rate limit"):
                await tool.search("test")
        await tool.close()

    @pytest.mark.asyncio
    async def test_close_clears_session(self):
        tool = YoucomSearchTool(settings=_make_settings())
        tool._session = MagicMock()
        await tool.close()
        assert tool._session is None
