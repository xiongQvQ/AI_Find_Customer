"""Tests for tools/baidu_search.py — mock Baidu Qianfan API, verify result parsing."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from tools.baidu_search import BaiduSearchTool

_FAKE_REQUEST = httpx.Request("POST", "https://qianfan.baidubce.com/v2/ai_search/web_search")

BAIDU_RESPONSE = {
    "request_id": "test-request-id-001",
    "references": [
        {
            "id": 1,
            "title": "深圳光伏科技有限公司-太阳能逆变器经销商",
            "web_anchor": "深圳光伏科技有限公司",
            "content": "深圳市光伏科技有限公司专业从事太阳能逆变器、光伏组件的批发与零售，是华南地区最大的光伏产品经销商之一。",
            "url": "https://www.szpvtech.com.cn/about",
            "date": "2025-01-15 10:00:00",
            "type": "web",
            "icon": None,
            "image": None,
            "video": None,
        },
        {
            "id": 2,
            "title": "上海新能源设备有限公司",
            "web_anchor": "上海新能源",
            "content": "上海新能源设备有限公司是专业的太阳能产品进口商和分销商，代理多个国际知名品牌。",
            "url": "https://www.sh-newenergy.com",
            "date": "2025-02-20 09:30:00",
            "type": "web",
            "icon": None,
            "image": None,
            "video": None,
        },
        {
            "id": 3,
            "title": "北京绿能科技",
            "web_anchor": "北京绿能科技",
            "content": "北京绿能科技有限公司，专注于光伏储能系统集成，提供完整的离网和并网解决方案。",
            "url": "https://www.bjgreenenergy.com",
            "date": "2025-03-01 14:00:00",
            "type": "web",
            "icon": None,
            "image": None,
            "video": None,
        },
        {
            "id": 4,
            "title": "No URL result",
            "web_anchor": "No URL",
            "content": "This result has no URL and should be filtered out.",
            "url": "",
            "date": "2025-01-01 00:00:00",
            "type": "web",
            "icon": None,
            "image": None,
            "video": None,
        },
    ],
}


def _make_mock_response(data: dict, status_code: int = 200) -> httpx.Response:
    import json
    return httpx.Response(
        status_code=status_code,
        content=json.dumps(data).encode(),
        request=_FAKE_REQUEST,
    )


class TestBaiduSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_parsed_results(self):
        """Normal search returns correctly parsed results, filtering empty URLs."""
        tool = BaiduSearchTool(api_key="test-key")
        mock_resp = _make_mock_response(BAIDU_RESPONSE)

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_client

            results = await tool.search("太阳能逆变器经销商 深圳")

        # 4 references but 1 has empty URL → 3 results
        assert len(results) == 3
        assert results[0]["title"] == "深圳光伏科技有限公司-太阳能逆变器经销商"
        assert results[0]["link"] == "https://www.szpvtech.com.cn/about"
        assert "光伏" in results[0]["snippet"]
        assert results[0]["source"] == "baidu"
        assert results[0]["position"] == 1

    @pytest.mark.asyncio
    async def test_search_result_positions_are_sequential(self):
        """Position field increments from 1."""
        tool = BaiduSearchTool(api_key="test-key")
        mock_resp = _make_mock_response(BAIDU_RESPONSE)

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_client

            results = await tool.search("test query")

        positions = [r["position"] for r in results]
        assert positions == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_empty(self):
        """Empty query returns empty list without making HTTP call."""
        tool = BaiduSearchTool(api_key="test-key")
        with patch.object(tool, "_get_client") as mock_get_client:
            results = await tool.search("   ")
            mock_get_client.assert_not_called()

        assert results == []

    @pytest.mark.asyncio
    async def test_search_http_error_returns_empty(self):
        """HTTP error returns empty list (logged as warning, not raised)."""
        tool = BaiduSearchTool(api_key="bad-key")
        mock_resp = _make_mock_response(
            {"requestId": "x", "code": 216003, "message": "Authentication error"},
            status_code=401,
        )

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_client

            results = await tool.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_network_error_returns_empty(self):
        """Network exception returns empty list (not raised)."""
        tool = BaiduSearchTool(api_key="test-key")

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("timeout"))
            mock_get_client.return_value = mock_client

            results = await tool.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_empty_references_returns_empty(self):
        """Response with empty references list returns empty list."""
        tool = BaiduSearchTool(api_key="test-key")
        mock_resp = _make_mock_response({"request_id": "x", "references": []})

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_client

            results = await tool.search("obscure query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_uses_correct_api_endpoint_and_headers(self):
        """Verifies correct URL, auth header, and payload are sent."""
        tool = BaiduSearchTool(api_key="my-secret-key", top_k=5)
        mock_resp = _make_mock_response({"references": []})

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_client

            await tool.search("solar inverter distributor")

        call_kwargs = mock_client.post.call_args
        url = call_kwargs[0][0]
        headers = call_kwargs[1]["headers"]
        payload = call_kwargs[1]["json"]

        assert "qianfan.baidubce.com" in url
        assert "web_search" in url
        assert headers["X-Appbuilder-Authorization"] == "Bearer my-secret-key"
        assert payload["messages"][0]["content"] == "solar inverter distributor"
        assert payload["search_source"] == "baidu_search_v2"
        assert payload["resource_type_filter"][0]["top_k"] == 5

    @pytest.mark.asyncio
    async def test_search_top_k_override(self):
        """Per-call top_k overrides instance default."""
        tool = BaiduSearchTool(api_key="test-key", top_k=10)
        mock_resp = _make_mock_response({"references": []})

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_client

            await tool.search("query", top_k=3)

        payload = mock_client.post.call_args[1]["json"]
        assert payload["resource_type_filter"][0]["top_k"] == 3

    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """close() closes the underlying httpx client."""
        tool = BaiduSearchTool(api_key="test-key")
        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        tool._client = mock_client

        await tool.close()

        mock_client.aclose.assert_called_once()
        assert tool._client is None

    @pytest.mark.asyncio
    async def test_close_noop_when_no_client(self):
        """close() is safe to call when no client has been created."""
        tool = BaiduSearchTool(api_key="test-key")
        await tool.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_web_anchor_used_as_title_fallback(self):
        """If title is empty, web_anchor is used as title."""
        tool = BaiduSearchTool(api_key="test-key")
        response = {
            "references": [{
                "id": 1,
                "title": "",
                "web_anchor": "Fallback Title",
                "content": "Some content",
                "url": "https://example.com",
                "type": "web",
            }]
        }
        mock_resp = _make_mock_response(response)

        with patch.object(tool, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_client

            results = await tool.search("test")

        assert results[0]["title"] == "Fallback Title"
