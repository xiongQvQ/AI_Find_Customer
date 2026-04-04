"""SMTP helpers for connection checks and outbound email sends."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config.settings import Settings
from emailing.body_format import format_plaintext_email_body


def _ensure_smtp_config(settings: Settings) -> None:
    required = {
        "EMAIL_SMTP_HOST": settings.email_smtp_host,
        "EMAIL_SMTP_PORT": str(settings.email_smtp_port or ""),
        "EMAIL_SMTP_USERNAME": settings.email_smtp_username,
        "EMAIL_SMTP_PASSWORD": settings.email_smtp_password,
        "EMAIL_FROM_ADDRESS": settings.email_from_address,
    }
    missing = [key for key, value in required.items() if not str(value or "").strip()]
    if missing:
        raise ValueError(f"Missing SMTP settings: {', '.join(missing)}")


def _connect(settings: Settings) -> smtplib.SMTP:
    _ensure_smtp_config(settings)
    host = settings.email_smtp_host
    port = int(settings.email_smtp_port or 0)

    if settings.email_use_tls and port == 465:
        client: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=20)
    else:
        client = smtplib.SMTP(host, port, timeout=20)
        client.ehlo()
        if settings.email_use_tls:
            client.starttls()
            client.ehlo()

    client.login(settings.email_smtp_username, settings.email_smtp_password)
    return client


def test_smtp_connection(settings: Settings) -> dict[str, str]:
    """Validate that SMTP settings can connect and authenticate."""
    client = _connect(settings)
    try:
        return {
            "status": "ok",
            "host": settings.email_smtp_host,
            "username": settings.email_smtp_username,
        }
    finally:
        client.quit()


def send_smtp_email(
    settings: Settings,
    *,
    to_address: str,
    subject: str,
    body_text: str,
) -> dict[str, str]:
    """Send a plain-text email using the configured SMTP account."""
    client = _connect(settings)
    try:
        message = EmailMessage()
        message["From"] = (
            f"{settings.email_from_name} <{settings.email_from_address}>"
            if settings.email_from_name.strip()
            else settings.email_from_address
        )
        message["To"] = to_address
        message["Subject"] = subject
        if settings.email_reply_to.strip():
            message["Reply-To"] = settings.email_reply_to
        message.set_content(format_plaintext_email_body(body_text))
        client.send_message(message)
        return {
            "status": "sent",
            "to_address": to_address,
            "subject": subject,
        }
    finally:
        client.quit()
