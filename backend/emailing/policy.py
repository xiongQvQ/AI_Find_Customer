"""Lead -> email target selection rules."""

from __future__ import annotations

import re
from typing import Any

_GENERIC_LOCAL_PARTS = {
    "info", "sales", "contact", "office", "hello", "support", "admin", "service",
}

_TITLE_PRIORITIES = [
    "purchasing",
    "procurement",
    "sourcing",
    "owner",
    "ceo",
    "sales director",
    "sales manager",
    "product",
    "engineering",
    "general manager",
]


def _normalize_email(email: str) -> str:
    return re.sub(r"\s*\(inferred\)\s*$", "", str(email or ""), flags=re.I).strip().lower()


def _email_status(email: str) -> str:
    text = str(email or "").strip()
    if not text:
        return "none"
    if re.search(r"\(inferred\)\s*$", text, flags=re.I) or text.lower() == "inferred":
        return "inferred-from-pattern"
    return "verified"


def _title_rank(title: str) -> int:
    normalized = str(title or "").lower()
    for idx, keyword in enumerate(_TITLE_PRIORITIES):
        if keyword in normalized:
            return idx
    return len(_TITLE_PRIORITIES)


def choose_email_target(lead: dict[str, Any]) -> dict[str, str]:
    """Choose the best outbound target email for a lead."""
    decision_makers = lead.get("decision_makers") or []
    ranked_dm: list[tuple[int, int, dict[str, Any], str, str]] = []
    for dm in decision_makers:
        if not isinstance(dm, dict):
            continue
        email = _normalize_email(str(dm.get("email", "") or ""))
        if not email or "@" not in email:
            continue
        status = _email_status(str(dm.get("email", "") or ""))
        status_rank = 0 if status == "verified" else 1
        ranked_dm.append((status_rank, _title_rank(str(dm.get("title", "") or "")), dm, email, status))

    if ranked_dm:
        ranked_dm.sort(key=lambda item: (item[0], item[1], item[3], item[2].get("name", "")))
        _, _, dm, email, status = ranked_dm[0]
        return {
            "target_email": email,
            "target_name": str(dm.get("name", "") or ""),
            "target_title": str(dm.get("title", "") or ""),
            "target_type": f"decision_maker_{status.replace('-', '_')}",
        }

    company_emails = []
    for email in lead.get("emails") or []:
        normalized = _normalize_email(str(email or ""))
        if "@" not in normalized:
            continue
        local = normalized.split("@", 1)[0]
        company_emails.append((0 if local in _GENERIC_LOCAL_PARTS else 1, normalized))
    if company_emails:
        company_emails.sort(key=lambda item: (item[0], item[1]))
        return {
            "target_email": company_emails[0][1],
            "target_name": str(lead.get("contact_person", "") or ""),
            "target_title": "",
            "target_type": "generic_company_email" if company_emails[0][0] == 0 else "company_email",
        }

    return {"target_email": "", "target_name": "", "target_title": "", "target_type": "none"}

