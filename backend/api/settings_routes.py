"""Settings API routes — read/write user .env configuration and license management."""

from __future__ import annotations

import asyncio
import os as _os
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from config.settings import get_settings
from emailing.imap_client import test_imap_connection
from emailing.smtp_client import test_smtp_connection
from license.settings_store import get_env_path, is_configured, read_settings, update_settings
from license.token_store import save_token
from license.validator import LicenseResult, LicenseValidator

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_validator() -> LicenseValidator:
    s = get_settings()
    server_url = getattr(s, "license_server_url", "https://license.b2binsights.io/api/v1")
    return LicenseValidator(server_url)


# ── Schemas ───────────────────────────────────────────────────────────────────

class SettingsPayload(BaseModel):
    # LLM
    llm_model: str = ""
    reasoning_model: str = ""
    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    zai_api_key: str = ""
    moonshot_api_key: str = ""
    minimax_api_key: str = ""
    # Search
    serper_api_key: str = ""
    tavily_api_key: str = ""
    jina_api_key: str = ""
    amap_api_key: str = ""
    baidu_api_key: str = ""
    # Email
    hunter_api_key: str = ""
    email_from_name: str = ""
    email_from_address: str = ""
    email_reply_to: str = ""
    email_smtp_host: str = ""
    email_smtp_port: str = ""
    email_smtp_username: str = ""
    email_smtp_password: str = ""
    email_imap_host: str = ""
    email_imap_port: str = ""
    email_imap_username: str = ""
    email_imap_password: str = ""
    email_use_tls: str = ""
    email_auto_send_enabled: str = ""
    email_reply_detection_enabled: str = ""
    email_reply_check_interval_seconds: str = ""
    # Concurrency
    search_concurrency: str = ""
    scrape_concurrency: str = ""


class SettingsResponse(BaseModel):
    settings: dict[str, str]
    is_configured: bool
    env_path: str


class ActivateRequest(BaseModel):
    license_key: str
    machine_label: str = ""


class SaveTokenRequest(BaseModel):
    token: str
    expires_at: str | None = None


class LicenseStatusResponse(BaseModel):
    status: str
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


# ── Settings routes ───────────────────────────────────────────────────────────

@router.get("", response_model=SettingsResponse)
async def get_settings_api():
    """Return current settings (masks secret keys partially)."""
    raw = read_settings()
    masked = {k: _mask(v) for k, v in raw.items()}
    return SettingsResponse(
        settings=masked,
        is_configured=is_configured(),
        env_path=str(get_env_path()),
    )


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def save_settings(payload: SettingsPayload):
    """Save settings to the user's .env file. Empty strings are skipped."""
    updates: dict[str, str] = {}
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
        "email_imap_host": "EMAIL_IMAP_HOST",
        "email_imap_port": "EMAIL_IMAP_PORT",
        "email_imap_username": "EMAIL_IMAP_USERNAME",
        "email_imap_password": "EMAIL_IMAP_PASSWORD",
        "email_use_tls": "EMAIL_USE_TLS",
        "email_auto_send_enabled": "EMAIL_AUTO_SEND_ENABLED",
        "email_reply_detection_enabled": "EMAIL_REPLY_DETECTION_ENABLED",
        "email_reply_check_interval_seconds": "EMAIL_REPLY_CHECK_INTERVAL_SECONDS",
        "search_concurrency": "SEARCH_CONCURRENCY",
        "scrape_concurrency": "SCRAPE_CONCURRENCY",
    }
    for field, env_key in field_map.items():
        value = getattr(payload, field, "")
        if value and not _is_masked(value):
            updates[env_key] = value

    if updates:
        update_settings(updates)
        # Propagate new values into the current process environment so that
        # get_settings() picks them up immediately after cache_clear().
        # pydantic-settings reads env_file once at instantiation; environment
        # variables take precedence over the file, so this guarantees fresh values.
        for env_key, value in updates.items():
            _os.environ[env_key] = value

    # Reload settings cache so next call picks up the new values
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
    return ImapTestResponse(
        status="ok",
        message="IMAP connection successful",
        host=result["host"],
        username=result["username"],
    )


# ── License routes ────────────────────────────────────────────────────────────

def _dev_skip_license() -> bool:
    return _os.environ.get("DEV_SKIP_LICENSE", "0") == "1"


def _dev_bypass_response() -> LicenseStatusResponse:
    return LicenseStatusResponse(
        status="valid",
        message="Dev bypass — license server not yet deployed",
        plan="lifetime",
        customer_name="Dev User",
        expires_at=None,
    )


@router.get("/license/status", response_model=LicenseStatusResponse)
async def license_status():
    """Check current license status."""
    if _dev_skip_license():
        return _dev_bypass_response()
    validator = _get_validator()
    result = await validator.check()
    return _to_response(result)


@router.post("/license/activate", response_model=LicenseStatusResponse)
async def activate_license(req: ActivateRequest):
    """Activate a license key on this machine."""
    if _dev_skip_license():
        return _dev_bypass_response()
    if not req.license_key.strip():
        raise HTTPException(status_code=400, detail="License key is required")
    validator = _get_validator()
    result = await validator.activate(req.license_key, req.machine_label)
    if not result.is_allowed:
        raise HTTPException(status_code=403, detail=result.message)
    return _to_response(result)


@router.post("/license/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_license():
    """Deactivate this device (for device transfer)."""
    validator = _get_validator()
    await validator.deactivate()


@router.post("/license/save-token", status_code=status.HTTP_204_NO_CONTENT)
async def save_license_token(req: SaveTokenRequest):
    """Save JWT token from license server (for offline use)."""
    if _dev_skip_license():
        return
    # If expires_at not provided, decode from JWT token (fallback)
    if req.expires_at:
        from datetime import datetime, timezone
        expires_at = datetime.fromisoformat(req.expires_at.replace("Z", "+00:00"))
    else:
        # Try to parse from JWT token
        import base64
        import json
        try:
            parts = req.token.split(".")
            if len(parts) >= 2:
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="[: (4 - len(parts[1]) % 4)]))
                exp = payload.get("exp")
                if exp:
                    from datetime import datetime, timezone
                    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                else:
                    expires_at = datetime.now(timezone.utc).replace(year=2099, month=12, day=31)
            else:
                expires_at = datetime.now(timezone.utc).replace(year=2099, month=12, day=31)
        except Exception:
            from datetime import datetime, timezone
            expires_at = datetime.now(timezone.utc).replace(year=2099, month=12, day=31)
    save_token(req.token, expires_at)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mask(value: str) -> str:
    """Partially mask a secret value for display."""
    if not value or len(value) < 8:
        return value
    return value[:4] + "****" + value[-4:]


def _is_masked(value: str) -> bool:
    return "****" in value


def _to_response(result: LicenseResult) -> LicenseStatusResponse:
    return LicenseStatusResponse(
        status=result.status.value,
        message=result.message,
        plan=result.plan,
        customer_name=result.customer_name,
        expires_at=result.expires_at.isoformat() if result.expires_at else None,
    )
