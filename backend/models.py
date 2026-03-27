"""Shared Pydantic models used by tests and cross-module data structures."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EmailType(str, Enum):
    COMPANY_INTRO = "company_intro"
    PRODUCT_SHOWCASE = "product_showcase"
    PARTNERSHIP_PROPOSAL = "partnership_proposal"


class FormalityLevel(str, Enum):
    FORMAL = "formal"
    SEMI_FORMAL = "semi_formal"
    CASUAL = "casual"


class TextDirection(str, Enum):
    LTR = "ltr"
    RTL = "rtl"


class HuntInput(BaseModel):
    website_url: str = ""
    product_keywords: list[str] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    uploaded_files: list[str] = Field(default_factory=list)
    target_lead_count: int = Field(default=200, ge=1)
    max_rounds: int = Field(default=10, ge=1, le=50)
    min_new_leads_threshold: int = Field(default=5, ge=1, le=100)
    enable_email_craft: bool = False


class LeadInfo(BaseModel):
    company_name: str
    website: str
    industry: str = ""
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    social_media: dict[str, str] = Field(default_factory=dict)
    contact_person: str | None = None
    country_code: str = ""
    source_keyword: str = ""
    match_score: float = Field(default=0.0, ge=0.0, le=1.0)


class EmailDraft(BaseModel):
    sequence_number: int = Field(ge=1, le=3)
    email_type: EmailType
    to_email: str
    subject: str
    body: str = ""
    language: str = "en"
    locale: str = "en_US"
    suggested_send_day: int = 0


class EmailSequence(BaseModel):
    lead: LeadInfo
    locale: str = "en_US"
    emails: list[EmailDraft] = Field(default_factory=list, max_length=3)


class EmailLocaleProfile(BaseModel):
    locale_code: str
    language_name: str
    greeting_template: str = ""
    tone: str = ""
    formality_level: FormalityLevel = FormalityLevel.FORMAL
    email_direction: TextDirection = TextDirection.LTR
    cultural_notes: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)


class KeywordPerformance(BaseModel):
    keyword: str
    search_results: int = 0
    leads_found: int = 0
    effectiveness: str = "low"


class RoundFeedback(BaseModel):
    round: int
    total_leads: int
    target: int
    new_leads_this_round: int
    keyword_performance: list[KeywordPerformance] = Field(default_factory=list)
    best_keywords: list[str] = Field(default_factory=list)
    worst_keywords: list[str] = Field(default_factory=list)
    top_sources: list[str] = Field(default_factory=list)
    industry_distribution: dict[str, int] = Field(default_factory=dict)
    region_distribution: dict[str, int] = Field(default_factory=dict)
