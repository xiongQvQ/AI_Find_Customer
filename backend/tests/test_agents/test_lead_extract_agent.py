"""Tests for agents/lead_extract_agent.py — ReAct-based extraction, dedup, node integration."""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from agents.lead_extract_agent import lead_extract_node, _scrape_and_extract, _verify_lead_emails, _apply_evidence_to_scores, _quick_gate_candidate, _has_concrete_customs_data, _normalize_decision_maker_emails, _is_generic_mailbox
import asyncio


def _base_state(**overrides):
    base = {
        "website_url": "https://solartech.de",
        "product_keywords": ["solar inverter"],
        "target_regions": ["Europe"],
        "uploaded_files": [],
        "target_lead_count": 200,
        "max_rounds": 10,
        "insight": {
            "products": ["solar inverter", "PV panel"],
            "industries": ["Renewable Energy"],
            "target_customer_profile": "B2B distributors in Europe",
        },
        "keywords": ["solar inverter distributor"],
        "used_keywords": ["solar inverter distributor"],
        "search_results": [
            {"title": "SolarTech", "link": "https://solartech.de/about", "snippet": "...", "source_keyword": "kw1"},
            {"title": "PV Dist", "link": "https://pvdist.com", "snippet": "...", "source_keyword": "kw1"},
        ],
        "matched_platforms": [],
        "keyword_search_stats": {"kw1": {"result_count": 2, "leads_found": 0}},
        "leads": [],
        "email_sequences": [],
        "hunt_round": 1,
        "prev_round_lead_count": 0,
        "round_feedback": None,
        "current_stage": "search",
        "messages": [],
    }
    base.update(overrides)
    return base


VALID_REACT_RESULT = json.dumps({
    "company_name": "SolarTech GmbH",
    "website": "https://solartech.de",
    "industry": "Renewable Energy",
    "description": "Leading solar inverter manufacturer",
    "contact_person": "Hans Mueller",
    "country_code": "de",
    "emails": ["info@solartech.de"],
    "phone_numbers": ["+49 30 12345678"],
    "social_media": {"linkedin": "https://linkedin.com/company/solartech"},
    "address": "Berlin, Germany",
    "match_score": 0.85,
})

INVALID_REACT_RESULT = json.dumps({
    "company_name": "",
    "website": "",
    "industry": "",
    "description": "This is a blog post",
    "contact_person": None,
    "country_code": "",
    "emails": [],
    "phone_numbers": [],
    "social_media": {},
    "match_score": 0.0,
})


