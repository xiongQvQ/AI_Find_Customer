"""Tests for agents/search_agent.py — concurrent search, semaphore, dedup, stats."""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from agents.search_agent import (
    search_node,
    _search_keyword,
    _maps_search_keyword,
    _baidu_search_keyword,
    _build_maps_snippet,
    _is_china_region,
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


class TestSearchKeyword:
    @pytest.mark.asyncio
    async def test_returns_results(self):
        sem = asyncio.Semaphore(5)
        mock_tool = AsyncMock()
        mock_tool.search = AsyncMock(return_value=[
            {"title": "Result 1", "link": "https://a.com", "snippet": "...", "position": 1},
        ])

        result = await _search_keyword("test kw", mock_tool, sem)
        assert result["keyword"] == "test kw"
        assert result["result_count"] == 1
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_handles_search_error(self):
        sem = asyncio.Semaphore(5)
        mock_tool = AsyncMock()
        mock_tool.search = AsyncMock(side_effect=Exception("API error"))

        result = await _search_keyword("test kw", mock_tool, sem)
        assert result["result_count"] == 0
        assert result["error"] == "API error"

    @pytest.mark.asyncio
    async def test_respects_semaphore(self):
        """Verify semaphore limits concurrency."""
        sem = asyncio.Semaphore(2)
        max_concurrent = {"val": 0}
        current = {"val": 0}

        original_search = AsyncMock(return_value=[])

        async def tracked_search(query, **kwargs):
            current["val"] += 1
            max_concurrent["val"] = max(max_concurrent["val"], current["val"])
            await asyncio.sleep(0.05)
            current["val"] -= 1
            return []

        mock_tool = AsyncMock()
        mock_tool.search = tracked_search

        tasks = [_search_keyword(f"kw{i}", mock_tool, sem) for i in range(6)]
        await asyncio.gather(*tasks)

        assert max_concurrent["val"] <= 2


class TestMapsSearchKeyword:
    @pytest.mark.asyncio
    async def test_returns_results_with_website(self):
        sem = asyncio.Semaphore(5)
        mock_tool = AsyncMock()
        mock_tool.search = AsyncMock(return_value=[
            {"title": "Solar Co", "website": "https://solar.com", "address": "Berlin",
             "phone_number": "+49 123", "rating": 4.5, "rating_count": 100,
             "type": "Solar company", "latitude": 52.5, "longitude": 13.4, "place_id": "abc"},
        ])

        result = await _maps_search_keyword("solar", mock_tool, sem)
        assert result["keyword"] == "solar"
        assert result["result_count"] == 1
        assert result["source"] == "google_maps"
        assert result["results"][0]["link"] == "https://solar.com"
        assert result["results"][0]["maps_data"]["address"] == "Berlin"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_skips_places_without_website(self):
        sem = asyncio.Semaphore(5)
        mock_tool = AsyncMock()
        mock_tool.search = AsyncMock(return_value=[
            {"title": "No Website", "address": "Berlin"},
            {"title": "Has Website", "website": "https://has.com", "address": "Munich"},
        ])

        result = await _maps_search_keyword("test", mock_tool, sem)
        assert result["result_count"] == 1
        assert result["results"][0]["link"] == "https://has.com"

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


def _mock_search_node_tools():
    """Helper to create all mocked tools for search_node tests."""
    search_inst = AsyncMock()
    search_inst.search = AsyncMock(return_value=[])
    search_inst.close = AsyncMock()

    maps_inst = AsyncMock()
    maps_inst.search = AsyncMock(return_value=[])
    maps_inst.close = AsyncMock()

    platform_inst = MagicMock()
    platform_inst.build_queries = MagicMock(return_value=[])
    platform_inst.match = MagicMock(return_value=[])

    return search_inst, maps_inst, platform_inst


class TestSearchNode:
    @pytest.mark.asyncio
    async def test_returns_search_results(self):
        state = _base_state()

        fake_results = [
            {"title": "SolarTech", "link": "https://solartech.de", "snippet": "...", "position": 1},
            {"title": "PV Dist", "link": "https://pvdist.com", "snippet": "...", "position": 2},
        ]

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.search = AsyncMock(return_value=fake_results)
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            result = await search_node(state)

        assert result["current_stage"] == "search"
        assert len(result["search_results"]) > 0

    @pytest.mark.asyncio
    async def test_deduplicates_urls(self):
        state = _base_state()

        # Both keywords return the same URL
        fake_results = [
            {"title": "Same", "link": "https://same.com", "snippet": "...", "position": 1},
        ]

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.search = AsyncMock(return_value=fake_results)
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            result = await search_node(state)

        # Should deduplicate — only 1 unique URL even with 2 keywords
        urls = [r["link"] for r in result["search_results"]]
        assert urls.count("https://same.com") == 1

    @pytest.mark.asyncio
    async def test_accumulates_with_existing_results(self):
        existing = [{"title": "Old", "link": "https://old.com", "snippet": "...", "position": 1}]
        state = _base_state(search_results=existing)

        new_results = [
            {"title": "New", "link": "https://new.com", "snippet": "...", "position": 1},
        ]

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.search = AsyncMock(return_value=new_results)
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            result = await search_node(state)

        urls = [r["link"] for r in result["search_results"]]
        assert "https://old.com" in urls
        assert "https://new.com" in urls

    @pytest.mark.asyncio
    async def test_tracks_keyword_stats(self):
        state = _base_state(keywords=["kw1"])

        fake_results = [
            {"title": "R1", "link": "https://r1.com", "snippet": "...", "position": 1},
            {"title": "R2", "link": "https://r2.com", "snippet": "...", "position": 2},
        ]

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.search = AsyncMock(return_value=fake_results)
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            result = await search_node(state)

        assert "kw1" in result["keyword_search_stats"]
        assert result["keyword_search_stats"]["kw1"]["result_count"] >= 1

    @pytest.mark.asyncio
    async def test_empty_keywords_returns_early(self):
        state = _base_state(keywords=[])
        result = await search_node(state)
        assert result["current_stage"] == "search"

    @pytest.mark.asyncio
    async def test_includes_platform_searches(self):
        state = _base_state(keywords=["solar inverter"])

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 10

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst

            platform_inst.build_queries = MagicMock(return_value=[
                {"platform": "Alibaba", "domain": "alibaba.com", "query": "site:alibaba.com solar inverter"},
                {"platform": "Europages", "domain": "europages.com", "query": "site:europages.com solar inverter"},
            ])
            platform_inst.match = MagicMock(return_value=[])
            MockPlatform.return_value = platform_inst

            result = await search_node(state)

        # Should have called search 3 times: 1 general + 2 platform (maps is separate)
        assert search_inst.search.call_count == 3

    @pytest.mark.asyncio
    async def test_maps_results_merged_into_search_results(self):
        """Verify Google Maps results are merged alongside Google Search results."""
        state = _base_state(keywords=["solar Berlin"])

        google_results = [
            {"title": "Google Result", "link": "https://google-result.com", "snippet": "...", "position": 1},
        ]
        maps_places = [
            {"title": "Maps Place", "website": "https://maps-place.com", "address": "Berlin",
             "phone_number": "+49", "rating": 4.0, "rating_count": 50, "type": "Solar",
             "latitude": 52.5, "longitude": 13.4, "place_id": "xyz"},
        ]

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.search = AsyncMock(return_value=google_results)
            search_inst.backend = "brave"
            maps_inst.search = AsyncMock(return_value=maps_places)
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            result = await search_node(state)

        urls = [r["link"] for r in result["search_results"]]
        assert "https://google-result.com" in urls
        assert "https://maps-place.com" in urls

    @pytest.mark.asyncio
    async def test_maps_close_called(self):
        """Verify maps_tool.close() is called after search."""
        state = _base_state(keywords=["test"])

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value.search_concurrency = 5

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            await search_node(state)

        maps_inst.close.assert_called_once()
        search_inst.close.assert_called_once()


class TestIsChinaRegion:
    def test_china_english(self):
        assert _is_china_region(["China"]) is True

    def test_china_chinese(self):
        assert _is_china_region(["中国"]) is True

    def test_china_cn(self):
        assert _is_china_region(["cn"]) is True

    def test_mainland_china(self):
        assert _is_china_region(["mainland china"]) is True

    def test_non_china(self):
        assert _is_china_region(["Germany", "Poland"]) is False

    def test_empty(self):
        assert _is_china_region([]) is False

    def test_mixed_china_and_other(self):
        assert _is_china_region(["China", "Germany"]) is True


class TestBaiduSearchKeyword:
    @pytest.mark.asyncio
    async def test_returns_results(self):
        """_baidu_search_keyword returns correctly formatted results."""
        sem = asyncio.Semaphore(5)
        mock_tool = MagicMock()
        mock_tool.search = AsyncMock(return_value=[
            {"title": "深圳光伏公司", "link": "https://szpv.com", "snippet": "太阳能逆变器", "position": 1, "source": "baidu"},
            {"title": "上海新能源", "link": "https://sh-energy.com", "snippet": "光伏组件批发", "position": 2, "source": "baidu"},
        ])

        result = await _baidu_search_keyword("太阳能逆变器经销商", mock_tool, sem)

        assert result["keyword"] == "太阳能逆变器经销商"
        assert result["source"] == "baidu"
        assert result["error"] is None
        assert len(result["results"]) == 2
        assert result["results"][0]["link"] == "https://szpv.com"
        assert result["results"][0]["source"] == "baidu"

    @pytest.mark.asyncio
    async def test_filters_empty_links(self):
        """Results with empty link are filtered out."""
        sem = asyncio.Semaphore(5)
        mock_tool = MagicMock()
        mock_tool.search = AsyncMock(return_value=[
            {"title": "Good", "link": "https://good.com", "snippet": "ok", "position": 1, "source": "baidu"},
            {"title": "No URL", "link": "", "snippet": "no url", "position": 2, "source": "baidu"},
        ])

        result = await _baidu_search_keyword("test", mock_tool, sem)

        assert len(result["results"]) == 1
        assert result["results"][0]["link"] == "https://good.com"

    @pytest.mark.asyncio
    async def test_handles_error(self):
        """Exceptions are caught and returned as error field."""
        sem = asyncio.Semaphore(5)
        mock_tool = MagicMock()
        mock_tool.search = AsyncMock(side_effect=Exception("API timeout"))

        result = await _baidu_search_keyword("test", mock_tool, sem)

        assert result["results"] == []
        assert result["error"] == "API timeout"
        assert result["source"] == "baidu"


class TestChinaToolRouting:
    """Verify that China regions activate Baidu+Amap, non-China uses Google Maps."""

    def _make_settings(self, baidu_key="baidu-test-key", **overrides):
        from config.settings import Settings
        defaults = {
            "search_concurrency": 5,
            "baidu_api_key": baidu_key,
            "amap_api_key": "amap-test-key",
            "serper_api_key": "serper-key",
            "tavily_api_key": "tavily-test-key",
        }
        defaults.update(overrides)
        return Settings(**defaults)

    @pytest.mark.asyncio
    async def test_china_region_activates_baidu(self):
        """China region → BaiduSearchTool is instantiated with api_key."""
        state = _base_state(
            keywords=["太阳能逆变器经销商"],
            target_regions=["China"],
        )

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.AmapSearchTool") as MockAmap, \
             patch("agents.search_agent.BaiduSearchTool") as MockBaidu, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.JinaReaderTool") as MockJina, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value = self._make_settings()

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            baidu_inst = MagicMock()
            baidu_inst.search = AsyncMock(return_value=[])
            baidu_inst.close = AsyncMock()
            MockBaidu.return_value = baidu_inst

            amap_inst = MagicMock()
            amap_inst.search = AsyncMock(return_value=[])
            amap_inst.close = AsyncMock()
            MockAmap.return_value = amap_inst

            jina_inst = MagicMock()
            jina_inst.close = AsyncMock()
            MockJina.return_value = jina_inst

            await search_node(state)

        # BaiduSearchTool must be instantiated with the api_key
        MockBaidu.assert_called_once_with(api_key="baidu-test-key")

    @pytest.mark.asyncio
    async def test_china_region_no_baidu_key_skips_baidu(self):
        """China region but no baidu_api_key → BaiduSearchTool NOT instantiated."""
        state = _base_state(
            keywords=["太阳能逆变器"],
            target_regions=["China"],
        )

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.AmapSearchTool") as MockAmap, \
             patch("agents.search_agent.BaiduSearchTool") as MockBaidu, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.JinaReaderTool") as MockJina, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value = self._make_settings(baidu_key="")

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            amap_inst = MagicMock()
            amap_inst.search = AsyncMock(return_value=[])
            amap_inst.close = AsyncMock()
            MockAmap.return_value = amap_inst

            jina_inst = MagicMock()
            jina_inst.close = AsyncMock()
            MockJina.return_value = jina_inst

            await search_node(state)

        # BaiduSearchTool must NOT be instantiated when api_key is empty
        MockBaidu.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_china_region_does_not_activate_baidu(self):
        """Non-China region → BaiduSearchTool NOT instantiated."""
        state = _base_state(
            keywords=["solar inverter distributor"],
            target_regions=["Germany"],
        )

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.BaiduSearchTool") as MockBaidu, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.JinaReaderTool") as MockJina, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value = self._make_settings()

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            jina_inst = MagicMock()
            jina_inst.close = AsyncMock()
            MockJina.return_value = jina_inst

            await search_node(state)

        MockBaidu.assert_not_called()

    @pytest.mark.asyncio
    async def test_baidu_results_merged_into_search_results(self):
        """Baidu results appear in final search_results for China region."""
        state = _base_state(
            keywords=["太阳能逆变器"],
            target_regions=["China"],
            search_results=[],
        )

        baidu_result = {
            "title": "深圳光伏公司",
            "link": "https://szpv.com.cn",
            "snippet": "太阳能逆变器批发",
            "position": 1,
            "source": "baidu",
        }

        with patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.AmapSearchTool") as MockAmap, \
             patch("agents.search_agent.BaiduSearchTool") as MockBaidu, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.JinaReaderTool") as MockJina, \
             patch("agents.search_agent.get_settings") as mock_settings:

            mock_settings.return_value = self._make_settings()

            search_inst, maps_inst, platform_inst = _mock_search_node_tools()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst
            MockMaps.return_value = maps_inst
            MockPlatform.return_value = platform_inst

            baidu_inst = MagicMock()
            baidu_inst.search = AsyncMock(return_value=[baidu_result])
            baidu_inst.close = AsyncMock()
            MockBaidu.return_value = baidu_inst

            amap_inst = MagicMock()
            amap_inst.search = AsyncMock(return_value=[])
            amap_inst.close = AsyncMock()
            MockAmap.return_value = amap_inst

            jina_inst = MagicMock()
            jina_inst.close = AsyncMock()
            MockJina.return_value = jina_inst

            result = await search_node(state)

        urls = [r.get("link", "") for r in result["search_results"]]
        assert "https://szpv.com.cn" in urls
