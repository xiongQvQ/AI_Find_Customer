"""Tests for agents/search_agent.py — Google Maps-only routing, dedup, stats."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.search_agent import (
    _build_maps_snippet,
    _is_china_region,
    _maps_search_keyword,
    _result_identity_key,
    search_node,
)


def _base_state(**overrides):
    base = {
        "website_url": "https://solartech.de",
        "product_keywords": ["solar inverter"],
        "target_regions": ["Europe"],
        "uploaded_files": [],
        "target_lead_count": 200,
        "max_rounds": 10,
        "insight": {
            "products": ["solar inverter"],
            "industries": ["Renewable Energy"],
        },
        "keywords": ["solar inverter distributor", "PV panel wholesale"],
        "used_keywords": ["solar inverter distributor", "PV panel wholesale"],
        "search_results": [],
        "seen_urls": [],
        "matched_platforms": [],
        "keyword_search_stats": {},
        "leads": [],
        "email_sequences": [],
        "hunt_round": 1,
        "prev_round_lead_count": 0,
        "round_feedback": None,
        "current_stage": "keyword_gen",
        "messages": [],
    }
    base.update(overrides)
    return base


class TestMapsSearchKeyword:
    @pytest.mark.asyncio
    async def test_returns_maps_results_and_fields(self):
        sem = asyncio.Semaphore(5)
        mock_tool = AsyncMock()
        mock_tool.search = AsyncMock(return_value=[
            {
                "title": "Solar Co",
                "website": "https://solar.com",
                "address": "Berlin",
                "phone_number": "+49 123",
                "rating": 4.5,
                "rating_count": 100,
                "type": "Solar company",
                "types": ["Solar company"],
                "description": "Distributor",
                "email": "sales@solar.com",
                "place_id": "abc",
            },
        ])

        result = await _maps_search_keyword("solar", mock_tool, sem)
        assert result["keyword"] == "solar"
        assert result["result_count"] == 1
        assert result["source"] == "google_maps"
        assert result["results"][0]["link"] == "https://solar.com"
        assert result["results"][0]["maps_data"]["phoneNumber"] == "+49 123"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_keeps_maps_rows_without_website(self):
        sem = asyncio.Semaphore(5)
        mock_tool = AsyncMock()
        mock_tool.search = AsyncMock(return_value=[
            {"title": "No Website Co", "address": "Berlin", "place_id": "pid-1"},
            {"title": "Has Website", "website": "https://has.com", "address": "Munich", "place_id": "pid-2"},
        ])

        result = await _maps_search_keyword("test", mock_tool, sem)
        assert result["result_count"] == 2
        assert result["results"][0]["link"] == ""
        assert result["results"][0]["maps_data"]["place_id"] == "pid-1"

    @pytest.mark.asyncio
    async def test_handles_maps_error(self):
        sem = asyncio.Semaphore(5)
        mock_tool = AsyncMock()
        mock_tool.search = AsyncMock(side_effect=Exception("Maps API error"))

        result = await _maps_search_keyword("test", mock_tool, sem)
        assert result["result_count"] == 0
        assert result["source"] == "google_maps"
        assert result["error"] == "Maps API error"


class TestBuildMapsSnippet:
    def test_full_snippet(self):
        place = {"type": "Solar", "address": "Berlin", "phone_number": "+49", "rating": 4.5, "rating_count": 10}
        assert _build_maps_snippet(place) == "Solar | Berlin | +49 | Rating: 4.5/5 (10 reviews)"

    def test_partial_snippet(self):
        place = {"type": "Solar", "address": "Berlin"}
        assert _build_maps_snippet(place) == "Solar | Berlin"

    def test_empty_snippet(self):
        assert _build_maps_snippet({}) == ""


class TestResultIdentityKey:
    def test_uses_url_when_present(self):
        key = _result_identity_key({"link": "https://example.com/a"})
        assert key == "url:https://example.com/a"

    def test_uses_place_id_without_url(self):
        key = _result_identity_key({"link": "", "maps_data": {"place_id": "PID-1"}})
        assert key == "place:pid-1"

    def test_falls_back_to_title_and_address(self):
        key = _result_identity_key({"title": "ACME", "maps_data": {"address": "Berlin"}})
        assert key == "maps:acme|berlin"


class TestSearchNode:
    @pytest.mark.asyncio
    async def test_maps_only_routing(self):
        state = _base_state(keywords=["solar berlin"])

        maps_places = [
            {
                "title": "Maps Place",
                "website": "https://maps-place.com",
                "address": "Berlin",
                "type": "Solar",
                "types": ["Solar"],
                "place_id": "xyz",
            },
        ]

        with patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5
            maps_inst = AsyncMock()
            maps_inst.search = AsyncMock(return_value=maps_places)
            maps_inst.close = AsyncMock()
            MockMaps.return_value = maps_inst

            result = await search_node(state)

        assert result["current_stage"] == "search"
        assert len(result["search_results"]) == 1
        assert result["search_results"][0]["source"] == "google_maps"
        maps_inst.search.assert_called_once()
        maps_inst.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_deduplicates_by_place_without_website(self):
        state = _base_state(
            keywords=["k1", "k2"],
            search_results=[],
            seen_urls=[],
        )

        maps_places = [{"title": "No Website Co", "address": "Berlin", "place_id": "pid-1"}]

        with patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5
            maps_inst = AsyncMock()
            maps_inst.search = AsyncMock(return_value=maps_places)
            maps_inst.close = AsyncMock()
            MockMaps.return_value = maps_inst

            result = await search_node(state)

        assert len(result["search_results"]) == 1
        assert result["seen_urls"] == ["place:pid-1"]

    @pytest.mark.asyncio
    async def test_accumulates_keyword_stats(self):
        state = _base_state(keywords=["kw1"])

        maps_places = [
            {"title": "R1", "website": "https://r1.com", "place_id": "p1"},
            {"title": "R2", "address": "Berlin", "place_id": "p2"},
        ]

        with patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5
            maps_inst = AsyncMock()
            maps_inst.search = AsyncMock(return_value=maps_places)
            maps_inst.close = AsyncMock()
            MockMaps.return_value = maps_inst

            result = await search_node(state)

        assert "kw1" in result["keyword_search_stats"]
        assert result["keyword_search_stats"]["kw1"]["result_count"] == 2

    @pytest.mark.asyncio
    async def test_empty_keywords_returns_early(self):
        state = _base_state(keywords=[])
        result = await search_node(state)
        assert result["current_stage"] == "search"


class TestIsChinaRegion:
    def test_china_english(self):
        assert _is_china_region(["China"]) is True

    def test_china_chinese(self):
        assert _is_china_region(["中国"]) is True

    def test_non_china(self):
        assert _is_china_region(["Germany", "Poland"]) is False
