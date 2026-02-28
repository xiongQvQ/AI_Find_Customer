"""Email finder tool — discover emails via Hunter.io API and regex extraction."""

from __future__ import annotations

import re
from typing import Optional

import httpx

from config.settings import Settings, get_settings


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


class EmailFinderTool:
    """Find email addresses for a company domain using Hunter.io and regex fallback.

    Strategy:
    1. Try Hunter.io domain-search API (if API key available)
    2. Fallback: regex extraction from provided page text
    """

    HUNTER_URL = "https://api.hunter.io/v2/domain-search"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def find_by_domain(self, domain: str) -> list[dict]:
        """Find emails for a domain via Hunter.io.

        Args:
            domain: Company domain (e.g. "solartech.de").

        Returns:
            List of dicts with keys: email, first_name, last_name, position, confidence.
            Empty list if no API key or no results.
        """
        if not self._settings.hunter_api_key:
            return []

        client = await self._get_client()
        resp = await client.get(
            self.HUNTER_URL,
            params={
                "domain": domain,
                "api_key": self._settings.hunter_api_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("data", {}).get("emails", []):
            results.append({
                "email": item.get("value", ""),
                "first_name": item.get("first_name", ""),
                "last_name": item.get("last_name", ""),
                "position": item.get("position", ""),
                "confidence": item.get("confidence", 0),
            })
        return results

    def find_in_text(self, text: str) -> list[str]:
        """Extract emails from raw text using regex.

        Args:
            text: Raw text (e.g. scraped web page content).

        Returns:
            List of unique valid email addresses.
        """
        return extract_emails_from_text(text)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
