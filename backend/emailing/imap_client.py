"""IMAP helpers for reply detection."""

from __future__ import annotations

import email
import imaplib
from email.header import decode_header, make_header

from config.settings import Settings


def _ensure_imap_config(settings: Settings) -> None:
    required = {
        "EMAIL_IMAP_HOST": settings.email_imap_host,
        "EMAIL_IMAP_PORT": str(settings.email_imap_port or ""),
        "EMAIL_IMAP_USERNAME": settings.email_imap_username,
        "EMAIL_IMAP_PASSWORD": settings.email_imap_password,
    }
    missing = [key for key, value in required.items() if not str(value or "").strip()]
    if missing:
        raise ValueError(f"Missing IMAP settings: {', '.join(missing)}")


def _connect(settings: Settings) -> imaplib.IMAP4_SSL:
    _ensure_imap_config(settings)
    client = imaplib.IMAP4_SSL(settings.email_imap_host, int(settings.email_imap_port or 993))
    client.login(settings.email_imap_username, settings.email_imap_password)
    return client


def test_imap_connection(settings: Settings) -> dict[str, str]:
    client = _connect(settings)
    try:
        return {
            "status": "ok",
            "host": settings.email_imap_host,
            "username": settings.email_imap_username,
        }
    finally:
        client.logout()


def _decode_subject(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def search_recent_replies(
    settings: Settings,
    *,
    from_address: str,
    limit: int = 10,
) -> list[dict[str, str]]:
    """Find recent messages from a sender in INBOX."""
    client = _connect(settings)
    try:
        client.select("INBOX")
        status, data = client.search(None, "FROM", f'"{from_address}"')
        if status != "OK":
            return []
        ids = [item for item in (data[0] or b"").split() if item][-limit:]
        replies: list[dict[str, str]] = []
        for msg_id in reversed(ids):
            fetch_status, msg_data = client.fetch(msg_id, "(RFC822)")
            if fetch_status != "OK" or not msg_data:
                continue
            raw = None
            for item in msg_data:
                if isinstance(item, tuple) and len(item) >= 2:
                    raw = item[1]
                    break
            if not raw:
                continue
            parsed = email.message_from_bytes(raw)
            replies.append({
                "from_address": from_address,
                "subject": _decode_subject(parsed.get("Subject")),
                "date": parsed.get("Date", ""),
                "message_id": parsed.get("Message-ID", ""),
            })
        return replies
    finally:
        client.logout()
