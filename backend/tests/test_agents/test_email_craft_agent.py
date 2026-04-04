"""Tests for agents/email_craft_agent.py — ReAct-based email gen, locale mapping, multi-language."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.email_craft_agent import (
    email_craft_node, _craft_for_lead, _get_locale,
    _get_locale_rules, _build_email_tools, _rule_validate_emails_payload,
    _auto_improve_reviewed_sequence,
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

    def test_rule_validator_flags_dense_plaintext_layout(self):
        emails = [
            {
                "sequence_number": 1,
                "email_type": "company_intro",
                "subject": "Potential fit for your switch category",
                "body_text": "Dear Sir/Madam, " + ("relevant industrial switch components for your buyer base " * 18),
                "suggested_send_day": 0,
            },
            {
                "sequence_number": 2,
                "email_type": "product_showcase",
                "subject": "More detail on our switch range",
                "body_text": "Dear Sir/Madam, " + ("common industrial use cases and repeat sourcing needs " * 18),
                "suggested_send_day": 3,
            },
            {
                "sequence_number": 3,
                "email_type": "partnership_proposal",
                "subject": "Should I send a short shortlist?",
                "body_text": "Dear Sir/Madam, " + ("shortlist for your team if this category is relevant " * 18),
                "suggested_send_day": 7,
            },
        ]

        result = _rule_validate_emails_payload(emails)

        assert result["passed"] is False
        assert any("layout lacks paragraph breaks" in issue for issue in result["issues"])

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

    def test_rule_validator_flags_repetition_and_aggressive_cta(self):
        payload = [
            {
                "sequence_number": 1,
                "email_type": "company_intro",
                "subject": "Hello",
                "body_text": "We are a leading provider. " + ("Generic text " * 55),
                "suggested_send_day": 0,
            },
            {
                "sequence_number": 2,
                "email_type": "product_showcase",
                "subject": "Hello",
                "body_text": "We are a leading provider. " + ("Generic text " * 55),
                "suggested_send_day": 3,
            },
            {
                "sequence_number": 3,
                "email_type": "partnership_proposal",
                "subject": "Final notice",
                "body_text": ("Urgent last chance final notice " * 20) + ("You should reply today " * 30),
                "suggested_send_day": 7,
            },
        ]

        result = _rule_validate_emails_payload(payload)
        assert result["passed"] is False
        assert any("subject repeats previous email" in issue for issue in result["issues"])
        assert any("too aggressive" in issue for issue in result["issues"])


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
        llm.generate = AsyncMock(side_effect=[
            json.dumps({
                "chosen_language": "de",
                "chosen_locale": "de_DE",
                "confidence": "high",
                "reason": "German company profile",
                "fallback_used": False,
            }),
            json.dumps({
                "recipient_profile": "German energy distributor",
                "why_this_company_may_fit": ["Distributor in a relevant energy market"],
                "best_value_angles": ["Solar inverter relevance"],
                "product_focus": ["solar inverter"],
                "proof_points_to_use": ["Relevant industry fit"],
                "claims_to_avoid": ["Avoid generic claims"],
                "cta_strategy": "Ask whether they evaluate inverter suppliers",
                "tone_guidance": "Formal and commercially credible",
                "personalization_hooks": ["EnergieDist"],
            }),
        ])
        llm.close = AsyncMock()

        lead = {
            "company_name": "EnergieDist",
            "website": "https://energiedist.de",
            "industry": "Energy",
            "country_code": "de",
            "emails": ["info@energiedist.de"],
        }
        insight = {"company_name": "SolarTech", "products": ["solar inverter"]}

        with patch("agents.email_craft_agent.react_loop", return_value=FAKE_EMAIL_RESPONSE), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_language_mode = "auto_by_region"
            mock_settings.return_value.email_default_language = "en"
            mock_settings.return_value.email_fallback_language = "en"
            mock_settings.return_value.email_review_min_score = 75
            mock_settings.return_value.email_review_max_blocking_issues = 0
            result = await _craft_for_lead(lead, insight, llm, sem)

        assert result is not None
        assert result["locale"] == "de_DE"
        assert len(result["emails"]) == 3
        assert result["lead"]["company_name"] == "EnergieDist"
        assert result["target"]["target_email"] == "info@energiedist.de"
        assert result["review_summary"]["status"] in {"approved", "needs_review"}
        assert "auto_send_eligible" in result

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
    async def test_no_sendable_email_returns_none(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        lead = {"company_name": "X", "country_code": "us", "emails": [], "decision_makers": []}

        result = await _craft_for_lead(lead, {}, llm, sem)
        assert result is None

    @pytest.mark.asyncio
    async def test_react_called_with_required_fields(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "chosen_language": "fr",
            "chosen_locale": "fr_FR",
            "confidence": "high",
            "reason": "public-facing language evidence",
            "fallback_used": False,
        }))
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Test", "country_code": "fr", "emails": ["info@test.fr"]}
        insight = {"company_name": "MyCompany", "products": ["widget"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_language_mode = "auto_by_region"
            mock_settings.return_value.email_default_language = "en"
            mock_settings.return_value.email_fallback_language = "en"
            await _craft_for_lead(lead, insight, llm, sem)

        assert "required_json_fields" in captured
        assert "locale" in captured["required_json_fields"]
        assert "emails" in captured["required_json_fields"]

    @pytest.mark.asyncio
    async def test_locale_injected_into_prompt(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        llm.generate = AsyncMock(side_effect=[
            json.dumps({
                "chosen_language": "pl",
                "chosen_locale": "pl_PL",
                "confidence": "high",
                "reason": "lead content is Polish",
                "fallback_used": False,
            }),
            json.dumps({
                "recipient_profile": "Polish distributor",
                "why_this_company_may_fit": ["Industrial distributor in Poland"],
                "best_value_angles": ["Relevant switch product line"],
                "product_focus": ["switch"],
                "proof_points_to_use": ["Industrial distribution focus"],
                "claims_to_avoid": ["Avoid generic claims"],
                "cta_strategy": "Ask whether they manage sourcing for switches",
                "tone_guidance": "Professional and direct",
                "personalization_hooks": ["Polska Firma"],
            }),
        ])
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Polska Firma", "country_code": "pl", "emails": ["info@polska.pl"]}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_language_mode = "auto_by_region"
            mock_settings.return_value.email_default_language = "en"
            mock_settings.return_value.email_fallback_language = "en"
            await _craft_for_lead(lead, insight, llm, sem)

        assert "pl_PL" in captured.get("user_prompt", "")
        assert "Polish" in captured.get("user_prompt", "")
        assert "Strategy Brief" in captured.get("user_prompt", "")
        assert "Sequence Objectives" in captured.get("user_prompt", "")

    @pytest.mark.asyncio
    async def test_english_only_mode_forces_english_locale(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        llm.generate = AsyncMock(side_effect=Exception("skip selector llm"))
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return json.dumps({
                "locale": "en_US",
                "emails": json.loads(FAKE_EMAIL_RESPONSE)["emails"],
            })

        lead = {"company_name": "Firma Polska", "country_code": "pl", "emails": ["info@firma.pl"]}
        insight = {"company_name": "MyCompany", "products": ["switch"], "value_propositions": [], "industries": []}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_language_mode = "english_only"
            mock_settings.return_value.email_default_language = "en"
            mock_settings.return_value.email_fallback_language = "en"
            result = await _craft_for_lead(lead, insight, llm, sem)

        assert result is not None
        assert result["locale"] == "en_US"
        assert "Language: English" in captured.get("user_prompt", "")

    @pytest.mark.asyncio
    async def test_validation_rewrite_loop_fixes_initial_invalid_output(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        llm.close = AsyncMock()
        llm.generate = AsyncMock(side_effect=[
            json.dumps({
                "chosen_language": "en",
                "chosen_locale": "en_US",
                "confidence": "high",
                "reason": "english_only mode",
                "fallback_used": True,
            }),
            json.dumps({
                "recipient_profile": "US distributor",
                "why_this_company_may_fit": ["Relevant distributor profile"],
                "best_value_angles": ["Relevant product fit"],
                "product_focus": ["switch"],
                "proof_points_to_use": ["Concrete product relevance"],
                "claims_to_avoid": ["Avoid generic claims"],
                "cta_strategy": "Ask a low-friction qualification question",
                "tone_guidance": "Professional and concise",
                "personalization_hooks": ["Acme"],
            }),
            json.dumps({
                "recipient_profile": "US distributor",
                "cta_strategy": "Ask a low-friction qualification question",
                "opening_strategy": "Lead with buyer relevance",
                "proof_points": ["Concrete product relevance"],
            }),
            json.dumps({
                "passed": False,
                "grammar_ok": False,
                "spelling_ok": True,
                "language_correct": True,
                "formality_correct": True,
                "salutation_correct": True,
                "business_etiquette_ok": False,
                "local_naturalness_ok": False,
                "commercial_quality": False,
                "sequence_progression": False,
                "issues": ["Email 1 grammar issue", "Email 2 too generic"],
                "suggestions": ["Fix grammar in Email 1", "Add buyer relevance in Email 2"],
            }),
            json.dumps({
                "locale": "en_US",
                "emails": [
                    {
                        "sequence_number": 1,
                        "email_type": "company_intro",
                        "subject": "Acme sourcing for industrial switches",
                        "body_text": "Dear team, " + ("you and your distribution business could benefit from our switch range. " * 12),
                        "suggested_send_day": 0,
                        "personalization_points": ["Acme distributor profile"],
                        "cultural_adaptations": ["Professional English tone"],
                    },
                    {
                        "sequence_number": 2,
                        "email_type": "product_showcase",
                        "subject": "Relevant switch applications for Acme",
                        "body_text": "Dear team, " + ("your buyers may care about our product fit and proof points. " * 12),
                        "suggested_send_day": 3,
                        "personalization_points": ["Relevant applications"],
                        "cultural_adaptations": ["Buyer-oriented wording"],
                    },
                    {
                        "sequence_number": 3,
                        "email_type": "partnership_proposal",
                        "subject": "Would a quick fit check be useful?",
                        "body_text": "Dear team, " + ("you may let me know whether you handle this category or the right colleague. " * 12),
                        "suggested_send_day": 7,
                        "personalization_points": ["Low-friction CTA"],
                        "cultural_adaptations": ["Polite follow-up"],
                    },
                ],
            }),
            json.dumps({
                "passed": True,
                "grammar_ok": True,
                "spelling_ok": True,
                "language_correct": True,
                "formality_correct": True,
                "salutation_correct": True,
                "business_etiquette_ok": True,
                "local_naturalness_ok": True,
                "commercial_quality": True,
                "sequence_progression": True,
                "issues": [],
                "suggestions": [],
            }),
        ])

        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        insight = {"company_name": "MyCompany", "products": ["switch"], "value_propositions": [], "industries": []}

        with patch("agents.email_craft_agent.react_loop", return_value=json.dumps({
            "locale": "en_US",
            "emails": [
                {
                    "sequence_number": 1,
                    "email_type": "company_intro",
                    "subject": "Hello",
                    "body_text": "bad grammar text",
                    "suggested_send_day": 0,
                    "personalization_points": [],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 2,
                    "email_type": "product_showcase",
                    "subject": "Hello",
                    "body_text": "generic follow up",
                    "suggested_send_day": 3,
                    "personalization_points": [],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 3,
                    "email_type": "partnership_proposal",
                    "subject": "Final notice",
                    "body_text": "urgent final notice",
                    "suggested_send_day": 7,
                    "personalization_points": [],
                    "cultural_adaptations": [],
                },
            ],
        })), patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_language_mode = "english_only"
            mock_settings.return_value.email_default_language = "en"
            mock_settings.return_value.email_fallback_language = "en"
            result = await _craft_for_lead(lead, insight, llm, sem)

        assert result is not None
        assert result["emails"][0]["subject"] == "Acme sourcing for industrial switches"
        assert result["review_status"] == "approved"

    @pytest.mark.asyncio
    async def test_unresolved_validation_marks_needs_review(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        llm.close = AsyncMock()
        llm.generate = AsyncMock(side_effect=[
            json.dumps({
                "chosen_language": "en",
                "chosen_locale": "en_US",
                "confidence": "high",
                "reason": "english_only mode",
                "fallback_used": True,
            }),
            json.dumps({
                "recipient_profile": "US distributor",
                "why_this_company_may_fit": ["Relevant distributor profile"],
                "best_value_angles": ["Relevant product fit"],
                "product_focus": ["switch"],
                "proof_points_to_use": ["Concrete product relevance"],
                "claims_to_avoid": ["Avoid generic claims"],
                "cta_strategy": "Ask a low-friction qualification question",
                "tone_guidance": "Professional and concise",
                "personalization_hooks": ["Acme"],
            }),
            json.dumps({
                "recipient_profile": "US distributor",
                "cta_strategy": "Ask a low-friction qualification question",
                "opening_strategy": "Lead with buyer relevance",
                "proof_points": ["Concrete product relevance"],
            }),
            json.dumps({
                "passed": False,
                "grammar_ok": False,
                "spelling_ok": False,
                "language_correct": False,
                "formality_correct": True,
                "salutation_correct": True,
                "business_etiquette_ok": False,
                "local_naturalness_ok": False,
                "commercial_quality": False,
                "sequence_progression": False,
                "issues": ["Email 1 is unnatural"],
                "suggestions": ["Rewrite Email 1 naturally"],
            }),
            json.dumps({
                "locale": "en_US",
                "emails": [
                    {
                        "sequence_number": 1,
                        "email_type": "company_intro",
                        "subject": "Hello",
                        "body_text": "bad text",
                        "suggested_send_day": 0,
                        "personalization_points": [],
                        "cultural_adaptations": [],
                    },
                    {
                        "sequence_number": 2,
                        "email_type": "product_showcase",
                        "subject": "Hello",
                        "body_text": "bad text",
                        "suggested_send_day": 3,
                        "personalization_points": [],
                        "cultural_adaptations": [],
                    },
                    {
                        "sequence_number": 3,
                        "email_type": "partnership_proposal",
                        "subject": "Hello",
                        "body_text": "bad text",
                        "suggested_send_day": 7,
                        "personalization_points": [],
                        "cultural_adaptations": [],
                    },
                ],
            }),
            json.dumps({
                "passed": False,
                "grammar_ok": False,
                "spelling_ok": False,
                "language_correct": False,
                "formality_correct": True,
                "salutation_correct": True,
                "business_etiquette_ok": False,
                "local_naturalness_ok": False,
                "commercial_quality": False,
                "sequence_progression": False,
                "issues": ["Still unnatural"],
                "suggestions": ["Needs human review"],
            }),
            json.dumps({
                "locale": "en_US",
                "emails": [
                    {
                        "sequence_number": 1,
                        "email_type": "company_intro",
                        "subject": "Hello",
                        "body_text": "bad text",
                        "suggested_send_day": 0,
                        "personalization_points": [],
                        "cultural_adaptations": [],
                    },
                    {
                        "sequence_number": 2,
                        "email_type": "product_showcase",
                        "subject": "Hello",
                        "body_text": "bad text",
                        "suggested_send_day": 3,
                        "personalization_points": [],
                        "cultural_adaptations": [],
                    },
                    {
                        "sequence_number": 3,
                        "email_type": "partnership_proposal",
                        "subject": "Hello",
                        "body_text": "bad text",
                        "suggested_send_day": 7,
                        "personalization_points": [],
                        "cultural_adaptations": [],
                    },
                ],
            }),
            json.dumps({
                "passed": False,
                "grammar_ok": False,
                "spelling_ok": False,
                "language_correct": False,
                "formality_correct": True,
                "salutation_correct": True,
                "business_etiquette_ok": False,
                "local_naturalness_ok": False,
                "commercial_quality": False,
                "sequence_progression": False,
                "issues": ["Still bad after second revision"],
                "suggestions": ["Manual review required"],
            }),
        ])

        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        insight = {"company_name": "MyCompany", "products": ["switch"], "value_propositions": [], "industries": []}

        with patch("agents.email_craft_agent.react_loop", return_value=json.dumps({
            "locale": "en_US",
            "emails": [
                {"sequence_number": 1, "email_type": "company_intro", "subject": "Hello", "body_text": "bad", "suggested_send_day": 0, "personalization_points": [], "cultural_adaptations": []},
                {"sequence_number": 2, "email_type": "product_showcase", "subject": "Hello", "body_text": "bad", "suggested_send_day": 3, "personalization_points": [], "cultural_adaptations": []},
                {"sequence_number": 3, "email_type": "partnership_proposal", "subject": "Hello", "body_text": "bad", "suggested_send_day": 7, "personalization_points": [], "cultural_adaptations": []},
            ],
        })), patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_language_mode = "english_only"
            mock_settings.return_value.email_default_language = "en"
            mock_settings.return_value.email_fallback_language = "en"
            result = await _craft_for_lead(lead, insight, llm, sem)

        assert result is not None
        assert result["review_status"] == "needs_review"
        assert result["validation_summary"]["status"] == "needs_review"

    @pytest.mark.asyncio
    async def test_user_examples_are_injected_into_prompt(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return FAKE_EMAIL_RESPONSE

        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_review_min_score = 75
            mock_settings.return_value.email_review_max_blocking_issues = 0
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

        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_review_min_score = 75
            mock_settings.return_value.email_review_max_blocking_issues = 0
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

        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", side_effect=capture), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_review_min_score = 75
            mock_settings.return_value.email_review_max_blocking_issues = 0
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

    @pytest.mark.asyncio
    async def test_review_gate_blocks_low_quality_sequence(self):
        sem = asyncio.Semaphore(3)
        llm = AsyncMock()
        llm.generate = AsyncMock()
        low_quality = json.dumps({
            "locale": "en_US",
            "emails": [
                {"sequence_number": 1, "email_type": "company_intro", "subject": "", "body_text": "short", "suggested_send_day": 0},
                {"sequence_number": 2, "email_type": "product_showcase", "subject": "Same", "body_text": "short", "suggested_send_day": 2},
                {"sequence_number": 3, "email_type": "partnership_proposal", "subject": "Same", "body_text": "short", "suggested_send_day": 7},
            ],
        })
        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        insight = {"company_name": "MyCompany", "products": ["switch"]}

        with patch("agents.email_craft_agent.react_loop", return_value=low_quality), \
             patch("agents.email_craft_agent.get_settings") as mock_settings:
            mock_settings.return_value.email_review_min_score = 75
            mock_settings.return_value.email_review_max_blocking_issues = 0
            result = await _craft_for_lead(lead, insight, llm, sem)

        assert result is not None
        assert result["review_summary"]["status"] == "needs_review"
        assert result["auto_send_eligible"] is False
        assert result["review_summary"]["issues"]

    @pytest.mark.asyncio
    async def test_review_gate_auto_optimizes_fixable_issues(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "locale": "en_US",
            "emails": [
                {
                    "sequence_number": 1,
                    "email_type": "company_intro",
                    "subject": "Acme partnership idea",
                    "body_text": (
                        "Hi Acme team, we noticed your distribution activity in industrial switching and thought our range "
                        "could be relevant. MyCompany supplies industrial switches for buyers who need stable supply, "
                        "clear specs, and responsive support. If this category is relevant on your side, I can share a "
                        "short overview with target applications and current export support. We already work with overseas "
                        "buyers who value predictable lead times, practical technical documentation, and straightforward "
                        "commercial communication during qualification."
                    ),
                    "suggested_send_day": 0,
                    "personalization_points": ["Acme", "industrial switching"],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 2,
                    "email_type": "product_showcase",
                    "subject": "Acme sourcing fit for industrial switches",
                    "body_text": (
                        "Following up with a bit more detail for Acme. Our switch range covers common industrial use cases, "
                        "with documentation and export coordination designed for distributors who need quick quoting and "
                        "repeatable supply. If useful, I can send a concise spec sheet and product shortlist aligned to the "
                        "kind of accounts your team usually serves. That usually helps partners quickly judge fit without "
                        "wasting time on oversized catalogs or claims that are hard to verify in an early sourcing discussion."
                    ),
                    "suggested_send_day": 3,
                    "personalization_points": ["Acme sourcing fit"],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 3,
                    "email_type": "partnership_proposal",
                    "subject": "Should I send Acme a short product shortlist?",
                    "body_text": (
                        "One last note in case this is relevant for Acme. If your team is reviewing switch suppliers or "
                        "related categories this quarter, I can send a short product shortlist with typical distributor use "
                        "cases and lead times. If not your area, happy to close the loop. If it is relevant, I can also "
                        "suggest a small first list focused on mainstream specifications so your team can evaluate quickly "
                        "without a heavy onboarding step."
                    ),
                    "suggested_send_day": 7,
                    "personalization_points": ["Acme"],
                    "cultural_adaptations": [],
                },
            ],
        }))

        current_sequence = {
            "locale": "en_US",
            "emails": [
                {"sequence_number": 1, "email_type": "company_intro", "subject": "Same", "body_text": "short text only", "suggested_send_day": 0},
                {"sequence_number": 2, "email_type": "product_showcase", "subject": "Same", "body_text": "short text only", "suggested_send_day": 3},
                {"sequence_number": 3, "email_type": "partnership_proposal", "subject": "Same", "body_text": "short text only", "suggested_send_day": 7},
            ],
        }
        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        template_profile = {"tone": "professional", "source": "auto_generated"}
        template_plan = {
            "cta_strategy": "Ask a low-friction qualification question",
            "opening_strategy": "Lead with buyer relevance",
            "value_angle": "Relevant product fit",
        }

        optimized, review_summary, optimization = await _auto_improve_reviewed_sequence(
            llm,
            locale="en_US",
            rules=_get_locale_rules("en_US"),
            user_prompt="Write a concise outbound sequence for Acme.",
            current_sequence=current_sequence,
            lead=lead,
            template_profile=template_profile,
            template_plan=template_plan,
            min_score=75,
            max_blocking_issues=0,
            max_rounds=2,
        )

        assert review_summary["status"] == "approved"
        assert optimization["attempted"] is True
        assert optimization["improved"] is True
        assert "Acme" in optimized["emails"][0]["body_text"]

    @pytest.mark.asyncio
    async def test_review_gate_auto_fix_revalidates_after_rewrite(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=json.dumps({
            "locale": "en_US",
            "emails": [
                {
                    "sequence_number": 1,
                    "email_type": "company_intro",
                    "subject": "Acme partnership idea",
                    "body_text": "This rewritten email now includes enough buyer-specific context for Acme and keeps a clear professional tone for review.",
                    "suggested_send_day": 0,
                    "personalization_points": ["Acme"],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 2,
                    "email_type": "product_showcase",
                    "subject": "Acme sourcing fit",
                    "body_text": "This rewritten follow-up explains product fit for Acme in clearer commercial language and keeps the progression intact.",
                    "suggested_send_day": 3,
                    "personalization_points": ["Acme"],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 3,
                    "email_type": "partnership_proposal",
                    "subject": "Should I send a shortlist?",
                    "body_text": "This rewritten final note keeps the CTA light while staying specific enough for Acme and preserving the three-step sequence.",
                    "suggested_send_day": 7,
                    "personalization_points": ["Acme"],
                    "cultural_adaptations": [],
                },
            ],
        }))
        current_sequence = {
            "locale": "en_US",
            "emails": [
                {"sequence_number": 1, "email_type": "company_intro", "subject": "Same", "body_text": "short text only", "suggested_send_day": 0},
                {"sequence_number": 2, "email_type": "product_showcase", "subject": "Same", "body_text": "short text only", "suggested_send_day": 3},
                {"sequence_number": 3, "email_type": "partnership_proposal", "subject": "Same", "body_text": "short text only", "suggested_send_day": 7},
            ],
        }
        lead = {"company_name": "Acme", "country_code": "us", "emails": ["buyer@acme.com"]}
        template_profile = {"tone": "professional", "source": "auto_generated"}
        template_plan = {
            "cta_strategy": "Ask a low-friction qualification question",
            "opening_strategy": "Lead with buyer relevance",
            "value_angle": "Relevant product fit",
        }
        validated_sequence = {
            "locale": "en_US",
            "emails": [
                {
                    "sequence_number": 1,
                    "email_type": "company_intro",
                    "subject": "Acme partnership idea",
                    "body_text": (
                        "This validated email includes enough buyer-specific context for Acme and keeps a clear professional "
                        "tone for review. It explains why the category may be relevant, keeps the language specific rather "
                        "than generic, and preserves a low-friction next step suitable for a first outbound touch."
                    ),
                    "suggested_send_day": 0,
                    "personalization_points": ["Acme"],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 2,
                    "email_type": "product_showcase",
                    "subject": "Acme sourcing fit",
                    "body_text": (
                        "This validated follow-up explains product fit for Acme in clearer commercial language and keeps the "
                        "progression intact. It adds enough sourcing detail to make the second touch meaningfully different "
                        "from the opener while staying concise and commercially grounded."
                    ),
                    "suggested_send_day": 3,
                    "personalization_points": ["Acme"],
                    "cultural_adaptations": [],
                },
                {
                    "sequence_number": 3,
                    "email_type": "partnership_proposal",
                    "subject": "Should I send a shortlist?",
                    "body_text": (
                        "This validated final note keeps the CTA light while staying specific enough for Acme and preserving "
                        "the three-step sequence. It closes politely, avoids pressure, and still gives the recipient a clear "
                        "reason to respond if the category is relevant."
                    ),
                    "suggested_send_day": 7,
                    "personalization_points": ["Acme"],
                    "cultural_adaptations": [],
                },
            ],
        }

        with patch(
            "agents.email_craft_agent._validate_and_revise_sequence",
            AsyncMock(return_value=(validated_sequence, {"passed": True, "status": "approved", "issues": [], "suggestions": []})),
        ) as mock_validate:
            optimized, review_summary, optimization = await _auto_improve_reviewed_sequence(
                llm,
                locale="en_US",
                rules=_get_locale_rules("en_US"),
                user_prompt="Write a concise outbound sequence for Acme.",
                current_sequence=current_sequence,
                lead=lead,
                template_profile=template_profile,
                template_plan=template_plan,
                min_score=75,
                max_blocking_issues=0,
                validation_max_revisions=1,
                max_rounds=1,
        )

        assert mock_validate.await_count == 1
        assert optimization["last_validation_status"] == "approved"
        assert review_summary["status"] in {"approved", "needs_review"}
        assert "validated" in optimized["emails"][0]["body_text"]


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
             "website": f"https://lead{i}.com", "emails": [f"info@lead{i}.com"]}
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
        assert react_call_count["n"] == 1

    @pytest.mark.asyncio
    async def test_reuses_template_for_same_group(self):
        leads = [
            {
                "company_name": "Lead A",
                "country_code": "us",
                "industry": "Industrial Supply",
                "website": "https://a.example.com",
                "emails": ["buyer@a.example.com"],
            },
            {
                "company_name": "Lead B",
                "country_code": "us",
                "industry": "Industrial Supply",
                "website": "https://b.example.com",
                "emails": ["buyer@b.example.com"],
            },
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
            mock_settings.return_value.email_template_max_send_count = 42

            llm_inst = AsyncMock()
            llm_inst.generate = AsyncMock(return_value=json.dumps({
                "passed": True,
                "grammar_ok": True,
                "spelling_ok": True,
                "language_correct": True,
                "formality_correct": True,
                "salutation_correct": True,
                "business_etiquette_ok": True,
                "local_naturalness_ok": True,
                "commercial_quality": True,
                "sequence_progression": True,
                "issues": [],
                "suggestions": [],
            }))
            llm_inst.close = AsyncMock()
            MockLLM.return_value = llm_inst

            result = await email_craft_node(state)

        assert react_call_count["n"] == 1
        assert len(result["email_sequences"]) == 2
        assert result["email_sequences"][0]["template_group"] == result["email_sequences"][1]["template_group"]
        assert result["email_sequences"][0]["template_id"] == result["email_sequences"][1]["template_id"]
        assert result["email_sequences"][0]["template_reused"] is False
        assert result["email_sequences"][1]["template_reused"] is True
        assert result["email_sequences"][0]["generation_mode"] == "template_pool"
        assert result["email_sequences"][1]["generation_mode"] == "template_pool"
        assert result["email_sequences"][0]["template_max_send_count"] == 42
        assert result["email_sequences"][0]["template_assigned_count"] == 2
        assert result["email_sequences"][1]["template_remaining_capacity"] == 40
        assert result["email_sequences"][0]["template_performance"]["status"] == "warming_up"

    @pytest.mark.asyncio
    async def test_reused_template_can_be_personalized_per_lead(self):
        leads = [
            {
                "company_name": "Lead A",
                "country_code": "us",
                "industry": "Industrial Supply",
                "website": "https://a.example.com",
                "emails": ["buyer@a.example.com"],
            },
            {
                "company_name": "Lead B",
                "country_code": "us",
                "industry": "Industrial Supply",
                "website": "https://b.example.com",
                "emails": ["buyer@b.example.com"],
            },
        ]
        state = _base_state(leads=leads)

        with patch("agents.email_craft_agent.LLMTool") as MockLLM, \
             patch("agents.email_craft_agent.get_settings") as mock_settings, \
             patch("agents.email_craft_agent._personalize_template_sequence", new_callable=AsyncMock) as mock_personalize, \
             patch("agents.email_craft_agent.react_loop", return_value=json.dumps({
                 "locale": "en_US",
                 "emails": [
                     {
                         "sequence_number": 1,
                         "email_type": "company_intro",
                         "subject": "Lead A fit for your buyers",
                         "body_text": "Dear team, " + ("Lead A looks relevant to your sourcing scope. " * 10),
                         "suggested_send_day": 0,
                         "personalization_points": ["Lead A"],
                         "cultural_adaptations": ["Professional English tone"],
                     },
                     {
                         "sequence_number": 2,
                         "email_type": "product_showcase",
                         "subject": "Lead A applications worth a look",
                         "body_text": "Dear team, " + ("Lead A may care about these applications and proof points. " * 10),
                         "suggested_send_day": 3,
                         "personalization_points": ["Lead A applications"],
                         "cultural_adaptations": ["Buyer-oriented wording"],
                     },
                     {
                         "sequence_number": 3,
                         "email_type": "partnership_proposal",
                         "subject": "Would Lead A review this category?",
                         "body_text": "Dear team, " + ("Lead A could confirm category ownership or redirect us internally. " * 10),
                         "suggested_send_day": 7,
                         "personalization_points": ["Lead A CTA"],
                         "cultural_adaptations": ["Low-pressure CTA"],
                     },
                 ],
             })):

            mock_settings.return_value.email_gen_concurrency = 3
            mock_settings.return_value.react_max_iterations = 3
            mock_settings.return_value.email_template_max_send_count = 42
            mock_settings.return_value.email_review_min_score = 75
            mock_settings.return_value.email_review_max_blocking_issues = 0

            llm_inst = AsyncMock()
            llm_inst.generate = AsyncMock(side_effect=[
                json.dumps({
                    "chosen_language": "en",
                    "chosen_locale": "en_US",
                    "confidence": "high",
                    "reason": "English is safest",
                    "fallback_used": False,
                }),
                json.dumps({
                    "recipient_profile": "Industrial distributor",
                    "why_this_company_may_fit": ["Relevant buyer profile"],
                    "best_value_angles": ["Switch range relevance"],
                    "product_focus": ["switch"],
                    "proof_points_to_use": ["Concrete fit"],
                    "claims_to_avoid": ["Avoid generic claims"],
                    "cta_strategy": "Ask a light qualification question",
                    "tone_guidance": "Professional and concise",
                    "personalization_hooks": ["Lead A"],
                }),
                json.dumps({
                    "recipient_profile": "Industrial distributor",
                    "cta_strategy": "Ask a light qualification question",
                    "opening_strategy": "Lead with buyer relevance",
                    "proof_points": ["Concrete fit"],
                }),
                json.dumps({
                    "passed": True,
                    "grammar_ok": True,
                    "spelling_ok": True,
                    "language_correct": True,
                    "formality_correct": True,
                    "salutation_correct": True,
                    "business_etiquette_ok": True,
                    "local_naturalness_ok": True,
                    "commercial_quality": True,
                    "sequence_progression": True,
                    "issues": [],
                    "suggestions": [],
                }),
            ])
            llm_inst.close = AsyncMock()
            MockLLM.return_value = llm_inst
            mock_personalize.return_value = {
                "locale": "en_US",
                "emails": [
                    {
                        "sequence_number": 1,
                        "email_type": "company_intro",
                        "subject": "Lead B fit for your buyers",
                        "body_text": "Dear team, " + ("Lead B looks relevant to your sourcing scope. " * 10),
                        "suggested_send_day": 0,
                        "personalization_points": ["Lead B"],
                        "cultural_adaptations": ["Professional English tone"],
                    },
                    {
                        "sequence_number": 2,
                        "email_type": "product_showcase",
                        "subject": "Lead B applications worth a look",
                        "body_text": "Dear team, " + ("Lead B may care about these applications and proof points. " * 10),
                        "suggested_send_day": 3,
                        "personalization_points": ["Lead B applications"],
                        "cultural_adaptations": ["Buyer-oriented wording"],
                    },
                    {
                        "sequence_number": 3,
                        "email_type": "partnership_proposal",
                        "subject": "Would Lead B review this category?",
                        "body_text": "Dear team, " + ("Lead B could confirm category ownership or redirect us internally. " * 10),
                        "suggested_send_day": 7,
                        "personalization_points": ["Lead B CTA"],
                        "cultural_adaptations": ["Low-pressure CTA"],
                    },
                ],
            }

            result = await email_craft_node(state)

        assert len(result["email_sequences"]) == 2
        assert result["email_sequences"][0]["generation_mode"] == "template_pool"
        assert result["email_sequences"][1]["generation_mode"] == "template_pool_personalized"
        assert "Lead B" in result["email_sequences"][1]["emails"][0]["subject"]
        assert "Lead B" in result["email_sequences"][1]["emails"][0]["body_text"]

    @pytest.mark.asyncio
    async def test_generates_new_template_for_different_groups(self):
        leads = [
            {
                "company_name": "Lead US",
                "country_code": "us",
                "industry": "Industrial Supply",
                "website": "https://us.example.com",
                "emails": ["buyer@us.example.com"],
            },
            {
                "company_name": "Lead DE",
                "country_code": "de",
                "industry": "Industrial Supply",
                "website": "https://de.example.com",
                "emails": ["buyer@de.example.com"],
            },
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
            llm_inst.generate = AsyncMock(return_value=json.dumps({
                "passed": True,
                "grammar_ok": True,
                "spelling_ok": True,
                "language_correct": True,
                "formality_correct": True,
                "salutation_correct": True,
                "business_etiquette_ok": True,
                "local_naturalness_ok": True,
                "commercial_quality": True,
                "sequence_progression": True,
                "issues": [],
                "suggestions": [],
            }))
            llm_inst.close = AsyncMock()
            MockLLM.return_value = llm_inst

            result = await email_craft_node(state)

        assert react_call_count["n"] == 2
        assert len(result["email_sequences"]) == 2
