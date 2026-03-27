"""Dataclasses for email automation state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EmailAccount:
    id: str
    provider_type: str
    from_name: str
    from_email: str
    reply_to: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_secret_encrypted: str
    imap_host: str
    imap_port: int
    imap_username: str
    imap_secret_encrypted: str
    use_tls: bool
    status: str
    daily_send_limit: int
    hourly_send_limit: int
    last_test_at: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class EmailCampaign:
    id: str
    hunt_id: str
    email_account_id: str
    name: str
    status: str
    language_mode: str
    default_language: str
    fallback_language: str
    tone: str
    step1_delay_days: int
    step2_delay_days: int
    step3_delay_days: int
    min_fit_score: float
    min_contactability_score: float
    created_at: str
    updated_at: str


@dataclass(slots=True)
class LeadEmailSequence:
    id: str
    campaign_id: str
    hunt_id: str
    lead_key: str
    lead_email: str
    lead_name: str
    decision_maker_name: str
    decision_maker_title: str
    locale: str
    status: str
    current_step: int
    stop_reason: str
    replied_at: str
    last_sent_at: str
    next_scheduled_at: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class EmailMessage:
    id: str
    sequence_id: str
    step_number: int
    goal: str
    locale: str
    subject: str
    body_text: str
    status: str
    scheduled_at: str
    sent_at: str
    provider_message_id: str
    thread_key: str
    failure_reason: str
    created_at: str
    updated_at: str

