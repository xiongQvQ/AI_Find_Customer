"""Tests for tools/web_search.py — Tavily-only WebSearchTool."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from config.settings import Settings
from tools.web_search import WebSearchTool, _RoundRobinPool, _parse_keys


# ── _parse_keys ───────────────────────────────────────────────────────────────


class TestParseKeys:
    def test_single_key(self):
        assert _parse_keys("abc123") == ["abc123"]

    def test_multiple_keys(self):
        assert _parse_keys("key1,key2,key3") == ["key1", "key2", "key3"]

    def test_strips_whitespace(self):
        assert _parse_keys("key1, key2 , key3") == ["key1", "key2", "key3"]

    def test_empty_string(self):
        assert _parse_keys("") == []

    def test_only_commas(self):
        assert _parse_keys(",,,") == []

    def test_trailing_comma(self):
        assert _parse_keys("key1,key2,") == ["key1", "key2"]


# ── _RoundRobinPool ───────────────────────────────────────────────────────────


class TestRoundRobinPool:
    def test_single_key_always_returns_same(self):
        pool = _RoundRobinPool(["only"])
        assert pool.next_key() == "only"
        assert pool.next_key() == "only"

    def test_two_keys_alternate(self):
        pool = _RoundRobinPool(["a", "b"])
        assert pool.next_key() == "a"
        assert pool.next_key() == "b"
        assert pool.next_key() == "a"
        assert pool.next_key() == "b"

    def test_three_keys_cycle(self):
        pool = _RoundRobinPool(["x", "y", "z"])
        results = [pool.next_key() for _ in range(6)]
        assert results == ["x", "y", "z", "x", "y", "z"]

    def test_bool_true_when_non_empty(self):
        assert bool(_RoundRobinPool(["k"])) is True

    def test_bool_false_when_empty(self):
        assert bool(_RoundRobinPool([])) is False

    def test_len(self):
        assert len(_RoundRobinPool(["a", "b", "c"])) == 3


# ── WebSearchTool backend selection ──────────────────────────────────────────


def _settings(**kwargs) -> Settings:
    defaults = dict(
        tavily_api_key="",
    )
    defaults.update(kwargs)
    return Settings(
        openai_api_key="x",
        **defaults,
    )


class TestWebSearchToolBackendSelection:
    def test_tavily_is_required_backend(self):
        s = _settings(tavily_api_key="tkey")
        tool = WebSearchTool(s)
        assert tool.backend == "tavily"

    def test_raises_when_no_keys(self):
        s = _settings(tavily_api_key="")
        with pytest.raises(ValueError, match="Set TAVILY_API_KEY"):
            WebSearchTool(s)

    def test_multi_key_tavily_pool_size(self):
        s = _settings(tavily_api_key="t1,t2")
        tool = WebSearchTool(s)
        assert len(tool._tavily_pool) == 2


# ── WebSearchTool.search() — Tavily backend ──────────────────────────────────


class TestWebSearchToolTavily:
    @pytest.mark.asyncio
    async def test_tavily_search_returns_results(self):
        s = _settings(tavily_api_key="tkey")
        tool = WebSearchTool(s)

        tavily_results = [
            {"title": "Foo", "link": "https://foo.com", "snippet": "desc", "position": 1}
        ]
        with patch("tools.web_search._tavily_search", AsyncMock(return_value=tavily_results)):
            results = await tool.search("packaging machine")

        assert len(results) == 1
        assert results[0]["title"] == "Foo"

    @pytest.mark.asyncio
    async def test_tavily_passes_country_param(self):
        """Tavily should use native country param, not site:.{gl} query hack."""
        s = _settings(tavily_api_key="tkey")
        tool = WebSearchTool(s)

        captured_kwargs: list[dict] = []

        async def fake_tavily(api_key, query, num, gl):
            captured_kwargs.append({"query": query, "gl": gl})
            return []

        with patch("tools.web_search._tavily_search", fake_tavily):
            await tool.search("solar distributor", gl="de")

        assert captured_kwargs[0]["gl"] == "de"
        # query must NOT contain site:.de hack
        assert "site:.de" not in captured_kwargs[0]["query"]

    @pytest.mark.asyncio
    async def test_tavily_uses_round_robin_keys(self):
        s = _settings(tavily_api_key="t1,t2,t3")
        tool = WebSearchTool(s)

        used_keys: list[str] = []

        async def fake_tavily(api_key, query, num, gl):
            used_keys.append(api_key)
            return []

        with patch("tools.web_search._tavily_search", fake_tavily):
            await tool.search("q1")
            await tool.search("q2")
            await tool.search("q3")
            await tool.search("q4")

        assert used_keys == ["t1", "t2", "t3", "t1"]

    @pytest.mark.asyncio
    async def test_tavily_error_is_raised_without_local_serper_fallback(self):
        s = _settings(tavily_api_key="tkey")
        tool = WebSearchTool(s)

        with patch("tools.web_search._tavily_search", AsyncMock(side_effect=Exception("Tavily down"))):
            with pytest.raises(Exception, match="Tavily down"):
                await tool.search("query")

    @pytest.mark.asyncio
    async def test_close_releases_client(self):
        s = _settings(tavily_api_key="tkey")
        tool = WebSearchTool(s)
        await tool.close()
