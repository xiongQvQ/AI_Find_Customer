"""E2E integration test — full pipeline through LangGraph with mocked external calls.

Wires real agent nodes into the StateGraph and runs the complete pipeline:
Insight → KeywordGen → Search → LeadExtract → Evaluate → (loop or finish) → EmailCraft
"""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from graph.builder import build_graph
from graph.evaluate import evaluate_progress, should_continue_hunting
from agents.insight_agent import insight_node
from agents.keyword_gen_agent import keyword_gen_node
from agents.search_agent import search_node
from agents.lead_extract_agent import lead_extract_node
from agents.email_craft_agent import email_craft_node


# ── Fake LLM responses ─────────────────────────────────────────────────

FAKE_INSIGHT = json.dumps({
    "company_name": "SolarTech GmbH",
    "products": ["solar inverter", "PV panel"],
    "industries": ["Renewable Energy", "Electronics"],
    "value_propositions": ["High efficiency", "10-year warranty"],
    "target_customer_profile": "B2B distributors in Europe",
    "recommended_regions": ["Europe", "North America"],
    "recommended_keywords_seed": ["solar inverter distributor", "PV panel wholesale"],
    "summary": "SolarTech manufactures high-efficiency solar inverters.",
})

FAKE_KEYWORDS = json.dumps([
    "solar inverter distributor Europe",
    "PV panel wholesale Germany",
    "renewable energy importer France",
    "solar module buyer UK",
    "photovoltaic distributor Spain",
])

FAKE_LEAD_VALID = json.dumps({
    "is_valid_lead": True,
    "company_name": "EnergieDist GmbH",
    "website": "https://energiedist.de",
    "industry": "Energy Distribution",
    "description": "German energy distributor specializing in solar products",
    "contact_person": "Hans Mueller",
    "country_code": "de",
    "emails": ["info@energiedist.de"],
    "phone_numbers": ["+49 30 12345678"],
    "social_media": {"linkedin": "https://linkedin.com/company/energiedist"},
    "address": "Berlin, Germany",
    "match_score": 0.85,
})

FAKE_EMAIL_SEQUENCE = json.dumps({
    "locale": "de_DE",
    "emails": [
        {
            "sequence_number": 1,
            "email_type": "company_intro",
            "subject": "Partnerschaft mit SolarTech",
            "body_text": "Sehr geehrte Damen und Herren...",
            "suggested_send_day": 0,
            "personalization_points": ["solar expertise"],
            "cultural_adaptations": ["formal German"],
        },
        {
            "sequence_number": 2,
            "email_type": "product_showcase",
            "subject": "Unsere Produkte",
            "body_text": "Wir möchten Ihnen...",
            "suggested_send_day": 3,
            "personalization_points": [],
            "cultural_adaptations": [],
        },
        {
            "sequence_number": 3,
            "email_type": "partnership_proposal",
            "subject": "Zusammenarbeit",
            "body_text": "Wir würden uns freuen...",
            "suggested_send_day": 7,
            "personalization_points": [],
            "cultural_adaptations": [],
        },
    ],
})


def _initial_state():
    """Minimal initial state to feed into the graph."""
    return {
        "website_url": "https://solartech.de",
        "product_keywords": ["solar inverter", "PV panel"],
        "target_regions": ["Europe"],
        "uploaded_files": [],
        "target_lead_count": 5,
        "max_rounds": 2,
        "enable_email_craft": True,
        "insight": None,
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
        "current_stage": "start",
        "messages": [],
    }


# ── Fake search results (different URLs per call) ──────────────────────

_search_call_count = {"n": 0}


def _make_search_results(query, **kwargs):
    """Return unique fake search results per call."""
    _search_call_count["n"] += 1
    n = _search_call_count["n"]
    return [
        {"title": f"Company {n}a", "link": f"https://company{n}a.com", "snippet": "...", "position": 1},
        {"title": f"Company {n}b", "link": f"https://company{n}b.com", "snippet": "...", "position": 2},
    ]


