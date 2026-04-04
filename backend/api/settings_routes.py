"""Settings API routes for reading and writing the user .env configuration."""

from __future__ import annotations

import asyncio
import os as _os
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from config.settings import get_settings
from config.settings_store import is_configured, read_settings, update_settings
from emailing.imap_client import test_imap_connection
from emailing.smtp_client import test_smtp_connection

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsPayload(BaseModel):
    llm_model: str = ""
    reasoning_model: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    zai_api_key: str = ""
    moonshot_api_key: str = ""
    minimax_api_key: str = ""
    serper_api_key: str = ""
    tavily_api_key: str = ""
    jina_api_key: str = ""
    email_provider_type: str = ""
    amap_api_key: str = ""
    baidu_api_key: str = ""
    hunter_api_key: str = ""
    email_from_name: str = ""
    email_from_address: str = ""
    email_reply_to: str = ""
    email_smtp_host: str = ""
    email_smtp_port: str = ""
    email_smtp_username: str = ""
    email_smtp_password: str = ""
    email_smtp_last_test_at: str = ""
    email_imap_host: str = ""
    email_imap_port: str = ""
    email_imap_username: str = ""
    email_imap_password: str = ""
    email_imap_last_test_at: str = ""
    email_use_tls: str = ""
    email_sequence_enabled: str = ""
    email_auto_send_enabled: str = ""
    email_step1_delay_days: str = ""
    email_step2_delay_days: str = ""
    email_step3_delay_days: str = ""
    email_business_hours_start: str = ""
    email_business_hours_end: str = ""
    email_weekdays_only: str = ""
    email_timezone: str = ""
    email_daily_send_limit: str = ""
    email_hourly_send_limit: str = ""
    email_language_mode: str = ""
    email_default_language: str = ""
    email_fallback_language: str = ""
    email_tone: str = ""
    email_signature_block: str = ""
    email_min_fit_score_to_send: str = ""
    email_min_contactability_score_to_send: str = ""
    email_allow_inferred_target: str = ""
    email_allow_generic_company_email: str = ""
    email_reply_detection_enabled: str = ""
    email_reply_check_interval_seconds: str = ""
    email_template_max_send_count: str = ""
    email_template_underperforming_min_assigned: str = ""
    email_template_underperforming_min_reply_rate: str = ""
    search_concurrency: str = ""
    scrape_concurrency: str = ""


class SettingsResponse(BaseModel):
    settings: dict[str, str]
    is_configured: bool


class ActivateRequest(BaseModel):
    license_key: str = ""
    machine_label: str = ""


def _ensure_settings_api_enabled() -> None:
    if get_settings().settings_api_enabled:
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings API is disabled")


class SaveTokenRequest(BaseModel):
    token: str
    expires_at: str | None = None


class LicenseStatusResponse(BaseModel):
    status: Literal["valid"]
    message: str
    plan: str
    customer_name: str
    expires_at: str | None


class SmtpTestResponse(BaseModel):
    status: str
    message: str
    host: str
    username: str


class ImapTestResponse(BaseModel):
    status: str
    message: str
    host: str
    username: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Settings routes ───────────────────────────────────────────────────────────
