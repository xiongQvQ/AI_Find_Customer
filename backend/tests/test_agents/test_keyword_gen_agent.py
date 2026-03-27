"""Tests for agents/keyword_gen_agent.py — LLM mock, feedback adaptation, dedup."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.keyword_gen_agent import keyword_gen_node, _build_prompt, _detect_local_languages


def _base_state(**overrides):
    base = {
        "website_url": "https://solartech.de",
        "product_keywords": ["solar inverter"],
        "target_regions": ["Europe"],
        "uploaded_files": [],
        "target_lead_count": 200,
        "max_rounds": 10,
        "insight": {
            "company_name": "SolarTech",
            "products": ["solar inverter", "PV panel"],
            "industries": ["Renewable Energy"],
            "target_customer_profile": "B2B distributors",
            "recommended_regions": ["Europe"],
            "recommended_keywords_seed": ["solar inverter distributor", "PV wholesale"],
        },
        "keywords": [],
        "used_keywords": [],
        "search_results": [],
        "matched_platforms": [],
        "keyword_search_stats": {},
        "leads": [],
        "email_sequences": [],
        "hunt_round": 1,
        "prev_round_lead_count": 0,
        "round_feedback": None,
        "current_stage": "insight",
        "messages": [],
    }
    base.update(overrides)
    return base


FAKE_KEYWORDS = ["solar inverter distributor Europe", "PV panel wholesale Germany",
                 "renewable energy importer France", "solar module buyer UK",
                 "photovoltaic distributor Spain", "green energy wholesale"]


class TestKeywordGenNode:
    @pytest.mark.asyncio
    async def test_generates_keywords(self):
        state = _base_state()

        with patch("agents.keyword_gen_agent.LLMTool") as MockLLM:
            llm = AsyncMock()
            llm.generate = AsyncMock(return_value=json.dumps(FAKE_KEYWORDS))
            llm.close = AsyncMock()
            MockLLM.return_value = llm

            result = await keyword_gen_node(state)

        assert len(result["keywords"]) > 0
        assert result["current_stage"] == "keyword_gen"
        assert len(result["used_keywords"]) == len(result["keywords"])

    @pytest.mark.asyncio
    async def test_deduplicates_against_used(self):
        state = _base_state(used_keywords=["solar inverter distributor europe"])

        with patch("agents.keyword_gen_agent.LLMTool") as MockLLM:
            llm = AsyncMock()
            llm.generate = AsyncMock(return_value=json.dumps(FAKE_KEYWORDS))
            llm.close = AsyncMock()
            MockLLM.return_value = llm

            result = await keyword_gen_node(state)

        # The first keyword matches used (case-insensitive), should be filtered
        for kw in result["keywords"]:
            assert kw.lower() != "solar inverter distributor europe"

    @pytest.mark.asyncio
    async def test_accumulates_used_keywords(self):
        state = _base_state(used_keywords=["old keyword 1", "old keyword 2"])

        with patch("agents.keyword_gen_agent.LLMTool") as MockLLM:
            llm = AsyncMock()
            llm.generate = AsyncMock(return_value=json.dumps(FAKE_KEYWORDS))
            llm.close = AsyncMock()
            MockLLM.return_value = llm

            result = await keyword_gen_node(state)

        assert "old keyword 1" in result["used_keywords"]
        assert "old keyword 2" in result["used_keywords"]
        assert len(result["used_keywords"]) > 2

    @pytest.mark.asyncio
    async def test_handles_dict_response(self):
        """LLM may return {"keywords": [...]} instead of bare array."""
        state = _base_state()

        with patch("agents.keyword_gen_agent.LLMTool") as MockLLM:
            llm = AsyncMock()
            llm.generate = AsyncMock(return_value=json.dumps({"keywords": FAKE_KEYWORDS}))
            llm.close = AsyncMock()
            MockLLM.return_value = llm

            result = await keyword_gen_node(state)

        assert len(result["keywords"]) > 0

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json(self):
        """If LLM returns invalid JSON, fall back to insight seed keywords."""
        state = _base_state()

        with patch("agents.keyword_gen_agent.LLMTool") as MockLLM:
            llm = AsyncMock()
            llm.generate = AsyncMock(return_value="not valid json at all")
            llm.close = AsyncMock()
            MockLLM.return_value = llm

            result = await keyword_gen_node(state)

        # Should fall back to insight seed keywords
        assert "solar inverter distributor" in result["keywords"]

    @pytest.mark.asyncio
    async def test_fallback_on_llm_error(self):
        """If LLM call fails, fall back to insight seed keywords."""
        state = _base_state()

        with patch("agents.keyword_gen_agent.LLMTool") as MockLLM:
            llm = AsyncMock()
            llm.generate = AsyncMock(side_effect=Exception("API error"))
            llm.close = AsyncMock()
            MockLLM.return_value = llm

            result = await keyword_gen_node(state)

        assert len(result["keywords"]) > 0
        assert result["current_stage"] == "keyword_gen"

    @pytest.mark.asyncio
    async def test_respects_max_keywords_per_round(self):
        """Should not return more than settings.default_keywords_per_round."""
        state = _base_state()
        many_keywords = [f"keyword_{i}" for i in range(20)]

        with patch("agents.keyword_gen_agent.LLMTool") as MockLLM, \
             patch("agents.keyword_gen_agent.get_settings") as mock_settings:
            mock_settings.return_value.default_keywords_per_round = 5

            llm = AsyncMock()
            llm.generate = AsyncMock(return_value=json.dumps(many_keywords))
            llm.close = AsyncMock()
            MockLLM.return_value = llm

            result = await keyword_gen_node(state)

        assert len(result["keywords"]) <= 5


class TestBuildPrompt:
    def test_includes_insight(self):
        state = _base_state()
        prompt = _build_prompt(state)
        assert "solar inverter" in prompt
        assert "Renewable Energy" in prompt
        assert "B2B distributors" in prompt

    def test_includes_used_keywords(self):
        state = _base_state(used_keywords=["old kw 1", "old kw 2"])
        prompt = _build_prompt(state)
        assert "old kw 1" in prompt
        assert "DO NOT repeat" in prompt

    def test_includes_feedback(self):
        feedback = {
            "round": 2,
            "total_leads": 50,
            "target": 200,
            "best_keywords": ["solar distributor"],
            "worst_keywords": ["random query"],
            "top_sources": ["linkedin.com"],
            "industry_distribution": {"Solar": 30},
            "region_distribution": {"de": 20},
        }
        state = _base_state(round_feedback=feedback)
        prompt = _build_prompt(state)
        assert "Round 2 Performance Feedback" in prompt
        assert "solar distributor" in prompt
        assert "HIGH performing" in prompt
        assert "LOW performing" in prompt
        assert "linkedin.com" in prompt

    def test_includes_target_regions(self):
        state = _base_state(target_regions=["Europe", "North America"])
        prompt = _build_prompt(state)
        assert "Europe" in prompt

    def test_no_feedback_first_round(self):
        state = _base_state(round_feedback=None)
        prompt = _build_prompt(state)
        assert "Feedback" not in prompt

    def test_used_keywords_truncated_to_recent_rounds(self):
        # With 30 used keywords and n_per_round=8, only last 16 should appear
        old_kws = [f"old_kw_{i}" for i in range(14)]
        recent_kws = [f"recent_kw_{i}" for i in range(16)]
        state = _base_state(used_keywords=old_kws + recent_kws)
        prompt = _build_prompt(state)
        # Recent keywords should appear
        assert "recent_kw_0" in prompt
        assert "recent_kw_15" in prompt
        # Old keywords beyond the window should NOT appear
        assert "old_kw_0" not in prompt

    def test_used_keywords_all_shown_when_few(self):
        # When total used < 2 rounds worth, show all
        state = _base_state(used_keywords=["kw_a", "kw_b", "kw_c"])
        prompt = _build_prompt(state)
        assert "kw_a" in prompt
        assert "kw_b" in prompt
        assert "kw_c" in prompt


class TestDetectLocalLanguages:
    def test_single_non_english_region(self):
        langs = _detect_local_languages(["Germany"])
        assert langs == ["German"]

    def test_multiple_non_english_regions(self):
        langs = _detect_local_languages(["Germany", "France", "Poland"])
        assert "German" in langs
        assert "French" in langs
        assert "Polish" in langs
        assert len(langs) == 3

    def test_english_region_returns_empty(self):
        langs = _detect_local_languages(["USA", "UK", "Australia"])
        assert langs == []

    def test_mixed_english_and_non_english(self):
        langs = _detect_local_languages(["Germany", "USA"])
        assert langs == ["German"]

    def test_deduplicates_same_language(self):
        # Germany and Austria both use German
        langs = _detect_local_languages(["Germany", "Austria"])
        assert langs.count("German") == 1

    def test_empty_regions(self):
        assert _detect_local_languages([]) == []

    def test_unrecognized_region(self):
        langs = _detect_local_languages(["Narnia"])
        assert langs == []

    def test_chinese_region(self):
        langs = _detect_local_languages(["China"])
        assert "Chinese (Simplified)" in langs

    def test_japanese_region(self):
        langs = _detect_local_languages(["Japan"])
        assert "Japanese" in langs