class TestE2EPipeline:
    """Full pipeline E2E test with mocked external services."""

    @pytest.mark.asyncio
    async def test_full_pipeline_single_round(self):
        """Run the full pipeline: insight → keywords → search → extract → evaluate → email.

        With target_lead_count=5 and enough fake leads, the pipeline should
        complete in 1-2 rounds and produce email sequences.
        """
        _search_call_count["n"] = 0

        # Track which LLM calls are made to return appropriate responses
        llm_call_count = {"n": 0}

        async def smart_llm_generate(prompt, **kwargs):
            """Route LLM responses based on the system prompt content."""
            system = kwargs.get("system", "")
            llm_call_count["n"] += 1

            if "market analyst" in system.lower():
                return FAKE_INSIGHT
            elif "keyword strategist" in system.lower():
                return FAKE_KEYWORDS
            elif "lead extraction" in system.lower():
                return FAKE_LEAD_VALID
            elif "email copywriter" in system.lower():
                return FAKE_EMAIL_SEQUENCE
            else:
                return json.dumps({"result": "unknown"})

        # ── Patch all external services ─────────────────────────────────
        with patch("agents.insight_agent.react_loop", return_value=FAKE_INSIGHT) as MockReactInsight, \
             patch("agents.insight_agent.JinaReaderTool") as MockJinaInsight, \
             patch("agents.insight_agent.GoogleSearchTool") as MockGoogleInsight, \
             patch("agents.keyword_gen_agent.LLMTool") as MockLLMKeyword, \
             patch("agents.keyword_gen_agent.get_settings") as mock_kw_settings, \
             patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_search_settings, \
             patch("agents.lead_extract_agent.JinaReaderTool") as MockJinaLead, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLMLead, \
             patch("agents.lead_extract_agent.react_loop", return_value=FAKE_LEAD_VALID) as MockReact, \
             patch("agents.lead_extract_agent.get_settings") as mock_lead_settings, \
             patch("agents.email_craft_agent.LLMTool") as MockLLMEmail, \
             patch("agents.email_craft_agent.get_settings") as mock_email_settings:

            # ── InsightAgent mocks ──────────────────────────────────────
            MockJinaInsight.return_value = AsyncMock(close=AsyncMock())
            MockGoogleInsight.return_value = AsyncMock(close=AsyncMock())

            # ── KeywordGenAgent mocks ───────────────────────────────────
            mock_kw_settings.return_value.default_keywords_per_round = 5

            llm_keyword = AsyncMock()
            llm_keyword.generate = smart_llm_generate
            llm_keyword.close = AsyncMock()
            MockLLMKeyword.return_value = llm_keyword

            # ── SearchAgent mocks ───────────────────────────────────────
            mock_search_settings.return_value.search_concurrency = 5

            search_inst = AsyncMock()
            search_inst.search = AsyncMock(side_effect=_make_search_results)
            search_inst.close = AsyncMock()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst

            maps_inst = AsyncMock()
            maps_inst.search = AsyncMock(return_value=[])
            maps_inst.close = AsyncMock()
            MockMaps.return_value = maps_inst

            platform_inst = MagicMock()
            platform_inst.build_queries = MagicMock(return_value=[])
            platform_inst.match = MagicMock(return_value=[])
            MockPlatform.return_value = platform_inst

            # ── LeadExtractAgent mocks ──────────────────────────────────
            mock_lead_settings.return_value.scrape_concurrency = 5

            jina_lead = AsyncMock()
            jina_lead.read = AsyncMock(return_value="# EnergieDist GmbH\nWe are a leading energy distributor in Germany specializing in solar products and renewable energy equipment for commercial installations.")
            jina_lead.close = AsyncMock()
            MockJinaLead.return_value = jina_lead

            llm_lead = AsyncMock()
            llm_lead.generate = smart_llm_generate
            llm_lead.close = AsyncMock()
            MockLLMLead.return_value = llm_lead

            # ── EmailCraftAgent mocks ───────────────────────────────────
            mock_email_settings.return_value.email_gen_concurrency = 3

            llm_email = AsyncMock()
            llm_email.generate = smart_llm_generate
            llm_email.close = AsyncMock()
            MockLLMEmail.return_value = llm_email

            # ── Build and run graph ─────────────────────────────────────
            graph = build_graph(
                insight_node=insight_node,
                keyword_gen_node=keyword_gen_node,
                search_node=search_node,
                lead_extract_node=lead_extract_node,
                evaluate_node=evaluate_progress,
                should_continue_fn=should_continue_hunting,
                email_craft_node=email_craft_node,
            )

            initial = _initial_state()
            result = await graph.ainvoke(initial)

        # ── Assertions ──────────────────────────────────────────────────
        # 1. Insight was generated
        assert result["insight"] is not None
        assert result["insight"]["company_name"] == "SolarTech GmbH"

        # 2. Keywords were generated
        assert len(result["used_keywords"]) > 0

        # 3. Search results were collected
        assert len(result["search_results"]) > 0

        # 4. Leads were extracted
        assert len(result["leads"]) > 0

        # 5. Email sequences were generated
        assert len(result["email_sequences"]) > 0

        # 6. Each email sequence has 3 emails
        for seq in result["email_sequences"]:
            assert len(seq["emails"]) == 3
            assert seq["locale"] is not None

        # 7. Pipeline completed (current_stage should be email_craft)
        assert result["current_stage"] == "email_craft"

        # 8. Round feedback was generated
        assert result["round_feedback"] is not None

    @pytest.mark.asyncio
    async def test_pipeline_with_no_leads_still_completes(self):
        """If no valid leads are found, pipeline should still complete gracefully."""
        _search_call_count["n"] = 0

        invalid_lead = json.dumps({
            "is_valid_lead": False,
            "company_name": "",
            "match_score": 0.0,
        })

        with patch("agents.insight_agent.react_loop", return_value=FAKE_INSIGHT) as MockReactInsight2, \
             patch("agents.insight_agent.JinaReaderTool") as MockJinaInsight, \
             patch("agents.insight_agent.GoogleSearchTool") as MockGoogleInsight2, \
             patch("agents.keyword_gen_agent.LLMTool") as MockLLMKeyword, \
             patch("agents.keyword_gen_agent.get_settings") as mock_kw_settings, \
             patch("agents.search_agent.WebSearchTool") as MockSearch, \
             patch("agents.search_agent.GoogleMapsSearchTool") as MockMaps2, \
             patch("agents.search_agent.PlatformRegistryTool") as MockPlatform, \
             patch("agents.search_agent.get_settings") as mock_search_settings, \
             patch("agents.lead_extract_agent.JinaReaderTool") as MockJinaLead, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLMLead, \
             patch("agents.lead_extract_agent.react_loop", return_value=json.dumps({"is_valid_lead": False, "emails": [], "phone_numbers": [], "social_media": {}, "match_score": 0.0})) as MockReact2, \
             patch("agents.lead_extract_agent.get_settings") as mock_lead_settings, \
             patch("agents.email_craft_agent.LLMTool") as MockLLMEmail, \
             patch("agents.email_craft_agent.get_settings") as mock_email_settings:

            # InsightAgent
            MockJinaInsight.return_value = AsyncMock(close=AsyncMock())
            MockGoogleInsight2.return_value = AsyncMock(close=AsyncMock())

            # KeywordGenAgent
            mock_kw_settings.return_value.default_keywords_per_round = 5
            llm_keyword = AsyncMock()
            llm_keyword.generate = AsyncMock(return_value=FAKE_KEYWORDS)
            llm_keyword.close = AsyncMock()
            MockLLMKeyword.return_value = llm_keyword

            # SearchAgent
            mock_search_settings.return_value.search_concurrency = 5
            search_inst = AsyncMock()
            search_inst.search = AsyncMock(side_effect=_make_search_results)
            search_inst.close = AsyncMock()
            search_inst.backend = "brave"
            MockSearch.return_value = search_inst

            maps_inst2 = AsyncMock()
            maps_inst2.search = AsyncMock(return_value=[])
            maps_inst2.close = AsyncMock()
            MockMaps2.return_value = maps_inst2

            platform_inst = MagicMock()
            platform_inst.build_queries = MagicMock(return_value=[])
            platform_inst.match = MagicMock(return_value=[])
            MockPlatform.return_value = platform_inst

            # LeadExtractAgent — all leads invalid
            mock_lead_settings.return_value.scrape_concurrency = 5
            jina_lead = AsyncMock()
            jina_lead.read = AsyncMock(return_value="# Random Blog Post\nThis is just a blog post about solar energy trends and market analysis for the upcoming year in Europe.")
            jina_lead.close = AsyncMock()
            MockJinaLead.return_value = jina_lead

            llm_lead = AsyncMock()
            llm_lead.generate = AsyncMock(return_value=invalid_lead)
            llm_lead.close = AsyncMock()
            MockLLMLead.return_value = llm_lead

            # EmailCraftAgent
            mock_email_settings.return_value.email_gen_concurrency = 3
            llm_email = AsyncMock()
            llm_email.generate = AsyncMock(return_value=FAKE_EMAIL_SEQUENCE)
            llm_email.close = AsyncMock()
            MockLLMEmail.return_value = llm_email

            graph = build_graph(
                insight_node=insight_node,
                keyword_gen_node=keyword_gen_node,
                search_node=search_node,
                lead_extract_node=lead_extract_node,
                evaluate_node=evaluate_progress,
                should_continue_fn=should_continue_hunting,
                email_craft_node=email_craft_node,
            )

            initial = _initial_state()
            initial["max_rounds"] = 2
            result = await graph.ainvoke(initial)

        # Pipeline should complete even with no leads
        assert result["current_stage"] == "email_craft"
        assert result["insight"] is not None
        assert len(result["leads"]) == 0
        assert result["email_sequences"] == []