class TestScrapeAndExtract:
    """Tests for _scrape_and_extract which delegates to react_loop."""

    @pytest.mark.asyncio
    async def test_valid_lead(self):
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()

        with patch("agents.lead_extract_agent.react_loop", return_value=VALID_REACT_RESULT):
            result = await _scrape_and_extract(
                {"link": "https://solartech.de", "source_keyword": "kw1"},
                jina, llm, sem, insight={"products": ["solar inverter"]}, google_search=google,
            )

        assert result is not None
        assert result["company_name"] == "SolarTech GmbH"
        assert result["match_score"] == 0.85
        assert "info@solartech.de" in result["emails"]
        assert result["source_keyword"] == "kw1"

    @pytest.mark.asyncio
    async def test_invalid_lead_returns_none(self):
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()

        with patch("agents.lead_extract_agent.react_loop", return_value=INVALID_REACT_RESULT):
            result = await _scrape_and_extract(
                {"link": "https://blog.com/post", "source_keyword": "kw1"},
                jina, llm, sem, insight={"products": ["solar inverter"]}, google_search=google,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_react_failure_returns_none(self):
        """When react_loop raises an exception, return None."""
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()

        with patch("agents.lead_extract_agent.react_loop", side_effect=Exception("LLM timeout")):
            result = await _scrape_and_extract(
                {"link": "https://down.com", "source_keyword": "kw1"},
                jina, llm, sem, insight={}, google_search=google,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_json_returns_none(self):
        """When react_loop returns non-JSON, return None."""
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()

        with patch("agents.lead_extract_agent.react_loop", return_value="not valid json at all"):
            result = await _scrape_and_extract(
                {"link": "https://broken.com", "source_keyword": "kw1"},
                jina, llm, sem, insight={}, google_search=google,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_link_returns_none(self):
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()

        result = await _scrape_and_extract(
            {"link": "", "source_keyword": "kw1"},
            jina, llm, sem, insight={}, google_search=google,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_maps_only_result_without_link_is_supported(self):
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()

        with patch("agents.lead_extract_agent.react_loop", return_value=VALID_REACT_RESULT):
            result = await _scrape_and_extract(
                {
                    "title": "SolarTech GmbH",
                    "link": "",
                    "source_keyword": "kw1",
                    "maps_data": {
                        "title": "SolarTech GmbH",
                        "address": "Berlin",
                        "type": "Solar company",
                        "types": ["Solar company"],
                        "website": "https://solartech.de",
                        "phoneNumber": "+49 30 12345678",
                        "description": "Leading solar panel distributor in Berlin.",
                        "email": "info@solartech.de",
                    },
                },
                jina, llm, sem, insight={"products": ["solar inverter"]}, google_search=google,
            )

        assert result is not None
        assert result["company_name"] == "SolarTech GmbH"
        assert result["maps_data"]["address"] == "Berlin"
        assert "info@solartech.de" in result["emails"]

    @pytest.mark.asyncio
    async def test_match_score_clamped(self):
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()

        over_score = json.dumps({
            "is_valid_lead": True,
            "company_name": "OverScore Inc",
            "emails": [],
            "phone_numbers": [],
            "social_media": {},
            "match_score": 1.5,
        })

        with patch("agents.lead_extract_agent.react_loop", return_value=over_score):
            result = await _scrape_and_extract(
                {"link": "https://over.com", "source_keyword": "kw1"},
                jina, llm, sem, insight={}, google_search=google,
            )

        assert result is not None
        assert result["match_score"] == 1.0

    @pytest.mark.asyncio
    async def test_url_type_hint_in_prompt(self):
        """Verify that the user prompt includes URL type hints for the ReAct agent."""
        sem = asyncio.Semaphore(5)
        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()
        captured_kwargs = {}

        async def capture_react_loop(**kwargs):
            captured_kwargs.update(kwargs)
            return VALID_REACT_RESULT

        with patch("agents.lead_extract_agent.react_loop", side_effect=capture_react_loop):
            # LinkedIn URL should get a LinkedIn-specific hint
            await _scrape_and_extract(
                {"link": "https://linkedin.com/company/acme-corp", "source_keyword": "kw1"},
                jina, llm, sem, insight={"products": ["solar"]}, google_search=google,
            )

        assert "LinkedIn" in captured_kwargs["user_prompt"]
        assert "Do NOT" in captured_kwargs["user_prompt"]

    @pytest.mark.asyncio
    async def test_platform_url_type_hint(self):
        """Verify platform URLs get a platform-specific hint."""
        sem = asyncio.Semaphore(5)
        captured_kwargs = {}

        async def capture_react_loop(**kwargs):
            captured_kwargs.update(kwargs)
            return VALID_REACT_RESULT

        with patch("agents.lead_extract_agent.react_loop", side_effect=capture_react_loop):
            await _scrape_and_extract(
                {"link": "https://alibaba.com/supplier/solartech", "source_keyword": "kw1"},
                AsyncMock(), AsyncMock(), sem,
                insight={"products": ["solar"]}, google_search=AsyncMock(),
            )

        assert "platform" in captured_kwargs["user_prompt"].lower()

    @pytest.mark.asyncio
    async def test_react_tools_are_built_with_correct_dependencies(self):
        """Verify that _build_react_tools creates 5 tools including customs lookup."""
        from agents.lead_extract_agent import _build_react_tools

        jina = AsyncMock()
        llm = AsyncMock()
        google = AsyncMock()
        insight = {"products": ["solar inverter"]}

        tools = _build_react_tools(jina, llm, google, insight)

        assert len(tools) == 5
        tool_names = {t.name for t in tools}
        assert tool_names == {"scrape_page", "google_search", "find_customs_data", "extract_lead_info", "assess_lead_fit"}

    @pytest.mark.asyncio
    async def test_react_tool_scrape_page_auto_extracts_contacts(self):
        """Test that scrape_page auto-extracts emails, phones, social from content."""
        from agents.lead_extract_agent import _build_react_tools

        jina = AsyncMock()
        jina.read = AsyncMock(return_value=(
            "# Company Page\nContact us at hello@acmecorp.com or call +1 555 123 4567. "
            "Visit https://linkedin.com/company/acme for more info. "
            "Enough text to pass the minimum length check for scraping."
        ))
        llm = AsyncMock()
        google = AsyncMock()

        tools = _build_react_tools(jina, llm, google, {})
        scrape_tool = next(t for t in tools if t.name == "scrape_page")

        result = await scrape_tool.fn(url="https://example.com")
        parsed = json.loads(result)
        assert "content" in parsed
        assert "hello@acmecorp.com" in parsed["extracted_emails"]
        assert len(parsed["extracted_phones"]) > 0

    @pytest.mark.asyncio
    async def test_react_tool_google_search(self):
        """Test the google_search tool function directly."""
        from agents.lead_extract_agent import _build_react_tools

        google = AsyncMock()
        google.search = AsyncMock(return_value=[
            {"title": "Acme Corp Contact", "link": "https://acmecorp.com/contact", "snippet": "Email: info@acmecorp.com for inquiries"},
        ])

        tools = _build_react_tools(AsyncMock(), AsyncMock(), google, {})
        search_tool = next(t for t in tools if t.name == "google_search")

        result = await search_tool.fn(query="acme corp email")
        parsed = json.loads(result)
        assert len(parsed["results"]) == 1
        assert "info@acmecorp.com" in parsed["contacts_from_snippets"]["emails"]

    @pytest.mark.asyncio
    async def test_react_tool_extract_lead_info(self):
        """Test the extract_lead_info tool function directly."""
        from agents.lead_extract_agent import _build_react_tools

        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=VALID_REACT_RESULT)

        tools = _build_react_tools(AsyncMock(), llm, AsyncMock(), {"products": ["solar"]})
        lead_tool = next(t for t in tools if t.name == "extract_lead_info")

        result = await lead_tool.fn(page_content="Some company page content")
        parsed = json.loads(result)
        assert parsed["company_name"] == "SolarTech GmbH"


class TestQuickGate:
    @pytest.mark.asyncio
    async def test_quick_gate_rejects_non_company_entity(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "pass_gate": False,
            "entity_type": "directory",
            "customer_role_guess": "unknown",
            "competitor_risk": "low",
            "confidence": 0.92,
            "reason": "Directory page, not a real prospect company.",
            "risk_flags": ["directory"],
        }))

        passed, gate = await _quick_gate_candidate(
            {"title": "Industrial Directory Listing", "maps_data": {"description": "Supplier directory"}},
            llm,
            {"products": ["micro switch"]},
        )

        assert passed is False
        assert gate["entity_type"] == "directory"
        assert "directory" in gate["risk_flags"]

    @pytest.mark.asyncio
    async def test_quick_gate_keeps_possible_channel_even_with_competitor_risk(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "pass_gate": True,
            "entity_type": "company",
            "customer_role_guess": "distributor",
            "competitor_risk": "high",
            "confidence": 0.61,
            "reason": "Sells related products but appears to act as distributor/importer.",
            "risk_flags": ["possible_competitor"],
        }))

        passed, gate = await _quick_gate_candidate(
            {"title": "Acme Electrical", "maps_data": {"description": "Distributor of industrial switches"}},
            llm,
            {"products": ["micro switch"]},
        )

        assert passed is True
        assert gate["customer_role_guess"] == "distributor"
        assert gate["competitor_risk"] == "high"

    @pytest.mark.asyncio
    async def test_react_tool_find_customs_data(self):
        """Test the customs router tool function directly."""
        from agents.lead_extract_agent import _build_react_tools

        with patch("agents.lead_extract_agent.route_customs_data", new=AsyncMock(return_value={
            "status": "ok",
            "summary": "importgenius: period 2024; import; partners: Vietnam. Source: https://example.com",
            "evidence": [{"provider": "importgenius", "source_url": "https://example.com"}],
        })):
            tools = _build_react_tools(AsyncMock(), AsyncMock(), AsyncMock(), {"products": ["micro switch"]})
            customs_tool = next(t for t in tools if t.name == "find_customs_data")

            result = await customs_tool.fn(company_name="Acme GmbH", website="https://acme.de", country="Germany")
            parsed = json.loads(result)
            assert parsed["status"] == "ok"
            assert parsed["evidence"][0]["provider"] == "importgenius"


