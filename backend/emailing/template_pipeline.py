"""Template extraction and composition helpers for outbound email generation."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from tools.llm_output import parse_json


logger = logging.getLogger(__name__)


TEMPLATE_EXTRACTOR_SYSTEM = """You analyze previous outbound emails and extract a reusable style/template profile.

Do not write the final outbound sequence.
Return JSON only.
Focus on:
- tone and formality
- subject-line style
- opening pattern
- value proposition framing
- CTA style
- claims to avoid
- reusable structure
"""


TEMPLATE_COMPOSER_SYSTEM = """You design a reusable outbound email template plan.

Inputs may include seller ICP, buyer ICP, website insight, and optional user-provided email examples.
Do not write the final 3-email sequence yet.
Return JSON only.
"""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clip(value: str, *, limit: int = 1600) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_fallback_template_profile(
    *,
    examples: list[str],
    lead: dict[str, Any],
    insight: dict[str, Any],
) -> dict[str, Any]:
    products = [str(item).strip() for item in (insight.get("products") or []) if str(item).strip()]
    example_signals = [_clip(item, limit=220) for item in examples[:3] if _clean_text(item)]
    return {
        "source": "user_examples" if example_signals else "auto_generated",
        "tone": "professional",
        "formality": "professional",
        "subject_style": "specific and low-pressure",
        "opening_style": "reference buyer relevance before introducing the seller",
        "value_prop_style": "focus on buyer fit and concrete use cases",
        "cta_style": "ask a light qualification question",
        "claims_to_avoid": [
            "Avoid unverifiable superlatives",
            "Avoid sounding like a bulk blast",
        ],
        "preferred_structure": [
            "buyer relevance",
            "seller introduction",
            "specific fit angle",
            "low-friction CTA",
        ],
        "example_signals": example_signals,
        "template_notes": (
            f"Buyer company: {lead.get('company_name', '') or 'unknown'}. "
            f"Industry: {lead.get('industry', '') or 'unknown'}. "
            f"Relevant products: {', '.join(products[:3]) or 'unknown'}."
        ),
    }


async def extract_template_profile(
    llm: Any,
    *,
    examples: list[str],
    lead: dict[str, Any],
    insight: dict[str, Any],
    notes: str = "",
) -> dict[str, Any]:
    fallback = build_fallback_template_profile(examples=examples, lead=lead, insight=insight)
    if not examples:
        return fallback

    prompt = (
        f"<seller>\n"
        f"name: {insight.get('company_name', '')}\n"
        f"products: {json.dumps(insight.get('products', []), ensure_ascii=False)}\n"
        f"</seller>\n\n"
        f"<buyer>\n"
        f"company_name: {lead.get('company_name', '')}\n"
        f"industry: {lead.get('industry', '')}\n"
        f"description: {lead.get('description', '')}\n"
        f"website: {lead.get('website', '')}\n"
        f"</buyer>\n\n"
        f"<notes>\n{notes}\n</notes>\n\n"
        f"<examples>\n{json.dumps([_clip(item) for item in examples[:5]], ensure_ascii=False)}\n</examples>\n\n"
        f"Extract a reusable style/template profile from the examples, adapted to this buyer context."
    )
    try:
        raw = await llm.generate(
            prompt,
            system=TEMPLATE_EXTRACTOR_SYSTEM,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        parsed = parse_json(raw, context="email_template_extractor")
        if isinstance(parsed, dict):
            return fallback | parsed | {"source": "user_examples"}
    except Exception as exc:
        logger.debug("[EmailTemplate] Extractor failed for %s: %s", lead.get("company_name"), exc)
    return fallback


async def compose_template_plan(
    llm: Any,
    *,
    lead: dict[str, Any],
    insight: dict[str, Any],
    template_profile: dict[str, Any],
    notes: str = "",
) -> dict[str, Any]:
    fallback = {
        "template_source": str(template_profile.get("source", "auto_generated") or "auto_generated"),
        "recipient_profile": str(lead.get("industry", "") or "Potential distributor or buyer"),
        "buyer_relevance_points": [
            str(lead.get("industry", "") or "Operates in a relevant industry"),
            str(lead.get("description", "") or "Public profile suggests buyer relevance"),
        ],
        "seller_value_points": [str(item) for item in (insight.get("products") or [])[:3]]
        or ["Relevant product portfolio for buyer conversations"],
        "proof_points": list((insight.get("value_propositions") or [])[:3]),
        "cta_strategy": "Ask a low-friction qualification question.",
        "tone_guidance": str(template_profile.get("tone", "professional") or "professional"),
        "template_instructions": [
            "Keep the copy concise and commercially credible",
            "Mention buyer relevance before seller credentials",
            "Use one clear CTA",
        ],
        "claims_to_avoid": list(template_profile.get("claims_to_avoid", [])),
    }
    prompt = (
        f"<seller>\n"
        f"name: {insight.get('company_name', '')}\n"
        f"products: {json.dumps(insight.get('products', []), ensure_ascii=False)}\n"
        f"industries: {json.dumps(insight.get('industries', []), ensure_ascii=False)}\n"
        f"summary: {insight.get('summary', '')}\n"
        f"value_propositions: {json.dumps(insight.get('value_propositions', []), ensure_ascii=False)}\n"
        f"</seller>\n\n"
        f"<buyer>\n"
        f"company_name: {lead.get('company_name', '')}\n"
        f"website: {lead.get('website', '')}\n"
        f"industry: {lead.get('industry', '')}\n"
        f"description: {lead.get('description', '')}\n"
        f"country_code: {lead.get('country_code', '')}\n"
        f"</buyer>\n\n"
        f"<template_profile>\n{json.dumps(template_profile, ensure_ascii=False)}\n</template_profile>\n\n"
        f"<notes>\n{notes}\n</notes>\n\n"
        f"Design a reusable outbound template plan for this buyer."
    )
    try:
        raw = await llm.generate(
            prompt,
            system=TEMPLATE_COMPOSER_SYSTEM,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        parsed = parse_json(raw, context="email_template_plan")
        if isinstance(parsed, dict):
            return fallback | parsed
    except Exception as exc:
        logger.debug("[EmailTemplate] Composer failed for %s: %s", lead.get("company_name"), exc)
    return fallback
