"""Email finder helpers — extract email addresses from raw text."""

from __future__ import annotations

import re


# Common email patterns found on web pages
_EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# Filter out common false positives
_BLACKLIST_DOMAINS = {
    "example.com", "example.org", "test.com", "sentry.io",
    "wixpress.com", "w3.org", "schema.org", "googleapis.com",
    "cloudflare.com", "gravatar.com",
}

_BLACKLIST_PREFIXES = {
    "noreply", "no-reply", "mailer-daemon", "postmaster",
    "webmaster", "hostmaster", "abuse",
}


def _is_valid_email(email: str) -> bool:
    """Filter out common false-positive emails."""
    email = email.lower().strip()
    local, _, domain = email.partition("@")

    if domain in _BLACKLIST_DOMAINS:
        return False
    if local in _BLACKLIST_PREFIXES:
        return False
    if domain.endswith(".png") or domain.endswith(".jpg") or domain.endswith(".gif"):
        return False
    return True


def extract_emails_from_text(text: str) -> list[str]:
    """Extract unique valid emails from raw text using regex."""
    raw = _EMAIL_REGEX.findall(text)
    seen = set()
    result = []
    for email in raw:
        email_lower = email.lower().strip()
        if email_lower not in seen and _is_valid_email(email_lower):
            seen.add(email_lower)
            result.append(email_lower)
    return result