class TestLeadExtractNode:
    @pytest.mark.asyncio
    async def test_extracts_leads(self):
        state = _base_state()

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", return_value=VALID_REACT_RESULT), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings:

            mock_settings.return_value.scrape_concurrency = 5

            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            result = await lead_extract_node(state)

        assert result["current_stage"] == "lead_extract"
        assert len(result["leads"]) > 0

    @pytest.mark.asyncio
    async def test_deduplicates_by_domain(self):
        state = _base_state(search_results=[
            {"link": "https://solartech.de/about", "source_keyword": "kw1"},
            {"link": "https://solartech.de/products", "source_keyword": "kw1"},
        ])

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", return_value=VALID_REACT_RESULT), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings:

            mock_settings.return_value.scrape_concurrency = 5

            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            result = await lead_extract_node(state)

        # Both URLs have same domain solartech.de — should only get 1 lead
        domains = [l["source"] for l in result["leads"]]
        assert domains.count("solartech.de") == 1

    @pytest.mark.asyncio
    async def test_skips_already_extracted_domains(self):
        existing_leads = [{"website": "https://solartech.de/about", "company_name": "SolarTech"}]
        state = _base_state(leads=existing_leads)

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", return_value=VALID_REACT_RESULT), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings:

            mock_settings.return_value.scrape_concurrency = 5

            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            result = await lead_extract_node(state)

        # solartech.de already in leads, only pvdist.com should be processed
        assert any(l.get("company_name") == "SolarTech" for l in result["leads"])

    @pytest.mark.asyncio
    async def test_updates_keyword_stats(self):
        state = _base_state(
            search_results=[
                {"link": "https://newlead.com", "source_keyword": "kw1"},
            ],
            keyword_search_stats={"kw1": {"result_count": 5, "leads_found": 0}},
        )

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", return_value=VALID_REACT_RESULT), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings:

            mock_settings.return_value.scrape_concurrency = 5

            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            result = await lead_extract_node(state)

        assert result["keyword_search_stats"]["kw1"]["leads_found"] >= 1

    @pytest.mark.asyncio
    async def test_does_not_dedupe_by_linkedin_host(self):
        """Different LinkedIn company pages must not be deduped by linkedin.com host."""
        state = _base_state(
            search_results=[
                {"link": "https://linkedin.com/company/acme-a", "source_keyword": "kw1"},
                {"link": "https://linkedin.com/company/acme-b", "source_keyword": "kw1"},
            ]
        )

        async def react_for_linkedin(**kwargs):
            prompt = kwargs.get("user_prompt", "")
            if "acme-a" in prompt:
                return json.dumps({
                    "company_name": "Acme A",
                    "website": "https://linkedin.com/company/acme-a",
                    "industry": "Manufacturing",
                    "description": "A",
                    "emails": ["a@example.com"],
                    "phone_numbers": [],
                    "social_media": {},
                    "match_score": 0.7,
                })
            return json.dumps({
                "company_name": "Acme B",
                "website": "https://linkedin.com/company/acme-b",
                "industry": "Manufacturing",
                "description": "B",
                "emails": ["b@example.com"],
                "phone_numbers": [],
                "social_media": {},
                "match_score": 0.71,
            })

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", side_effect=react_for_linkedin), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings:

            mock_settings.return_value.scrape_concurrency = 5
            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            result = await lead_extract_node(state)

        # Should keep both; no dedupe on linkedin.com host
        assert len(result["leads"]) == 2

    @pytest.mark.asyncio
    async def test_dedupes_platform_results_by_official_website(self):
        """Platform URLs should dedupe only when extracted official website matches."""
        state = _base_state(
            search_results=[
                {"link": "https://thomasnet.com/company/acme-a", "source_keyword": "kw1"},
                {"link": "https://alibaba.com/company/acme-a", "source_keyword": "kw1"},
            ]
        )

        async def react_for_platforms(**kwargs):
            prompt = kwargs.get("user_prompt", "")
            if "thomasnet.com" in prompt:
                return json.dumps({
                    "company_name": "Acme Corp",
                    "website": "https://acme.com",
                    "industry": "Manufacturing",
                    "description": "A",
                    "emails": ["sales@acme.com"],
                    "phone_numbers": [],
                    "social_media": {},
                    "match_score": 0.8,
                })
            return json.dumps({
                "company_name": "Acme Corporation",
                "website": "https://www.acme.com/about",
                "industry": "Manufacturing",
                "description": "B",
                "emails": ["contact@acme.com"],
                "phone_numbers": [],
                "social_media": {},
                "match_score": 0.81,
            })

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", side_effect=react_for_platforms), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings:

            mock_settings.return_value.scrape_concurrency = 5
            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            result = await lead_extract_node(state)

        assert len(result["leads"]) == 1

    @pytest.mark.asyncio
    async def test_empty_search_results(self):
        state = _base_state(search_results=[])
        result = await lead_extract_node(state)
        assert result["current_stage"] == "lead_extract"

    @pytest.mark.asyncio
    async def test_filters_irrelevant_urls(self):
        """Irrelevant URLs (google.com, tiktok.com) should be filtered out."""
        state = _base_state(search_results=[
            {"link": "https://google.com/search?q=solar", "source_keyword": "kw1"},
            {"link": "https://tiktok.com/@solar", "source_keyword": "kw1"},
            {"link": "https://realcompany.com", "source_keyword": "kw1"},
        ])

        call_count = {"n": 0}
        original_valid = VALID_REACT_RESULT

        async def counting_react_loop(**kwargs):
            call_count["n"] += 1
            return original_valid

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", side_effect=counting_react_loop), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings:

            mock_settings.return_value.scrape_concurrency = 5

            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            result = await lead_extract_node(state)

        # Only realcompany.com should be processed, google/tiktok filtered
        assert call_count["n"] == 1


