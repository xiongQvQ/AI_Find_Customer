"""Email verifier tool — verify email deliverability via MX record checks."""

from __future__ import annotations

import asyncio
import re
import socket
from typing import Optional


def _get_mx_records(domain: str) -> list[str]:
    """Resolve MX records for a domain using DNS.

    Returns list of MX hostnames sorted by priority (lowest first).
    Returns empty list if no MX records found.
    """
    try:
        import dns.resolver

        answers = dns.resolver.resolve(domain, "MX")
        mx_list = [(r.preference, str(r.exchange).rstrip(".")) for r in answers]
        mx_list.sort(key=lambda x: x[0])
        return [mx for _, mx in mx_list]
    except ImportError:
        # Fallback: use socket to check if domain resolves at all
        try:
            socket.getaddrinfo(domain, 25)
            return [domain]
        except socket.gaierror:
            return []
    except Exception:
        return []


def _has_valid_syntax(email: str) -> bool:
    """Check basic email syntax."""
    pattern = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
    return bool(pattern.match(email))


class EmailVerifierTool:
    """Verify email addresses using MX record checks.

    Verification levels:
    1. Syntax check (regex)
    2. Domain MX record check (DNS)

    Note: Full SMTP verification (RCPT TO) is not implemented
    to avoid being flagged as spam.
    """

    async def verify(self, email: str) -> dict:
        """Verify an email address.

        Args:
            email: Email address to verify.

        Returns:
            Dict with keys: email, valid_syntax, has_mx, is_deliverable, mx_records.
        """
        email = email.lower().strip()
        result = {
            "email": email,
            "valid_syntax": False,
            "has_mx": False,
            "is_deliverable": False,
            "mx_records": [],
        }

        # Step 1: Syntax check
        if not _has_valid_syntax(email):
            return result
        result["valid_syntax"] = True

        # Step 2: MX record check (run in thread to avoid blocking)
        domain = email.split("@")[1]
        loop = asyncio.get_event_loop()
        mx_records = await loop.run_in_executor(None, _get_mx_records, domain)

        result["mx_records"] = mx_records
        result["has_mx"] = len(mx_records) > 0
        result["is_deliverable"] = len(mx_records) > 0

        return result

    async def verify_batch(self, emails: list[str]) -> list[dict]:
        """Verify multiple emails concurrently.

        Args:
            emails: List of email addresses.

        Returns:
            List of verification results.
        """
        tasks = [self.verify(email) for email in emails]
        return await asyncio.gather(*tasks)