@router.get("", response_model=SettingsResponse)
async def get_settings_api():
    """Return current settings with sensitive values partially masked."""
    _ensure_settings_api_enabled()
    raw = read_settings()
    masked = {key: _mask(value) for key, value in raw.items()}
    return SettingsResponse(
        settings=masked,
        is_configured=is_configured(),
    )


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def save_settings(payload: SettingsPayload):
    """Save settings to the user's .env file. Empty strings are skipped."""
    _ensure_settings_api_enabled()
    field_map = {
        "llm_model": "LLM_MODEL",
        "reasoning_model": "REASONING_MODEL",
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "openrouter_api_key": "OPENROUTER_API_KEY",
        "groq_api_key": "GROQ_API_KEY",
        "zai_api_key": "ZAI_API_KEY",
        "moonshot_api_key": "MOONSHOT_API_KEY",
        "minimax_api_key": "MINIMAX_API_KEY",
        "serper_api_key": "SERPER_API_KEY",
        "tavily_api_key": "TAVILY_API_KEY",
        "jina_api_key": "JINA_API_KEY",
        "email_provider_type": "EMAIL_PROVIDER_TYPE",
        "amap_api_key": "AMAP_API_KEY",
        "baidu_api_key": "BAIDU_API_KEY",
        "hunter_api_key": "HUNTER_API_KEY",
        "email_from_name": "EMAIL_FROM_NAME",
        "email_from_address": "EMAIL_FROM_ADDRESS",
        "email_reply_to": "EMAIL_REPLY_TO",
        "email_smtp_host": "EMAIL_SMTP_HOST",
        "email_smtp_port": "EMAIL_SMTP_PORT",
        "email_smtp_username": "EMAIL_SMTP_USERNAME",
        "email_smtp_password": "EMAIL_SMTP_PASSWORD",
        "email_smtp_last_test_at": "EMAIL_SMTP_LAST_TEST_AT",
        "email_imap_host": "EMAIL_IMAP_HOST",
        "email_imap_port": "EMAIL_IMAP_PORT",
        "email_imap_username": "EMAIL_IMAP_USERNAME",
        "email_imap_password": "EMAIL_IMAP_PASSWORD",
        "email_imap_last_test_at": "EMAIL_IMAP_LAST_TEST_AT",
        "email_use_tls": "EMAIL_USE_TLS",
        "email_sequence_enabled": "EMAIL_SEQUENCE_ENABLED",
        "email_auto_send_enabled": "EMAIL_AUTO_SEND_ENABLED",
        "email_step1_delay_days": "EMAIL_STEP1_DELAY_DAYS",
        "email_step2_delay_days": "EMAIL_STEP2_DELAY_DAYS",
        "email_step3_delay_days": "EMAIL_STEP3_DELAY_DAYS",
        "email_business_hours_start": "EMAIL_BUSINESS_HOURS_START",
        "email_business_hours_end": "EMAIL_BUSINESS_HOURS_END",
        "email_weekdays_only": "EMAIL_WEEKDAYS_ONLY",
        "email_timezone": "EMAIL_TIMEZONE",
        "email_daily_send_limit": "EMAIL_DAILY_SEND_LIMIT",
        "email_hourly_send_limit": "EMAIL_HOURLY_SEND_LIMIT",
        "email_language_mode": "EMAIL_LANGUAGE_MODE",
        "email_default_language": "EMAIL_DEFAULT_LANGUAGE",
        "email_fallback_language": "EMAIL_FALLBACK_LANGUAGE",
        "email_tone": "EMAIL_TONE",
        "email_signature_block": "EMAIL_SIGNATURE_BLOCK",
        "email_min_fit_score_to_send": "EMAIL_MIN_FIT_SCORE_TO_SEND",
        "email_min_contactability_score_to_send": "EMAIL_MIN_CONTACTABILITY_SCORE_TO_SEND",
        "email_allow_inferred_target": "EMAIL_ALLOW_INFERRED_TARGET",
        "email_allow_generic_company_email": "EMAIL_ALLOW_GENERIC_COMPANY_EMAIL",
        "email_reply_detection_enabled": "EMAIL_REPLY_DETECTION_ENABLED",
        "email_reply_check_interval_seconds": "EMAIL_REPLY_CHECK_INTERVAL_SECONDS",
        "email_template_max_send_count": "EMAIL_TEMPLATE_MAX_SEND_COUNT",
        "email_template_underperforming_min_assigned": "EMAIL_TEMPLATE_UNDERPERFORMING_MIN_ASSIGNED",
        "email_template_underperforming_min_reply_rate": "EMAIL_TEMPLATE_UNDERPERFORMING_MIN_REPLY_RATE",
        "search_concurrency": "SEARCH_CONCURRENCY",
        "scrape_concurrency": "SCRAPE_CONCURRENCY",
    }

    updates: dict[str, str] = {}
    smtp_fields_changed = False
    imap_fields_changed = False
    for field, env_key in field_map.items():
        value = getattr(payload, field, "")
        if value and not _is_masked(value):
            updates[env_key] = value
            if field in {"email_from_address", "email_smtp_host", "email_smtp_port", "email_smtp_username", "email_smtp_password", "email_use_tls"}:
                smtp_fields_changed = True
            if field in {"email_imap_host", "email_imap_port", "email_imap_username", "email_imap_password"}:
                imap_fields_changed = True

    if smtp_fields_changed:
        updates["EMAIL_SMTP_LAST_TEST_AT"] = ""
    if imap_fields_changed:
        updates["EMAIL_IMAP_LAST_TEST_AT"] = ""

    if updates:
        update_settings(updates)
        for env_key, value in updates.items():
            _os.environ[env_key] = value

    get_settings.cache_clear()


@router.post("/email/test", response_model=SmtpTestResponse)
async def test_email_settings():
    """Test SMTP connectivity using the current saved settings."""
    get_settings.cache_clear()
    settings = get_settings()
    try:
        result = await asyncio.to_thread(test_smtp_connection, settings)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    tested_at = _now_iso()
    update_settings({"EMAIL_SMTP_LAST_TEST_AT": tested_at})
    _os.environ["EMAIL_SMTP_LAST_TEST_AT"] = tested_at
    get_settings.cache_clear()
    return SmtpTestResponse(
        status="ok",
        message="SMTP connection successful",
        host=result["host"],
        username=result["username"],
    )


@router.post("/email/imap-test", response_model=ImapTestResponse)
async def test_email_imap_settings():
    """Test IMAP connectivity using the current saved settings."""
    get_settings.cache_clear()
    settings = get_settings()
    try:
        result = await asyncio.to_thread(test_imap_connection, settings)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    tested_at = _now_iso()
    update_settings({"EMAIL_IMAP_LAST_TEST_AT": tested_at})
    _os.environ["EMAIL_IMAP_LAST_TEST_AT"] = tested_at
    get_settings.cache_clear()
    return ImapTestResponse(
        status="ok",
        message="IMAP connection successful",
        host=result["host"],
        username=result["username"],
    )


# ── License routes ────────────────────────────────────────────────────────────

def _license_removed_response() -> LicenseStatusResponse:
    return LicenseStatusResponse(
        status="valid",
        message="License verification has been removed; all features are available.",
        plan="lifetime",
        customer_name="Local User",
        expires_at=None,
    )


@router.get("/license/status", response_model=LicenseStatusResponse)
async def license_status():
    """Return a compatibility response after license verification removal."""
    return _license_removed_response()


@router.post("/license/activate", response_model=LicenseStatusResponse)
async def activate_license(req: ActivateRequest):
    """Keep the old activation endpoint stable after license removal."""
    return _license_removed_response()


@router.post("/license/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_license():
    """Keep the old deactivation endpoint stable after license removal."""
    return None


@router.post("/license/save-token", status_code=status.HTTP_204_NO_CONTENT)
async def save_license_token(req: SaveTokenRequest):
    """Accept legacy save-token calls as a no-op after license removal."""
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────
def _mask(value: str) -> str:
    """Partially mask a secret value for display."""
    if not value or len(value) < 8:
        return value
    return value[:4] + "****" + value[-4:]


def _is_masked(value: str) -> bool:
    return "****" in value