class TestCollectedContactsMerge:
    """Tests for P0-3: Regex-extracted emails are merged into leads."""

    @pytest.mark.asyncio
    async def test_scrape_page_collects_contacts(self):
        """scrape_page tool accumulates Regex-extracted contacts into _collected_contacts."""
        from agents.lead_extract_agent import _build_react_tools

        jina = AsyncMock()
        jina.read = AsyncMock(return_value=(
            "# Company Page\nContact us at hello@acmecorp.com or sales@acmecorp.com. "
            "Call +1 555 123 4567. Visit https://linkedin.com/company/acme. "
            "Enough text to pass the minimum length check for scraping."
        ))
        collected = {"emails": set(), "phones": set(), "social": {}}

        tools = _build_react_tools(
            jina, AsyncMock(), AsyncMock(), {},
            _collected_contacts=collected,
        )
        scrape_tool = next(t for t in tools if t.name == "scrape_page")
        await scrape_tool.fn(url="https://acmecorp.com")

        assert "hello@acmecorp.com" in collected["emails"]
        assert "sales@acmecorp.com" in collected["emails"]
        assert len(collected["phones"]) > 0

    @pytest.mark.asyncio
    async def test_regex_emails_merged_into_lead(self):
        """Even if ReAct JSON omits emails found by Regex, they appear in the final lead."""
        sem = asyncio.Semaphore(5)

        # ReAct returns a valid lead but with EMPTY emails list
        react_result_no_emails = json.dumps({
            "is_valid_lead": True,
            "company_name": "Acme Corp",
            "website": "https://acmecorp.com",
            "industry": "Manufacturing",
            "description": "Test company",
            "emails": [],  # ← ReAct agent omitted the emails!
            "phone_numbers": [],
            "social_media": {},
            "match_score": 0.7,
        })

        # But the Jina scraper found emails in the page content
        jina = AsyncMock()
        jina.read = AsyncMock(return_value=(
            "Contact us at sales@acmecorp.com for inquiries. "
            "This is a long enough text to pass the content length check. "
            "Additional text to ensure we have enough content here."
        ))

        # The key: mock react_loop so it invokes the scrape_page tool
        # (which populates _collected_contacts via closure) before returning.
        async def react_loop_that_scrapes(**kwargs):
            # Find the scrape_page tool from the tools list
            tools = kwargs.get("tools", [])
            scrape_tool = next((t for t in tools if t.name == "scrape_page"), None)
            if scrape_tool:
                await scrape_tool.fn(url="https://acmecorp.com/contact")
            return react_result_no_emails

        with patch("agents.lead_extract_agent.react_loop", side_effect=react_loop_that_scrapes):
            result = await _scrape_and_extract(
                {"link": "https://acmecorp.com/contact", "source_keyword": "kw1"},
                jina, AsyncMock(), sem,
                insight={"products": ["widgets"]},
                google_search=AsyncMock(),
            )

        assert result is not None
        # The Regex-extracted email should be merged in via P0-3
        assert "sales@acmecorp.com" in result["emails"]

    @pytest.mark.asyncio
    async def test_react_loop_called_with_required_fields(self):
        """Verify that _scrape_and_extract passes required_json_fields to react_loop."""
        sem = asyncio.Semaphore(5)
        captured_kwargs = {}

        async def capture_react_loop(**kwargs):
            captured_kwargs.update(kwargs)
            return VALID_REACT_RESULT

        with patch("agents.lead_extract_agent.react_loop", side_effect=capture_react_loop):
            await _scrape_and_extract(
                {"link": "https://example.com", "source_keyword": "kw1"},
                AsyncMock(), AsyncMock(), sem,
                insight={"products": ["solar"]},
                google_search=AsyncMock(),
            )

        assert "required_json_fields" in captured_kwargs
        required = captured_kwargs["required_json_fields"]
        assert "company_name" in required
        assert "emails" in required
        assert "match_score" in required

    @pytest.mark.asyncio
    async def test_build_react_tools_accepts_collected_contacts(self):
        """_build_react_tools works with and without _collected_contacts."""
        from agents.lead_extract_agent import _build_react_tools

        # Without _collected_contacts (backward compat)
        tools = _build_react_tools(AsyncMock(), AsyncMock(), AsyncMock(), {})
        assert len(tools) == 5  # scrape_page, google_search, find_customs_data, extract_lead_info, assess_lead_fit

        # With _collected_contacts
        collected = {"emails": set(), "phones": set(), "social": {}}
        tools = _build_react_tools(
            AsyncMock(), AsyncMock(), AsyncMock(), {},
            _collected_contacts=collected,
        )
        assert len(tools) == 5

    @pytest.mark.asyncio
    async def test_customs_tool_result_merged_into_lead(self):
        """If ReAct calls the customs tool but omits customs_data, post-processing should fill it."""
        sem = asyncio.Semaphore(5)
        react_result_no_customs = json.dumps({
            "company_name": "Acme Corp",
            "website": "https://acme.com",
            "industry": "Manufacturing",
            "description": "Test company",
            "emails": [],
            "phone_numbers": [],
            "social_media": {},
            "customs_data": "No data found",
            "evidence": [],
            "match_score": 0.7,
        })

        async def react_loop_that_calls_customs(**kwargs):
            tools = kwargs.get("tools", [])
            customs_tool = next((t for t in tools if t.name == "find_customs_data"), None)
            if customs_tool:
                await customs_tool.fn(company_name="Acme Corp", website="https://acme.com", country="Germany")
            return react_result_no_customs

        with patch("agents.lead_extract_agent.route_customs_data", new=AsyncMock(return_value={
            "status": "ok",
            "summary": "importgenius: period 2024; import; partners: Vietnam. Source: https://importgenius.com/importers/acme-corp",
            "evidence": [
                {
                    "provider": "importgenius",
                    "source_url": "https://importgenius.com/importers/acme-corp",
                    "trade_direction": "import",
                    "period": "2024",
                    "partner_countries": ["Vietnam"],
                }
            ],
        })), patch("agents.lead_extract_agent.react_loop", side_effect=react_loop_that_calls_customs):
            result = await _scrape_and_extract(
                {"link": "https://acme.com", "source_keyword": "kw1"},
                AsyncMock(), AsyncMock(), sem,
                insight={"products": ["micro switch"]},
                google_search=AsyncMock(),
            )

        assert result is not None
        assert "importgenius" in result["customs_data"]
        assert len(result["customs_records"]) == 1
        assert result["customs_records"][0]["provider"] == "importgenius"
        assert any("importgenius.com/importers/acme-corp" in item["source_url"] for item in result["evidence"])


