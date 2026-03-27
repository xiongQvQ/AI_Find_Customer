"""Detect inbound email replies via IMAP polling."""

from __future__ import annotations

import asyncio
import email
import imaplib
import uuid
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any, Callable

from api.hunt_store import load_hunt, save_hunt
from emailing.store import EmailStore

_AUTO_REPLY_SUBJECT_MARKERS = (
    "out of office",
    "automatic reply",
    "auto reply",
    "autoreply",
    "vacation",
    "on leave",
    "delivery status notification",
    "delivery failure",
    "mail delivery failed",
    "undeliverable",
    "failure notice",
    "read:",
    "read receipt",
)

_AUTO_REPLY_SNIPPET_MARKERS = (
    "i am currently out of office",
    "i'm currently out of office",
    "this is an automatic reply",
    "this is an auto reply",
    "thank you for your email. i am away",
    "delivery has failed",
    "could not be delivered",
    "recipient address rejected",
)

_AUTO_REPLY_LOCAL_PARTS = {
    "mailer-daemon",
    "postmaster",
    "noreply",
    "no-reply",
    "do-not-reply",
    "donotreply",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_message_id(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("<") and text.endswith(">"):
        return text
    return f"<{text.strip('<>')}>"


def _extract_message_ids(header_value: str) -> list[str]:
    text = str(header_value or "").strip()
    if not text:
        return []
    ids = []
    for token in text.replace(",", " ").split():
        normalized = _normalize_message_id(token)
        if normalized:
            ids.append(normalized)
    return ids


def _decode_header_value(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _normalize_subject(subject: str) -> str:
    text = _decode_header_value(subject).strip()
    prefixes = ("re:", "fw:", "fwd:", "sv:", "aw:")
    changed = True
    while changed and text:
        changed = False
        lowered = text.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                text = text[len(prefix):].strip()
                changed = True
                break
    return " ".join(text.split())


def _extract_snippet(message: email.message.Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace").strip()[:500]
    payload = message.get_payload(decode=True) or b""
    charset = message.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace").strip()[:500]


def _received_at(message: email.message.Message, fallback_iso: str) -> str:
    raw_date = message.get("Date", "")
    if not raw_date:
        return fallback_iso
    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return fallback_iso


def _refresh_hunt_email_summary(store: EmailStore, hunt_id: str, campaign_id: str) -> None:
    hunt = load_hunt(hunt_id)
    if not hunt:
        return
    campaign = store.get_campaign(campaign_id)
    sequences = store.list_sequences_for_campaign(campaign_id)
    result = hunt.setdefault("result", {})
    result["email_campaign_summary"] = {
        "campaign_id": campaign_id,
        "status": campaign.get("status", "draft") if campaign else "draft",
        "sequences_total": len(sequences),
        "sent_count": store.count_messages_for_campaign(campaign_id, status="sent"),
        "failed_count": store.count_messages_for_campaign(campaign_id, status="failed"),
        "pending_count": store.count_messages_for_campaign(campaign_id, status="pending"),
        "replied_count": sum(1 for seq in sequences if seq.get("status") == "replied"),
    }
    save_hunt(hunt_id, hunt)


def _match_sent_message(store: EmailStore, inbound: dict[str, Any]) -> dict[str, Any] | None:
    candidates = []
    in_reply_to = _normalize_message_id(str(inbound.get("in_reply_to", "") or ""))
    if in_reply_to:
        candidates.append(in_reply_to)
    for ref in inbound.get("references", []) or []:
        normalized = _normalize_message_id(str(ref or ""))
        if normalized:
            candidates.append(normalized)
    for message_id in candidates:
        matched = store.find_message_by_provider_message_id(message_id)
        if matched:
            return matched

    from_email = str(inbound.get("from_email", "") or "").strip().lower()
    normalized_subject = _normalize_subject(str(inbound.get("subject", "") or ""))
    if from_email and normalized_subject:
        return store.find_sent_message_by_lead_email_and_subject(from_email, normalized_subject)
    return None


def _is_auto_reply(inbound: dict[str, Any]) -> bool:
    from_email = str(inbound.get("from_email", "") or "").strip().lower()
    if from_email and "@" in from_email:
        local = from_email.split("@", 1)[0]
        if local in _AUTO_REPLY_LOCAL_PARTS:
            return True

    subject = _normalize_subject(str(inbound.get("subject", "") or "")).lower()
    if any(marker in subject for marker in _AUTO_REPLY_SUBJECT_MARKERS):
        return True

    snippet = str(inbound.get("snippet", "") or "").strip().lower()
    if any(marker in snippet for marker in _AUTO_REPLY_SNIPPET_MARKERS):
        return True

    headers = {str(k).lower(): str(v).lower() for k, v in (inbound.get("headers", {}) or {}).items()}
    auto_submitted = headers.get("auto-submitted", "")
    precedence = headers.get("precedence", "")
    x_autoreply = headers.get("x-autoreply", "")
    x_autorespond = headers.get("x-autorespond", "")
    x_failed_recipients = headers.get("x-failed-recipients", "")

    if auto_submitted and auto_submitted != "no":
        return True
    if precedence in {"bulk", "junk", "list", "auto_reply"}:
        return True
    if x_autoreply or x_autorespond or x_failed_recipients:
        return True
    return False


def fetch_imap_replies(account: dict[str, Any], *, now_iso: str, recent_days: int = 14) -> list[dict[str, Any]]:
    """Fetch recent inbound messages from IMAP for reply matching."""
    host = str(account.get("imap_host", "") or "").strip()
    username = str(account.get("imap_username", "") or "").strip()
    password = str(account.get("imap_secret_encrypted", "") or "")
    port = int(account.get("imap_port", 993) or 993)
    use_tls = bool(account.get("use_tls", True))
    if not host or not username or not password:
        return []

    mailbox: imaplib.IMAP4 = imaplib.IMAP4_SSL(host, port) if use_tls else imaplib.IMAP4(host, port)
    messages: list[dict[str, Any]] = []
    try:
        mailbox.login(username, password)
        mailbox.select("INBOX")
        since = (datetime.fromisoformat(now_iso.replace("Z", "+00:00")) - timedelta(days=recent_days)).strftime("%d-%b-%Y")
        status, data = mailbox.search(None, "SINCE", since)
        if status != "OK":
            return []
        message_nums = data[0].split()[-100:]
        for num in message_nums:
            status, parts = mailbox.fetch(num, "(RFC822)")
            if status != "OK":
                continue
            raw_email = b""
            for part in parts:
                if isinstance(part, tuple):
                    raw_email += part[1]
            if not raw_email:
                continue
            parsed = email.message_from_bytes(raw_email)
            addresses = getaddresses([parsed.get("From", "")])
            from_email = addresses[0][1].strip().lower() if addresses else ""
            message_id = _normalize_message_id(parsed.get("Message-ID", ""))
            raw_ref = message_id or f"imap:{num.decode()}"
            messages.append({
                "raw_ref": raw_ref,
                "message_id": message_id,
                "from_email": from_email,
                "subject": _decode_header_value(parsed.get("Subject", "")),
                "in_reply_to": parsed.get("In-Reply-To", ""),
                "references": _extract_message_ids(parsed.get("References", "")),
                "received_at": _received_at(parsed, now_iso),
                "snippet": _extract_snippet(parsed),
                "headers": {
                    "Auto-Submitted": parsed.get("Auto-Submitted", ""),
                    "Precedence": parsed.get("Precedence", ""),
                    "X-Autoreply": parsed.get("X-Autoreply", ""),
                    "X-Autorespond": parsed.get("X-Autorespond", ""),
                    "X-Failed-Recipients": parsed.get("X-Failed-Recipients", ""),
                },
            })
    finally:
        try:
            mailbox.logout()
        except Exception:
            pass
    return messages


async def run_reply_detection_once(
    store: EmailStore,
    account: dict[str, Any],
    *,
    now_iso: str | None = None,
    fetcher: Callable[..., list[dict[str, Any]]] = fetch_imap_replies,
) -> dict[str, int]:
    """Poll inbox once, match replies to sent messages, and stop follow-ups."""
    current = now_iso or _now_iso()
    inbound_messages = await asyncio.to_thread(fetcher, account, now_iso=current)
    checked = 0
    matched = 0
    skipped = 0
    ignored = 0
    for inbound in inbound_messages:
        checked += 1
        raw_ref = str(inbound.get("raw_ref", "") or "")
        if raw_ref and store.has_reply_event(raw_ref):
            skipped += 1
            continue
        if _is_auto_reply(inbound):
            ignored += 1
            continue

        sent_message = _match_sent_message(store, inbound)
        if not sent_message:
            skipped += 1
            continue
        sequence = store.get_sequence(str(sent_message.get("sequence_id", "")))
        if not sequence:
            skipped += 1
            continue

        received_at = str(inbound.get("received_at", "") or current)
        store.create_reply_event({
            "id": str(uuid.uuid4()),
            "sequence_id": str(sequence["id"]),
            "message_id": str(sent_message.get("id", "") or ""),
            "from_email": str(inbound.get("from_email", "") or ""),
            "subject": str(inbound.get("subject", "") or ""),
            "snippet": str(inbound.get("snippet", "") or ""),
            "received_at": received_at,
            "raw_ref": raw_ref,
            "created_at": current,
        })
        store.update_sequence_status(
            str(sequence["id"]),
            status="replied",
            updated_at=current,
            replied_at=received_at,
            stop_reason="reply_detected",
        )
        store.cancel_future_pending_messages(str(sequence["id"]), updated_at=current)
        _refresh_hunt_email_summary(store, str(sequence["hunt_id"]), str(sequence["campaign_id"]))
        matched += 1

    return {"checked": checked, "matched": matched, "skipped": skipped, "ignored": ignored}
