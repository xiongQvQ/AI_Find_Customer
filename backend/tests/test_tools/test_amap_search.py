"""Tests for tools/amap_search.py — mock Amap POI API, verify result parsing."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from config.settings import Settings
from tools.amap_search import AmapSearchTool

_FAKE_REQUEST = httpx.Request("GET", "https://fake")


def _make_settings(**overrides) -> Settings:
    defaults = {"amap_api_key": "amap-test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


AMAP_RESPONSE = {
    "status": "1",
    "info": "ok",
    "infocode": "10000",
    "count": "3",
    "pois": [
        {
            "name": "深圳光伏科技有限公司",
            "id": "B0001",
            "address": "南山区科技园南路100号",
            "location": "113.9440,22.5400",
            "type": "公司企业;公司",
            "typecode": "170100",
            "pname": "广东省",
            "cityname": "深圳市",
            "adname": "南山区",
            "business": {
                "tel": "0755-12345678",
                "business_area": "科技园",
                "rating": "4.5",
            },
        },
        {
            "name": "上海新能源设备有限公司",
            "id": "B0002",
            "address": "浦东新区张江高科技园区",
            "location": "121.6100,31.2000",
            "type": "公司企业;公司",
            "typecode": "170100",
            "pname": "上海市",
            "cityname": "上海市",
            "adname": "浦东新区",
            "business": {
                "tel": "021-87654321",
                "business_area": "张江",
            },
        },
        {
            "name": "北京绿能科技有限公司",
            "id": "B0003",
            "address": "海淀区中关村大街1号",
            "location": "116.3200,39.9900",
            "type": "公司企业;公司",
            "typecode": "170100",
            "pname": "北京市",
            "cityname": "北京市",
            "adname": "海淀区",
            "business": {},
        },
    ],
}


class TestAmapSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_pois(self):
        tool = AmapSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json=AMAP_RESPONSE, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("光伏设备")

        assert len(results) == 3
        assert results[0]["name"] == "深圳光伏科技有限公司"
        assert results[0]["address"] == "南山区科技园南路100号"
        assert results[0]["phone"] == "0755-12345678"
        assert results[0]["province"] == "广东省"
        assert results[0]["city"] == "深圳市"
        assert results[0]["district"] == "南山区"
        assert results[0]["longitude"] == pytest.approx(113.944)
        assert results[0]["latitude"] == pytest.approx(22.54)
        assert results[0]["business_area"] == "科技园"
        assert results[0]["rating"] == "4.5"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_correct_params(self):
        tool = AmapSearchTool(settings=_make_settings())
        captured_params = {}

        async def mock_get(url, **kwargs):
            captured_params.update(kwargs.get("params", {}))
            return httpx.Response(200, json={"status": "1", "pois": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.search("太阳能", region="深圳市", city_limit=True)

        assert captured_params["key"] == "amap-test-key"
        assert captured_params["keywords"] == "太阳能"
        assert captured_params["region"] == "深圳市"
        assert captured_params["city_limit"] == "true"
        assert captured_params["show_fields"] == "business"
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_no_region(self):
        tool = AmapSearchTool(settings=_make_settings())
        captured_params = {}

        async def mock_get(url, **kwargs):
            captured_params.update(kwargs.get("params", {}))
            return httpx.Response(200, json={"status": "1", "pois": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.search("光伏")

        assert "region" not in captured_params
        assert "city_limit" not in captured_params
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        tool = AmapSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json={"status": "1", "pois": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("不存在的公司")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_api_error(self):
        tool = AmapSearchTool(settings=_make_settings())
        error_resp = {"status": "0", "info": "INVALID_USER_KEY", "infocode": "10001"}
        mock_resp = httpx.Response(200, json=error_resp, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("test")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_http_error(self):
        tool = AmapSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(403, json={"error": "forbidden"}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(httpx.HTTPStatusError):
                await tool.search("test")
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_no_api_key(self):
        tool = AmapSearchTool(settings=_make_settings(amap_api_key=""))
        results = await tool.search("test")
        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_missing_business(self):
        """POI without business info should still parse correctly."""
        tool = AmapSearchTool(settings=_make_settings())
        sparse_response = {
            "status": "1",
            "pois": [
                {
                    "name": "测试公司",
                    "id": "B9999",
                    "address": "测试地址",
                    "location": "116.0,39.0",
                    "pname": "北京市",
                    "cityname": "北京市",
                    "adname": "朝阳区",
                },
            ],
        }
        mock_resp = httpx.Response(200, json=sparse_response, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("test")

        assert len(results) == 1
        assert results[0]["name"] == "测试公司"
        assert results[0]["phone"] == ""
        assert results[0]["business_area"] == ""
        assert results[0]["longitude"] == pytest.approx(116.0)
        assert results[0]["latitude"] == pytest.approx(39.0)
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_bad_location_format(self):
        """POI with invalid location string should default to 0,0."""
        tool = AmapSearchTool(settings=_make_settings())
        response = {
            "status": "1",
            "pois": [{"name": "X", "location": "bad"}],
        }
        mock_resp = httpx.Response(200, json=response, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.search("test")

        assert results[0]["longitude"] == 0.0
        assert results[0]["latitude"] == 0.0
        await tool.close()

    @pytest.mark.asyncio
    async def test_close(self):
        tool = AmapSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json={"status": "1", "pois": []}, request=_FAKE_REQUEST)
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            await tool.search("test")

        assert tool._client is not None
        await tool.close()
        assert tool._client is None

    @pytest.mark.asyncio
    async def test_search_with_types(self):
        tool = AmapSearchTool(settings=_make_settings())
        captured_params = {}

        async def mock_get(url, **kwargs):
            captured_params.update(kwargs.get("params", {}))
            return httpx.Response(200, json={"status": "1", "pois": []}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.search("太阳能", types="170100|170200")

        assert captured_params["types"] == "170100|170200"
        await tool.close()