class TestEmailVerification:
    """Tests for P0-2: Email verification in lead_extract_node."""

    @pytest.mark.asyncio
    async def test_undeliverable_emails_removed(self):
        """lead_extract_node filters out emails with no MX records."""
        state = _base_state(search_results=[
            {"link": "https://newlead.com", "source_keyword": "kw1"},
        ])

        # ReAct returns a lead with two emails
        react_result_with_emails = json.dumps({
            "is_valid_lead": True,
            "company_name": "NewLead Corp",
            "website": "https://newlead.com",
            "industry": "Tech",
            "description": "A tech company",
            "emails": ["valid@newlead.com", "invalid@expired-domain.xyz"],
            "phone_numbers": [],
            "social_media": {},
            "match_score": 0.9,
        })

        # Mock EmailVerifierTool to mark one email as undeliverable
        mock_verify_results = [
            {"email": "valid@newlead.com", "valid_syntax": True, "has_mx": True, "is_deliverable": True, "mx_records": ["mx.newlead.com"]},
            {"email": "invalid@expired-domain.xyz", "valid_syntax": True, "has_mx": False, "is_deliverable": False, "mx_records": []},
        ]

        with patch("agents.lead_extract_agent.JinaReaderTool") as MockJina, \
             patch("agents.lead_extract_agent.LLMTool") as MockLLM, \
             patch("agents.lead_extract_agent.GoogleSearchTool") as MockGoogle, \
             patch("agents.lead_extract_agent.react_loop", return_value=react_result_with_emails), \
             patch("agents.lead_extract_agent.get_settings") as mock_settings, \
             patch("agents.lead_extract_agent.EmailVerifierTool") as MockVerifier:

            mock_settings.return_value.scrape_concurrency = 5
            MockJina.return_value = AsyncMock(close=AsyncMock())
            MockLLM.return_value = AsyncMock(close=AsyncMock())
            MockGoogle.return_value = AsyncMock(close=AsyncMock())

            mock_verifier_instance = AsyncMock()
            mock_verifier_instance.verify_batch = AsyncMock(return_value=mock_verify_results)
            MockVerifier.return_value = mock_verifier_instance

            result = await lead_extract_node(state)

        # Only the deliverable email should remain
        new_leads = [l for l in result["leads"] if l.get("company_name") == "NewLead Corp"]
        assert len(new_leads) == 1
        assert "valid@newlead.com" in new_leads[0]["emails"]
        assert "invalid@expired-domain.xyz" not in new_leads[0]["emails"]


