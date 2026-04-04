"""Helpers for formatting plain-text outbound email bodies."""

from __future__ import annotations

import re

_CLOSING_PATTERNS = (
    "kind regards",
    "best regards",
    "regards",
    "sincerely",
    "yours sincerely",
    "yours faithfully",
    "mit freundlichen grüßen",
    "cordiali saluti",
    "atentamente",
    "atenciosamente",
    "z poważaniem",
    "с уважением",
    "此致",
    "敬礼",
    "敬祝",
    "期待您的回复",
)


def _normalize_lines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    compact: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            blank_run = 0
            compact.append(line.strip())
        else:
            blank_run += 1
            if blank_run == 1:
                compact.append("")
    return "\n".join(compact).strip()


def _split_sentences(text: str) -> list[str]:
    collapsed = re.sub(r"\s+", " ", text.strip())
    if not collapsed:
        return []
    parts = re.split(r"(?<=[.!?])\s+", collapsed)
    return [part.strip() for part in parts if part.strip()]


def _extract_closing(sentences: list[str]) -> tuple[list[str], str]:
    if not sentences:
        return [], ""
    last = sentences[-1].strip()
    lowered = last.lower()
    if any(lowered.startswith(pattern) for pattern in _CLOSING_PATTERNS):
        return sentences[:-1], last
    return sentences, ""


def format_plaintext_email_body(body_text: str) -> str:
    """Format email body as readable plain text with paragraphs.

    If the model already returned paragraph breaks, keep them.
    Otherwise apply a conservative sentence-based grouping so the
    body reads like a standard outreach email rather than one block.
    """
    normalized = _normalize_lines(str(body_text or ""))
    if not normalized:
        return ""
    if "\n\n" in normalized:
        return normalized

    sentences = _split_sentences(normalized)
    if len(sentences) < 2:
        return normalized

    body_sentences, closing = _extract_closing(sentences)
    if len(body_sentences) >= 5:
        groups = [body_sentences[:2], body_sentences[2:4], body_sentences[4:]]
    elif len(body_sentences) == 4:
        groups = [body_sentences[:2], body_sentences[2:]]
    elif len(body_sentences) == 3:
        groups = [body_sentences[:1], body_sentences[1:2], body_sentences[2:]]
    else:
        groups = [body_sentences[:1], body_sentences[1:]]

    paragraphs = [" ".join(group).strip() for group in groups if group]
    if closing:
        paragraphs.append(closing)
    return "\n\n".join(part for part in paragraphs if part).strip()


def format_email_sequence_bodies(emails: list[dict]) -> list[dict]:
    """Return a copy of emails with normalized plain-text paragraph spacing."""
    formatted: list[dict] = []
    for email in emails:
        if not isinstance(email, dict):
            formatted.append(email)
            continue
        item = dict(email)
        item["body_text"] = format_plaintext_email_body(str(item.get("body_text", "") or ""))
        formatted.append(item)
    return formatted
