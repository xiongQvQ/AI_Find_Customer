"""Centralized LLM output cleaning and schema validation.

Every LLM call that expects structured JSON should use these utilities
to ensure robustness against:
- Markdown code fences (```json ... ```)
- Extra text before/after JSON
- Missing required fields
- Wrong field types
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def clean_json(raw: str) -> str:
    """Strip markdown fences and surrounding text, return clean JSON string.

    Handles:
    - ```json\\n{...}\\n```
    - ```\\n{...}\\n```
    - Leading/trailing prose around JSON
    """
    text = raw.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove opening fence (```json or ```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return text


def parse_json(raw: str, *, context: str = "") -> dict | list | None:
    """Parse LLM output as JSON with multiple fallback strategies.

    1. Direct parse after cleaning markdown fences
    2. Regex extraction of outermost {...} or [...]
    3. Returns None if all strategies fail

    Args:
        raw: Raw LLM output string.
        context: Description for logging (e.g. "InsightAgent").

    Returns:
        Parsed dict/list, or None on failure.
    """
    if not raw or not raw.strip():
        logger.warning("[%s] Empty LLM output", context or "parse_json")
        return None

    clean = clean_json(raw)

    # Strategy 1: direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract outermost JSON object {...}
    m = re.search(r'\{.*\}', clean, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    # Strategy 3: extract outermost JSON array [...]
    m = re.search(r'\[.*\]', clean, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    logger.warning("[%s] Failed to parse JSON: %s", context or "parse_json", clean[:200])
    return None


def validate_dict(
    data: Any,
    required_fields: dict[str, type | tuple[type, ...]],
    *,
    defaults: dict[str, Any] | None = None,
    context: str = "",
) -> dict | None:
    """Validate a parsed dict has required fields with correct types.

    Missing fields are filled from `defaults` if provided.
    Wrong-type fields are coerced or replaced with defaults.

    Args:
        data: Parsed JSON (should be a dict).
        required_fields: Mapping of field_name → expected type(s).
        defaults: Default values for missing/invalid fields.
        context: Description for logging.

    Returns:
        Validated dict, or None if data is not a dict at all.
    """
    if not isinstance(data, dict):
        logger.warning("[%s] Expected dict, got %s", context, type(data).__name__)
        return None

    defaults = defaults or {}
    result = dict(data)

    for field, expected_type in required_fields.items():
        val = result.get(field)
        if val is None or not isinstance(val, expected_type):
            if field in defaults:
                result[field] = defaults[field]
            else:
                logger.debug("[%s] Field '%s' missing or wrong type (got %s, expected %s)",
                             context, field, type(val).__name__, expected_type)

    return result


# ── Per-agent schema definitions ──────────────────────────────────────────

INSIGHT_REQUIRED: dict[str, type | tuple[type, ...]] = {
    "company_name": str,
    "products": list,
    "industries": list,
    "value_propositions": list,
    "target_customer_profile": str,
    "negative_targeting_criteria": list,
    "recommended_regions": list,
    "recommended_keywords_seed": list,
    "summary": str,
}

INSIGHT_DEFAULTS: dict[str, Any] = {
    "company_name": "Unknown",
    "products": [],
    "industries": [],
    "value_propositions": [],
    "target_customer_profile": "",
    "negative_targeting_criteria": [],
    "recommended_regions": [],
    "recommended_keywords_seed": [],
    "summary": "",
}

LEAD_REQUIRED: dict[str, type | tuple[type, ...]] = {
    "company_name": str,
    "website": str,
    "emails": list,
    "phone_numbers": list,
    "social_media": dict,
    "match_score": (int, float),
}

LEAD_DEFAULTS: dict[str, Any] = {
    "is_valid_lead": False,
    "company_name": "",
    "website": "",
    "industry": "",
    "description": "",
    "emails": [],
    "phone_numbers": [],
    "social_media": {},
    "match_score": 0.0,
    "contact_person": None,
    "address": "",
    "country_code": "",
    "business_types": [],
}

EMAIL_SEQUENCE_REQUIRED: dict[str, type | tuple[type, ...]] = {
    "emails": list,
}

EMAIL_SEQUENCE_DEFAULTS: dict[str, Any] = {
    "emails": [],
}

CONTENT_EXTRACT_REQUIRED: dict[str, type | tuple[type, ...]] = {
    "companies": list,
}

CONTENT_EXTRACT_DEFAULTS: dict[str, Any] = {
    "companies": [],
}