class TestVerifyLeadEmails:
    """Unit tests for the module-level _verify_lead_emails function."""

    @pytest.mark.asyncio
    async def test_removes_undeliverable_emails(self):
        lead = {"company_name": "TestCo", "emails": ["good@test.com", "bad@dead.xyz"]}
        verifier = AsyncMock()
        verifier.verify_batch = AsyncMock(return_value=[
            {"email": "good@test.com", "is_deliverable": True},
            {"email": "bad@dead.xyz", "is_deliverable": False},
        ])
        result = await _verify_lead_emails(lead, verifier)
        assert result["emails"] == ["good@test.com"]

    @pytest.mark.asyncio
    async def test_keeps_all_when_all_deliverable(self):
        lead = {"company_name": "TestCo", "emails": ["a@x.com", "b@x.com"]}
        verifier = AsyncMock()
        verifier.verify_batch = AsyncMock(return_value=[
            {"email": "a@x.com", "is_deliverable": True},
            {"email": "b@x.com", "is_deliverable": True},
        ])
        result = await _verify_lead_emails(lead, verifier)
        assert result["emails"] == ["a@x.com", "b@x.com"]

    @pytest.mark.asyncio
    async def test_no_emails_skips_verification(self):
        lead = {"company_name": "TestCo", "emails": []}
        verifier = AsyncMock()
        verifier.verify_batch = AsyncMock()
        result = await _verify_lead_emails(lead, verifier)
        verifier.verify_batch.assert_not_called()
        assert result["emails"] == []

    @pytest.mark.asyncio
    async def test_verification_error_keeps_original(self):
        lead = {"company_name": "TestCo", "emails": ["a@x.com"]}
        verifier = AsyncMock()
        verifier.verify_batch = AsyncMock(side_effect=Exception("DNS timeout"))
        result = await _verify_lead_emails(lead, verifier)
        # On error, original emails preserved
        assert result["emails"] == ["a@x.com"]

    @pytest.mark.asyncio
    async def test_returns_same_lead_dict(self):
        lead = {"company_name": "TestCo", "emails": ["a@x.com"], "match_score": 0.8}
        verifier = AsyncMock()
        verifier.verify_batch = AsyncMock(return_value=[
            {"email": "a@x.com", "is_deliverable": True},
        ])
        result = await _verify_lead_emails(lead, verifier)
        assert result["match_score"] == 0.8
        assert result["company_name"] == "TestCo"


