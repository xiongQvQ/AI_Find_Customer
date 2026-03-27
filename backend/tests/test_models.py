"""Tests for models.py — verify creation, serialization, defaults, validation."""

import pytest
from pydantic import ValidationError

from models import (
    EmailDraft,
    EmailLocaleProfile,
    EmailSequence,
    EmailType,
    FormalityLevel,
    HuntInput,
    KeywordPerformance,
    LeadInfo,
    RoundFeedback,
    TextDirection,
)


class TestHuntInput:
    def test_minimal_creation(self):
        inp = HuntInput(website_url="https://example.com")
        assert inp.website_url == "https://example.com"
        assert inp.product_keywords == []
        assert inp.target_regions == []
        assert inp.uploaded_files == []
        assert inp.target_lead_count == 200
        assert inp.max_rounds == 10
        assert inp.min_new_leads_threshold == 5
        assert inp.enable_email_craft is False

    def test_full_creation(self):
        inp = HuntInput(
            website_url="https://solar.com",
            product_keywords=["solar inverter", "PV"],
            target_regions=["Europe", "North America"],
            uploaded_files=["/tmp/catalog.pdf"],
            target_lead_count=300,
            max_rounds=15,
            min_new_leads_threshold=7,
            enable_email_craft=True,
        )
        assert inp.target_lead_count == 300
        assert inp.min_new_leads_threshold == 7
        assert len(inp.product_keywords) == 2
        assert inp.enable_email_craft is True

    def test_target_lead_count_must_be_positive(self):
        with pytest.raises(ValidationError):
            HuntInput(website_url="https://x.com", target_lead_count=0)

    def test_max_rounds_upper_bound(self):
        with pytest.raises(ValidationError):
            HuntInput(website_url="https://x.com", max_rounds=51)

    def test_min_new_leads_threshold_bounds(self):
        with pytest.raises(ValidationError):
            HuntInput(website_url="https://x.com", min_new_leads_threshold=0)

    def test_serialization_roundtrip(self):
        inp = HuntInput(website_url="https://example.com", product_keywords=["a", "b"])
        data = inp.model_dump()
        restored = HuntInput(**data)
        assert restored == inp


class TestLeadInfo:
    def test_defaults(self):
        lead = LeadInfo(company_name="Acme", website="https://acme.com")
        assert lead.industry == ""
        assert lead.emails == []
        assert lead.match_score == 0.0
        assert lead.contact_person is None
        assert lead.source_keyword == ""

    def test_match_score_bounds(self):
        lead = LeadInfo(company_name="X", website="https://x.com", match_score=0.85)
        assert lead.match_score == 0.85

        with pytest.raises(ValidationError):
            LeadInfo(company_name="X", website="https://x.com", match_score=1.5)

        with pytest.raises(ValidationError):
            LeadInfo(company_name="X", website="https://x.com", match_score=-0.1)

    def test_serialization(self):
        lead = LeadInfo(
            company_name="SolarTech",
            website="https://solartech.de",
            industry="Renewable Energy",
            emails=["info@solartech.de"],
            match_score=0.9,
            country_code="de",
        )
        data = lead.model_dump()
        assert data["company_name"] == "SolarTech"
        assert data["country_code"] == "de"


class TestEmailDraft:
    def test_creation(self):
        draft = EmailDraft(
            sequence_number=1,
            email_type=EmailType.COMPANY_INTRO,
            to_email="info@acme.com",
            subject="Partnership Opportunity",
        )
        assert draft.sequence_number == 1
        assert draft.email_type == EmailType.COMPANY_INTRO
        assert draft.language == "en"
        assert draft.locale == "en_US"
        assert draft.suggested_send_day == 0

    def test_sequence_number_bounds(self):
        with pytest.raises(ValidationError):
            EmailDraft(
                sequence_number=0,
                email_type=EmailType.COMPANY_INTRO,
                to_email="x@x.com",
                subject="Hi",
            )
        with pytest.raises(ValidationError):
            EmailDraft(
                sequence_number=4,
                email_type=EmailType.COMPANY_INTRO,
                to_email="x@x.com",
                subject="Hi",
            )

    def test_email_types(self):
        assert EmailType.COMPANY_INTRO.value == "company_intro"
        assert EmailType.PRODUCT_SHOWCASE.value == "product_showcase"
        assert EmailType.PARTNERSHIP_PROPOSAL.value == "partnership_proposal"


