"""Tests for tools/scavio_maps_search.py using mocked Scavio Maps requests."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from config.settings import Settings
from tools.scavio_maps_search import ScavioMapsSearchTool

_FAKE_REQUEST = httpx.Request("POST", "https://api.scavio.dev/api/v2/google/maps/search")


def _make_settings(**overrides) -> Settings:
    defaults = {"scavio_api_key": "sk-scavio-test", "maps_search_provider": "scavio"}
    defaults.update(overrides)
    return Settings(**defaults)


# Trimmed from a live response for "LED lighting distributor Munich".
SCAVIO_MAPS_RESPONSE = {
    "search_parameters": {
        "engine": "google_maps",
        "type": "search",
        "q": "LED lighting distributor Munich",
    },
    "local_results": [
        {
            "position": 1,
            "title": "Davies GmbH",
            "place_id": "ChIJuV3i2ih0nkcRZvY5DsE9Zik",
            "data_id": "0x479e7428dae25db9:0x29663dc10e39f666",
            "data_cid": "2983139702556194406",
            "gps_coordinates": {"latitude": 48.184129999999996, "longitude": 11.585989999999999},
            "rating": 4.9,
            "reviews": 14,
            "type": "Lighting store",
            "types": ["Lighting store"],
            "address": "Leopoldstraße 256, 80807 München, Germany",
            "phone": "+49 89 215477480",
            "website": "http://www.davies-led.de/",
        },
        {
            "position": 2,
            "title": "Astera LED Technology GmbH",
            "place_id": "ChIJnf-_RHgLnkcRqoQrtUARQpY",
            "data_id": "0x479e0b7844bfff9d:0x96421140b52b84aa",
            "data_cid": "10827235423767200938",
            "gps_coordinates": {"latitude": 48.131733999999994, "longitude": 11.658831099999999},
            "rating": 4.7,
            "reviews": 3,
            "type": "Lighting manufacturer",
            "types": ["Lighting manufacturer"],
            "address": "Schatzbogen 60, 81829 München, Germany",
            "phone": "+49 89 215522531",
            "website": "http://www.astera-led.com/",
        },
    ],
    "cached": False,
    "credits_used": 1,
}


def _capture_post(captured: dict, response: dict | None = None, status: int = 200):
    async def mock_post(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        captured["json"] = kwargs.get("json", {})
        body = response or {"local_results": []}
        return httpx.Response(status, json=body, request=_FAKE_REQUEST)

    return mock_post


class TestScavioMapsSearchTool:
    @pytest.mark.asyncio
    async def test_search_returns_places_in_the_serper_row_shape(self):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json=SCAVIO_MAPS_RESPONSE, request=_FAKE_REQUEST)

        with patch.object(
            httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp
        ):
            results = await tool.search("LED lighting distributor Munich")

        assert len(results) == 2
        first = results[0]
        assert first["title"] == "Davies GmbH"
        assert first["address"] == "Leopoldstraße 256, 80807 München, Germany"
        assert first["website"] == "http://www.davies-led.de/"
        assert first["phone_number"] == "+49 89 215477480"
        assert first["rating"] == 4.9
        assert first["rating_count"] == 14
        assert first["type"] == "Lighting store"
        assert first["types"] == ["Lighting store"]
        assert first["latitude"] == pytest.approx(48.18413)
        assert first["longitude"] == pytest.approx(11.58599)
        assert first["cid"] == "2983139702556194406"
        assert first["place_id"] == "ChIJuV3i2ih0nkcRZvY5DsE9Zik"
        assert first["email"] == ""
        await tool.close()

    @pytest.mark.asyncio
    async def test_search_sends_key_and_a_country_view_for_gl(self):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        captured: dict = {}

        with patch.object(httpx.AsyncClient, "post", side_effect=_capture_post(captured)):
            await tool.search("solar inverter distributor Berlin", gl="de", hl="de")

        assert captured["url"] == "https://api.scavio.dev/api/v2/google/maps/search"
        assert captured["headers"]["Authorization"] == "Bearer sk-scavio-test"
        assert captured["json"] == {
            "query": "solar inverter distributor Berlin",
            "hl": "de",
            "ll": "@51.1657,10.4515,6z",
            "gl": "de",
        }
        await tool.close()

    @pytest.mark.asyncio
    async def test_uk_is_sent_as_gb(self):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        captured: dict = {}

        with patch.object(httpx.AsyncClient, "post", side_effect=_capture_post(captured)):
            await tool.search("wholesaler Manchester", gl="uk", hl="en")

        assert captured["json"]["gl"] == "gb"
        assert captured["json"]["ll"] == "@54.0000,-2.5000,6z"
        await tool.close()

    @pytest.mark.asyncio
    async def test_explicit_ll_wins_and_unknown_gl_is_not_sent_alone(self):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        captured: dict = {}

        with patch.object(httpx.AsyncClient, "post", side_effect=_capture_post(captured)):
            await tool.search("q", gl="de", ll="@48.1351,11.5820,12z")
        assert captured["json"]["ll"] == "@48.1351,11.5820,12z"

        with patch.object(httpx.AsyncClient, "post", side_effect=_capture_post(captured)):
            await tool.search("q", gl="zz", hl="en")
        assert captured["json"] == {"query": "q", "hl": "en"}
        await tool.close()

    @pytest.mark.asyncio
    async def test_num_limits_the_rows(self):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        mock_resp = httpx.Response(200, json=SCAVIO_MAPS_RESPONSE, request=_FAKE_REQUEST)

        with patch.object(
            httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp
        ):
            results = await tool.search("q", num=1)

        assert [r["title"] for r in results] == ["Davies GmbH"]
        await tool.close()

    @pytest.mark.asyncio
    async def test_missing_key_raises_before_any_request(self):
        tool = ScavioMapsSearchTool(settings=_make_settings(scavio_api_key=""))

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as post:
            with pytest.raises(RuntimeError, match="SCAVIO_API_KEY"):
                await tool.search("q")
        post.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("status", "message"),
        [(401, "SCAVIO_API_KEY"), (402, "out of credits")],
    )
    async def test_key_and_credit_errors_are_named(self, status, message):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        resp = httpx.Response(status, json={"error": "x"}, request=_FAKE_REQUEST)

        with patch.object(
            httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=resp
        ) as post:
            with pytest.raises(RuntimeError, match=message):
                await tool.search("q")
        assert post.call_count == 1
        await tool.close()

    @pytest.mark.asyncio
    async def test_server_error_raises_once_without_retry(self):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        resp = httpx.Response(502, json={"error": "upstream"}, request=_FAKE_REQUEST)

        with patch.object(
            httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=resp
        ) as post:
            with pytest.raises(httpx.HTTPStatusError):
                await tool.search("q")
        assert post.call_count == 1
        await tool.close()

    @pytest.mark.asyncio
    async def test_malformed_response_is_an_error_not_an_empty_result(self):
        tool = ScavioMapsSearchTool(settings=_make_settings())
        resp = httpx.Response(200, json={"error": "nope"}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=resp):
            with pytest.raises(RuntimeError, match="local_results"):
                await tool.search("q")
        await tool.close()