class TestEvidenceScoring:
    def test_customs_and_contacts_raise_contactability_and_priority(self):
        lead = {
            "company_name": "Acme",
            "match_score": 0.72,
            "fit_score": 0.72,
            "contactability_score": 0.1,
            "priority_tier": "low",
            "emails": ["sales@acme.com"],
            "phone_numbers": ["+49 30 123456"],
            "decision_makers": [{"name": "Jane", "title": "Purchasing Manager", "email": "jane@acme.com"}],
            "customs_data": "importgenius: period 2024; import; partners: Vietnam. Source: https://example.com",
            "evidence": [{"claim": "Customs evidence: import; period 2024", "source_url": "https://example.com"}],
        }

        result = _apply_evidence_to_scores(lead)
        assert result["contactability_score"] > 0.4
        assert result["customs_score"] > 0.5
        assert result["priority_tier"] == "high"

    def test_low_fit_stays_low_even_with_contact_and_customs(self):
        lead = {
            "company_name": "WeakFit",
            "match_score": 0.2,
            "fit_score": 0.2,
            "contactability_score": 0.0,
            "priority_tier": "low",
            "emails": ["info@weakfit.com"],
            "phone_numbers": ["+1 555 0000"],
            "decision_makers": [{"name": "Tom", "title": "Owner", "email": "tom@weakfit.com"}],
            "customs_data": "importgenius: period 2024; import. Source: https://example.com",
            "evidence": [{"claim": "Customs evidence: import", "source_url": "https://example.com"}],
        }

        result = _apply_evidence_to_scores(lead)
        assert result["contactability_score"] > 0.3
        assert result["customs_score"] > 0.4
        assert result["priority_tier"] == "low"

    def test_negative_customs_explanation_does_not_count_as_customs_data(self):
        assert _has_concrete_customs_data("No detailed customs data available through public sources.") is False
        assert _has_concrete_customs_data("No data found - company is an engineering services provider, not an importer/exporter") is False
        assert _has_concrete_customs_data("importgenius: period 2024; import; partners: Vietnam. Source: https://example.com") is True

    def test_negative_customs_text_does_not_raise_customs_score(self):
        lead = {
            "company_name": "Service Co",
            "fit_score": 0.8,
            "contactability_score": 0.2,
            "customs_score": 0.0,
            "priority_tier": "low",
            "emails": [],
            "phone_numbers": [],
            "decision_makers": [],
            "customs_data": "No data available - this is a UK-based service company, not an importer/exporter of goods",
            "evidence": [],
        }
        result = _apply_evidence_to_scores(lead)
        assert result["customs_score"] == 0.0

    @pytest.mark.asyncio
    async def test_negative_customs_text_is_normalized_to_no_data_without_tool_evidence(self):
        sem = asyncio.Semaphore(5)
        react_result_negative_customs = json.dumps({
            "company_name": "Service Co",
            "website": "https://serviceco.com",
            "industry": "Engineering services",
            "description": "Service company",
            "emails": [],
            "phone_numbers": [],
            "social_media": {},
            "customs_data": "No data available - this is a service company, not an importer/exporter of goods",
            "evidence": [],
            "match_score": 0.4,
        })

        with patch("agents.lead_extract_agent.react_loop", return_value=react_result_negative_customs):
            result = await _scrape_and_extract(
                {"link": "https://serviceco.com", "source_keyword": "kw1"},
                AsyncMock(), AsyncMock(), sem,
                insight={"products": ["servo motor"]},
                google_search=AsyncMock(),
            )

        assert result is not None
        assert result["customs_data"] == "No data found"


