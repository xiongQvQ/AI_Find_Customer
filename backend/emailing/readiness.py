"""Readiness checks for email generation, delivery, and reply detection."""

from __future__ import annotations

from typing import Any


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (int, float)):
        return value <= 0
    return False


def _missing_fields(settings: Any, required_fields: list[tuple[str, str]]) -> list[str]:
    missing: list[str] = []
    for attr_name, label in required_fields:
        if _is_missing(getattr(settings, attr_name, "")):
            missing.append(label)
    return missing


def smtp_readiness(settings: Any) -> dict[str, Any]:
    missing = _missing_fields(
        settings,
        [
            ("email_from_address", "EMAIL_FROM_ADDRESS"),
            ("email_smtp_host", "EMAIL_SMTP_HOST"),
            ("email_smtp_port", "EMAIL_SMTP_PORT"),
            ("email_smtp_username", "EMAIL_SMTP_USERNAME"),
            ("email_smtp_password", "EMAIL_SMTP_PASSWORD"),
        ],
    )
    return {
        "ready": not missing,
        "missing_fields": missing,
        "message": "SMTP is not configured. Missing: " + ", ".join(missing) if missing else "SMTP is configured.",
    }


def imap_readiness(settings: Any) -> dict[str, Any]:
    missing = _missing_fields(
        settings,
        [
            ("email_imap_host", "EMAIL_IMAP_HOST"),
            ("email_imap_port", "EMAIL_IMAP_PORT"),
            ("email_imap_username", "EMAIL_IMAP_USERNAME"),
            ("email_imap_password", "EMAIL_IMAP_PASSWORD"),
        ],
    )
    return {
        "ready": not missing,
        "missing_fields": missing,
        "message": "IMAP is not configured. Missing: " + ", ".join(missing) if missing else "IMAP is configured.",
    }


def smtp_test_readiness(settings: Any) -> dict[str, Any]:
    configured = smtp_readiness(settings)
    tested_at = str(getattr(settings, "email_smtp_last_test_at", "") or "").strip()
    ready = bool(configured["ready"] and tested_at)
    return {
        "ready": ready,
        "tested_at": tested_at,
        "message": (
            "SMTP connection has not been verified yet. Please test SMTP in Settings before enabling auto send."
            if configured["ready"] and not tested_at
            else "SMTP connection verified."
        ),
    }


def imap_test_readiness(settings: Any) -> dict[str, Any]:
    configured = imap_readiness(settings)
    tested_at = str(getattr(settings, "email_imap_last_test_at", "") or "").strip()
    ready = bool(configured["ready"] and tested_at)
    return {
        "ready": ready,
        "tested_at": tested_at,
        "message": (
            "IMAP connection has not been verified yet. Please test IMAP in Settings before enabling automated reply detection."
            if configured["ready"] and not tested_at
            else "IMAP connection verified."
        ),
    }


def ensure_smtp_ready(settings: Any) -> None:
    status = smtp_readiness(settings)
    if not status["ready"]:
        raise ValueError(str(status["message"]))


def ensure_imap_ready(settings: Any) -> None:
    status = imap_readiness(settings)
    if not status["ready"]:
        raise ValueError(str(status["message"]))


def ensure_smtp_tested(settings: Any) -> None:
    ensure_smtp_ready(settings)
    status = smtp_test_readiness(settings)
    if not status["ready"]:
        raise ValueError(str(status["message"]))


def ensure_imap_tested(settings: Any) -> None:
    ensure_imap_ready(settings)
    status = imap_test_readiness(settings)
    if not status["ready"]:
        raise ValueError(str(status["message"]))