class TestEmailSequence:
    def test_creation_with_lead(self):
        lead = LeadInfo(company_name="Acme", website="https://acme.com")
        seq = EmailSequence(lead=lead, locale="de_DE")
        assert seq.locale == "de_DE"
        assert seq.emails == []

    def test_max_three_emails(self):
        lead = LeadInfo(company_name="Acme", website="https://acme.com")
        emails = [
            EmailDraft(
                sequence_number=i,
                email_type=EmailType.COMPANY_INTRO,
                to_email="x@x.com",
                subject=f"Email {i}",
            )
            for i in range(1, 4)
        ]
        seq = EmailSequence(lead=lead, emails=emails)
        assert len(seq.emails) == 3


class TestEmailLocaleProfile:
    def test_defaults(self):
        profile = EmailLocaleProfile(locale_code="en_US", language_name="English")
        assert profile.formality_level == FormalityLevel.FORMAL
        assert profile.email_direction == TextDirection.LTR
        assert profile.cultural_notes == []
        assert profile.taboos == []

    def test_arabic_rtl(self):
        profile = EmailLocaleProfile(
            locale_code="ar_AR",
            language_name="Arabic",
            email_direction=TextDirection.RTL,
            formality_level=FormalityLevel.FORMAL,
        )
        assert profile.email_direction == TextDirection.RTL

    def test_serialization(self):
        profile = EmailLocaleProfile(
            locale_code="ja_JP",
            language_name="Japanese",
            greeting_template="{LastName}様",
            tone="extremely formal",
            cultural_notes=["seasonal greetings required"],
        )
        data = profile.model_dump()
        assert data["locale_code"] == "ja_JP"
        assert len(data["cultural_notes"]) == 1


class TestKeywordPerformance:
    def test_defaults(self):
        kp = KeywordPerformance(keyword="solar inverter")
        assert kp.search_results == 0
        assert kp.leads_found == 0
        assert kp.effectiveness == "low"

    def test_high_effectiveness(self):
        kp = KeywordPerformance(
            keyword="PV distributor Europe",
            search_results=25,
            leads_found=8,
            effectiveness="high",
        )
        assert kp.effectiveness == "high"


class TestRoundFeedback:
    def test_creation(self):
        fb = RoundFeedback(
            round=2,
            total_leads=65,
            target=300,
            new_leads_this_round=40,
            best_keywords=["solar inverter distributor"],
            worst_keywords=["PV buyer"],
            industry_distribution={"Renewable Energy": 30, "Electronics": 15},
            region_distribution={"Europe": 40, "Asia": 25},
        )
        assert fb.round == 2
        assert fb.total_leads == 65
        assert len(fb.best_keywords) == 1
        assert fb.industry_distribution["Renewable Energy"] == 30

    def test_defaults(self):
        fb = RoundFeedback(round=1, total_leads=0, target=200, new_leads_this_round=0)
        assert fb.keyword_performance == []
        assert fb.best_keywords == []
        assert fb.worst_keywords == []
        assert fb.top_sources == []

    def test_serialization_roundtrip(self):
        kp = KeywordPerformance(keyword="test kw", search_results=10, leads_found=3, effectiveness="medium")
        fb = RoundFeedback(
            round=1,
            total_leads=50,
            target=200,
            new_leads_this_round=50,
            keyword_performance=[kp],
        )
        data = fb.model_dump()
        restored = RoundFeedback(**data)
        assert restored.keyword_performance[0].keyword == "test kw"