class TestDecisionMakerEmailInference:
    def test_detects_generic_mailboxes(self):
        assert _is_generic_mailbox("info@acme.com") is True
        assert _is_generic_mailbox("sales.team@acme.com") is True
        assert _is_generic_mailbox("jane.doe@acme.com") is False

    def test_generic_company_mailbox_is_removed_from_decision_maker(self):
        lead = {
            "website": "https://xotechtrading.com",
            "decision_makers": [
                {"name": "Mr. Mohammed", "title": "Managing Director", "email": "info@xotechtrading.com"},
                {"name": "Sales Team", "title": "Sales Department", "email": "sales@xotechtrading.com", "linkedin": "https://linkedin.com/in/sales-team"},
            ],
        }
        result = _normalize_decision_maker_emails(lead)
        assert result["decision_makers"][0]["email"] == ""
        assert result["decision_makers"][1]["email"] == ""
        assert result["decision_makers"][1]["linkedin"] == "https://linkedin.com/in/sales-team"

    def test_inferred_email_without_pattern_evidence_is_removed(self):
        lead = {
            "website": "https://degrenne.fr",
            "decision_makers": [
                {"name": "Francois Degrenne", "title": "Owner/CEO", "email": "francois@degrenne.fr (inferred)"},
            ],
        }
        result = _normalize_decision_maker_emails(lead)
        assert result["decision_makers"][0]["email"] == ""

    def test_inferred_email_uses_real_same_domain_pattern(self):
        lead = {
            "website": "https://acme.com",
            "decision_makers": [
                {"name": "Jane Smith", "title": "Sales Director", "email": "jane.smith@acme.com"},
                {"name": "John Doe", "title": "CEO", "email": "inferred"},
            ],
        }
        result = _normalize_decision_maker_emails(lead)
        assert result["decision_makers"][1]["email"] == "john.doe@acme.com (inferred)"
