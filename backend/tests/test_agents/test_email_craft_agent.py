"""Tests for agents/email_craft_agent.py — ReAct-based email gen, locale mapping, multi-language."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.email_craft_agent import (
    email_craft_node, _craft_for_lead, _get_locale,
    _get_locale_rules, _build_email_tools,
)
from emailing.template_pipeline import build_fallback_template_profile
import asyncio


FAKE_EMAIL_RESPONSE = json.dumps({
    "locale": "de_DE",
    "emails": [
        {
            "sequence_number": 1,
            "email_type": "company_intro",
            "subject": "Partnerschaft mit SolarTech",
            "body_text": (
                "Sehr geehrte Damen und Herren, wir freuen uns, Ihnen SolarTech GmbH vorzustellen, "
                "einen führenden Hersteller von Solarwechselrichtern und PV-Modulen. Unsere Produkte "
                "zeichnen sich durch höchste Qualität und Zuverlässigkeit aus. Wir sind überzeugt, "
                "dass eine Zusammenarbeit mit Ihrem Unternehmen für beide Seiten sehr vorteilhaft wäre. "
                "Gerne stellen wir Ihnen unser vollständiges Produktportfolio vor. Mit freundlichen Grüßen."
            ),
            "suggested_send_day": 0,
            "personalization_points": ["solar inverter expertise"],
            "cultural_adaptations": ["formal German greeting with Sie"],
        },
        {
            "sequence_number": 2,
            "email_type": "product_showcase",
            "subject": "Unsere Solarwechselrichter — Technische Details",
            "body_text": (
                "Sehr geehrte Damen und Herren, in dieser E-Mail möchten wir Ihnen unsere neueste "
                "Produktlinie im Detail vorstellen. Unsere Solarwechselrichter der Serie SX-5000 "
                "zeichnen sich durch hohe Effizienz von bis zu 98,5 Prozent und eine Lebensdauer "
                "von über 25 Jahren aus. Wir bieten umfassenden technischen Support und eine "
                "europaweite Garantie. Gerne senden wir Ihnen detaillierte technische Unterlagen. "
                "Mit freundlichen Grüßen, Ihr SolarTech-Team."
            ),
            "suggested_send_day": 3,
            "personalization_points": ["energy distribution focus"],
            "cultural_adaptations": ["technical detail emphasis for German market"],
        },
        {
            "sequence_number": 3,
            "email_type": "partnership_proposal",
            "subject": "Vorschlag zur Zusammenarbeit",
            "body_text": (
                "Sehr geehrte Damen und Herren, nach unseren bisherigen Gesprächen möchten wir Ihnen "
                "einen konkreten Partnerschaftsvorschlag unterbreiten. Als autorisierter Distributor "
                "von SolarTech GmbH würden Sie von exklusiven Konditionen, umfangreichem Marketing-Support "
                "und technischer Schulung profitieren. Wir sind überzeugt, dass eine langfristige "
                "Zusammenarbeit für beide Seiten sehr vorteilhaft wäre. Bitte teilen Sie uns Ihren "
                "Terminwunsch für ein erstes Gespräch mit. Mit freundlichen Grüßen."
            ),
            "suggested_send_day": 7,
            "personalization_points": ["distribution network"],
            "cultural_adaptations": ["formal closing with Mit freundlichen Grüßen"],
        },
    ],
})


def _base_state(**overrides):
    base = {
        "website_url": "https://solartech.de",
        "product_keywords": ["solar inverter"],
        "target_regions": ["Europe"],
        "uploaded_files": [],
        "target_lead_count": 200,
        "max_rounds": 10,
        "enable_email_craft": True,
        "insight": {
            "company_name": "SolarTech GmbH",
            "products": ["solar inverter", "PV panel"],
            "industries": ["Renewable Energy"],
        },
        "keywords": [],
        "used_keywords": [],
        "search_results": [],
        "matched_platforms": [],
        "keyword_search_stats": {},
        "leads": [
            {
                "company_name": "EnergieDist GmbH",
                "website": "https://energiedist.de",
                "industry": "Energy Distribution",
                "description": "German energy distributor",
                "emails": ["info@energiedist.de"],
                "contact_person": "Hans Mueller",
                "match_score": 0.9,
                "source": "energiedist.de",
                "country_code": "de",
                "source_keyword": "solar distributor",
            },
            {
                "company_name": "SunPower France",
                "website": "https://sunpower.fr",
                "industry": "Solar",
                "description": "French solar panel distributor",
                "emails": ["contact@sunpower.fr"],
                "contact_person": None,
                "match_score": 0.8,
                "source": "sunpower.fr",
                "country_code": "fr",
                "source_keyword": "solar distributor",
            },
        ],
        "email_sequences": [],
        "email_template_examples": [],
        "email_template_notes": "",
        "hunt_round": 3,
        "prev_round_lead_count": 2,
        "round_feedback": None,
        "current_stage": "evaluate",
        "messages": [],
    }
    base.update(overrides)
    return base


class TestGetLocale:
    def test_german(self):
        assert _get_locale("de") == "de_DE"

    def test_french(self):
        assert _get_locale("fr") == "fr_FR"

    def test_japanese(self):
        assert _get_locale("jp") == "ja_JP"
        assert _get_locale("ja") == "ja_JP"

    def test_chinese(self):
        assert _get_locale("cn") == "zh_CN"
        assert _get_locale("tw") == "zh_TW"

    def test_unknown_defaults_to_en_us(self):
        assert _get_locale("xx") == "en_US"
        assert _get_locale("") == "en_US"

    def test_case_insensitive(self):
        assert _get_locale("DE") == "de_DE"
        assert _get_locale("Fr") == "fr_FR"

    def test_eastern_europe(self):
        assert _get_locale("pl") == "pl_PL"
        assert _get_locale("cz") == "cs_CZ"
        assert _get_locale("ro") == "ro_RO"
        assert _get_locale("hu") == "hu_HU"

    def test_middle_east(self):
        assert _get_locale("sa") == "ar_SA"
        assert _get_locale("ae") == "ar_AE"


class TestGetLocaleRules:
    def test_german_rules(self):
        rules = _get_locale_rules("de_DE")
        assert rules["language"] == "German"
        assert rules["formality"] == "formal"
        assert "Sie" in " ".join(rules["checks"])

    def test_japanese_rules(self):
        rules = _get_locale_rules("ja_JP")
        assert rules["language"] == "Japanese"
        assert rules["script"] == "japanese"
        assert "keigo" in " ".join(rules["checks"])

    def test_chinese_traditional_rules(self):
        rules = _get_locale_rules("zh_TW")
        assert rules["language"] == "Chinese (Traditional)"

    def test_chinese_simplified_rules(self):
        rules = _get_locale_rules("zh_CN")
        assert rules["language"] == "Chinese (Simplified)"

    def test_arabic_rules(self):
        rules = _get_locale_rules("ar_SA")
        assert rules["language"] == "Arabic"
        assert rules["script"] == "arabic"

    def test_unknown_falls_back_to_english(self):
        rules = _get_locale_rules("xx_XX")
        assert rules["language"] == "English"


class TestValidateEmailsTool:
    @pytest.mark.asyncio
    async def test_valid_emails_pass_structural_checks(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "passed": True, "language_correct": True,
            "formality_correct": True, "salutation_correct": True,
            "issues": [], "suggestions": [],
        }))
        tools = _build_email_tools(llm, "de_DE")
        validate_fn = tools[0].fn

        result = json.loads(await validate_fn(emails_json=FAKE_EMAIL_RESPONSE))
        assert result["passed"] is True
        assert result["language"] == "German"

    @pytest.mark.asyncio
    async def test_wrong_email_count_fails(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "passed": True, "language_correct": True,
            "formality_correct": True, "salutation_correct": True,
            "issues": [], "suggestions": [],
        }))
        tools = _build_email_tools(llm, "de_DE")
        validate_fn = tools[0].fn

        only_two = json.dumps({"emails": [
            {"sequence_number": 1, "email_type": "company_intro",
             "subject": "Test", "body_text": "A " * 60,
             "suggested_send_day": 0, "personalization_points": [], "cultural_adaptations": []},
            {"sequence_number": 2, "email_type": "product_showcase",
             "subject": "Test2", "body_text": "B " * 60,
             "suggested_send_day": 3, "personalization_points": [], "cultural_adaptations": []},
        ]})
        result = json.loads(await validate_fn(emails_json=only_two))
        assert result["passed"] is False
        assert any("3 emails" in issue for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_short_body_fails(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "passed": True, "language_correct": True,
            "formality_correct": True, "salutation_correct": True,
            "issues": [], "suggestions": [],
        }))
        tools = _build_email_tools(llm, "en_US")
        validate_fn = tools[0].fn

        short_emails = json.dumps({"emails": [
            {"sequence_number": 1, "email_type": "company_intro",
             "subject": "Hi", "body_text": "Too short.",
             "suggested_send_day": 0, "personalization_points": [], "cultural_adaptations": []},
            {"sequence_number": 2, "email_type": "product_showcase",
             "subject": "Products", "body_text": "Also short.",
             "suggested_send_day": 3, "personalization_points": [], "cultural_adaptations": []},
            {"sequence_number": 3, "email_type": "partnership_proposal",
             "subject": "Partner", "body_text": "Short too.",
             "suggested_send_day": 7, "personalization_points": [], "cultural_adaptations": []},
        ]})
        result = json.loads(await validate_fn(emails_json=short_emails))
        assert result["passed"] is False
        assert any("too short" in issue for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_empty_input_fails(self):
        llm = AsyncMock()
        tools = _build_email_tools(llm, "en_US")
        validate_fn = tools[0].fn

        result = json.loads(await validate_fn(emails_json=""))
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_tool_name_and_description(self):
        llm = AsyncMock()
        tools = _build_email_tools(llm, "ja_JP")
        assert len(tools) == 1
        assert tools[0].name == "validate_emails"
        assert "Japanese" in tools[0].description


class TestCraftForLead:
    def test_build_fallback_template_profile_prefers_examples(self):
        profile = build_fallback_template_profile(
            examples=["Subject: Quick intro\nHello, we noticed your industrial sourcing footprint."],
            lead={"company_name": "Acme", "industry": "Industrial Supply"},
            insight={"products": ["switch", "sensor"]},
        )
        assert profile["source"] == "user_examples"
        assert profile["example_signals"]

    @pytest.mark.asyncio
    async def test_generates_email_sequence_via_react(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        llm.generate = AsyncMock()
        llm.close = AsyncMock()

        lead = {
            "company_name": "EnergieDist",
            "website": "https://energiedist.de",
            "industry": "Energy",
            "country_code": "de",
            "emails": ["info@energiedist.de"],
        }
        insight = {"company_name": "SolarTech", "products": ["solar inverter"]}

        with patch("agents.email_craft_agent.react_loop", return_value=FAKE_EMAIL_RESPONSE):
            result = await _craft_for_lead(lead, insight, llm, sem)

        assert result is not None
        assert result["locale"] == "de_DE"
        assert len(result["emails"]) == 3
        assert result["lead"]["company_name"] == "EnergieDist"

    @pytest.mark.asyncio
    async def test_react_loop_failure_returns_none(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()

        lead = {"company_name": "X", "country_code": "us"}

        with patch("agents.email_craft_agent.react_loop", side_effect=Exception("API error")):
            result = await _craft_for_lead(lead, {}, llm, sem)

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_json_from_react_returns_none(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()

        lead = {"company_name": "X", "country_code": "us"}

        with patch("agents.email_craft_agent.react_loop", return_value="not json at all"):
            result = await _craft_for_lead(lead, {}, llm, sem)

        assert result is None

    @pytest.mark.asyncio
    async def test_react_called_with_required_fields(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Test", "country_code": "fr", "emails": []}
        insight = {"company_name": "MyCompany", "products": ["widget"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture):
            await _craft_for_lead(lead, insight, llm, sem)

        assert "required_json_fields" in captured
        assert "locale" in captured["required_json_fields"]
        assert "emails" in captured["required_json_fields"]

    @pytest.mark.asyncio
    async def test_locale_injected_into_prompt(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Polska Firma", "country_code": "pl", "emails": []}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture):
            await _craft_for_lead(lead, insight, llm, sem)

        assert "pl_PL" in captured.get("user_prompt", "")
        assert "Polish" in captured.get("user_prompt", "")

    @pytest.mark.asyncio
    async def test_user_examples_are_injected_into_prompt(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Acme", "country_code": "us", "emails": []}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture):
            await _craft_for_lead(
                lead,
                insight,
                llm,
                sem,
                email_template_examples=["Subject: Quick intro\nWe noticed your sourcing footprint."],
                email_template_notes="Keep it short and direct.",
            )

        prompt = captured.get("user_prompt", "")
        assert "Template source: user_examples" in prompt
        assert "Keep it short and direct." in prompt
        assert "Template profile:" in prompt
        assert "Template plan:" in prompt

    @pytest.mark.asyncio
    async def test_auto_template_mode_without_examples(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Acme", "country_code": "us", "emails": []}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture):
            result = await _craft_for_lead(lead, insight, llm, sem)

        assert result is not None
        assert result["template_profile"]["source"] == "auto_generated"
        assert "Template source: auto_generated" in captured.get("user_prompt", "")

    @pytest.mark.asyncio
    async def test_distinct_example_styles_produce_distinct_template_outputs(self):
        sem = asyncio.Semaphore(3)
        captured = {}

        class StubLLM:
            async def generate(self, prompt, **kwargs):
                system = kwargs.get("system", "")
                if "extract a reusable style/template profile" in system.lower():
                    if "warm relationship-first" in prompt.lower():
                        return json.dumps({
                            "tone": "warm",
                            "subject_style": "soft and relationship-first",
                            "cta_style": "invite a friendly exploratory reply",
                        })
                    return json.dumps({
                        "tone": "direct",
                        "subject_style": "short and commercially direct",
                        "cta_style": "ask a sharp qualification question",
                    })
                if "design a reusable outbound email template plan" in system.lower():
                    if '"tone": "warm"' in prompt:
                        return json.dumps({
                            "recipient_profile": "Relationship-driven distributor",
                            "cta_strategy": "Invite a brief exploratory conversation.",
                            "template_instructions": ["Lead with rapport", "Use softer CTA"],
                        })
                    return json.dumps({
                        "recipient_profile": "Commercially driven buyer",
                        "cta_strategy": "Ask whether they own this category.",
                        "template_instructions": ["Lead with concrete fit", "Use direct CTA"],
                    })
                raise AssertionError(f"Unexpected system prompt: {system}")

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Acme", "country_code": "us", "emails": []}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture):
            warm_result = await _craft_for_lead(
                lead,
                insight,
                StubLLM(),
                sem,
                email_template_examples=["Warm relationship-first note with softer opener."],
            )
            warm_prompt = captured["user_prompt"]
            captured.clear()
            direct_result = await _craft_for_lead(
                lead,
                insight,
                StubLLM(),
                sem,
                email_template_examples=["Direct commercial note with fast qualification CTA."],
            )
            direct_prompt = captured["user_prompt"]

        assert warm_result["template_profile"]["tone"] == "warm"
        assert direct_result["template_profile"]["tone"] == "direct"
        assert warm_result["template_plan"]["cta_strategy"] == "Invite a brief exploratory conversation."
        assert direct_result["template_plan"]["cta_strategy"] == "Ask whether they own this category."
        assert '"tone": "warm"' in warm_prompt
        assert '"tone": "direct"' in direct_prompt
        assert "Use softer CTA" in warm_prompt
        assert "Use direct CTA" in direct_prompt


class TestEmailCraftNode:
    @pytest.mark.asyncio
    async def test_generates_sequences_for_all_leads(self):
        state = _base_state()

        with patch("agents.email_craft_agent.LLMTool") as MockLLM, \
             patch("agents.email_craft_agent.get_settings") as mock_settings, \
             patch("agents.email_craft_agent.react_loop", return_value=FAKE_EMAIL_RESPONSE):

            mock_settings.return_value.email_gen_concurrency = 3
            mock_settings.return_value.react_max_iterations = 3

            llm_inst = AsyncMock()
            llm_inst.generate = AsyncMock()
            llm_inst.close = AsyncMock()
            MockLLM.return_value = llm_inst

            result = await email_craft_node(state)

        assert result["current_stage"] == "email_craft"
        assert len(result["email_sequences"]) == 2

    @pytest.mark.asyncio
    async def test_state_level_template_examples_are_forwarded(self):
        state = _base_state(
            email_template_examples=["Subject: Fit for your product line\nHi there, we noticed your market coverage."],
            email_template_notes="Use concise English.",
        )
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        with patch("agents.email_craft_agent.LLMTool") as MockLLM, \
             patch("agents.email_craft_agent.get_settings") as mock_settings, \
             patch("agents.email_craft_agent.react_loop", side_effect=capture):

            mock_settings.return_value.email_gen_concurrency = 1
            mock_settings.return_value.react_max_iterations = 3

            llm_inst = AsyncMock()
            llm_inst.generate = AsyncMock()
            llm_inst.close = AsyncMock()
            MockLLM.return_value = llm_inst

            await email_craft_node(state)

        assert "Template source: user_examples" in captured.get("user_prompt", "")
        assert "Use concise English." in captured.get("user_prompt", "")

    @pytest.mark.asyncio
    async def test_empty_leads_returns_empty(self):
        state = _base_state(leads=[])
        result = await email_craft_node(state)
        assert result["email_sequences"] == []
        assert result["current_stage"] == "email_craft"

    @pytest.mark.asyncio
    async def test_partial_failure_still_returns_successes(self):
        state = _base_state()
        call_count = {"n": 0}

        async def alternating(**kwargs):
            call_count["n"] += 1
            if call_count["n"] % 2 == 0:
                raise Exception("API error")
            return FAKE_EMAIL_RESPONSE

        with patch("agents.email_craft_agent.LLMTool") as MockLLM, \
             patch("agents.email_craft_agent.get_settings") as mock_settings, \
             patch("agents.email_craft_agent.react_loop", side_effect=alternating):

            mock_settings.return_value.email_gen_concurrency = 3
            mock_settings.return_value.react_max_iterations = 3

            llm_inst = AsyncMock()
            llm_inst.close = AsyncMock()
            MockLLM.return_value = llm_inst

            result = await email_craft_node(state)

        assert len(result["email_sequences"]) == 1

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """Verify multiple leads are processed concurrently."""
        leads = [
            {"company_name": f"Lead{i}", "country_code": "us",
             "website": f"https://lead{i}.com", "emails": []}
            for i in range(5)
        ]
        state = _base_state(leads=leads)
        react_call_count = {"n": 0}

        async def count_calls(**kwargs):
            react_call_count["n"] += 1
            return FAKE_EMAIL_RESPONSE

        with patch("agents.email_craft_agent.LLMTool") as MockLLM, \
             patch("agents.email_craft_agent.get_settings") as mock_settings, \
             patch("agents.email_craft_agent.react_loop", side_effect=count_calls):

            mock_settings.return_value.email_gen_concurrency = 3
            mock_settings.return_value.react_max_iterations = 3

            llm_inst = AsyncMock()
            llm_inst.close = AsyncMock()
            MockLLM.return_value = llm_inst

            result = await email_craft_node(state)

        assert len(result["email_sequences"]) == 5
        assert react_call_count["n"] == 5
