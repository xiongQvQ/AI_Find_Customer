"""ParseDescriptionAgent — extracts structured hunt parameters from a free-form description.

When a user types something like:
  "我想找东南亚的旅行社公司"
  "Looking for US importers of industrial LED lighting"
  "帮我找巴西的太阳能经销商"

This agent extracts:
  - target_regions: ["东南亚"] / ["US"] / ["Brazil"]
  - target_customer_profile: "旅行社" / "importers of industrial LED" / "solar energy distributors"
  - product_keywords: [] / ["industrial LED lighting"] / ["solar panels"]
  - description_insight: short summary of what was understood (for prompt enrichment)

The extracted values MERGE with (not overwrite) any user-supplied fields —
e.g. if the user also typed a website URL, both the URL and description are used.

This node runs ONLY when state.description is non-empty.
It runs BEFORE insight_node so that InsightAgent receives enriched state.
"""

from __future__ import annotations

import logging

from config.settings import get_settings
from graph.state import HuntState
from tools.llm_client import LLMTool

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a B2B lead hunting assistant. A user has typed a free-form description
of what they want to find. Your job is to extract structured parameters from this description.

Extract the following fields:
- target_regions: list of geographic regions/countries/cities mentioned or implied
- target_customer_profile: description of the ideal customer type (business role, industry)
- product_keywords: list of specific products or services mentioned
- company_name: company name if mentioned (empty string if not)
- description_insight: 1-2 sentence summary of what was understood (in English)

## Rules
- target_regions: be specific. "东南亚" → ["Southeast Asia"], "南美" → ["South America"],
  "巴西" → ["Brazil"], "全球" → ["Global"]. If no region mentioned, return [].
- target_customer_profile: capture the customer TYPE, not the user's own company.
  "找旅行社" → "travel agencies and tour operators"
  "找经销商" → "distributors and resellers"
  "找进口商" → "importers and trading companies"
  If already detailed in the description, use the full description.
- product_keywords: specific products/services. "LED灯" → ["LED lighting"], "太阳能板" → ["solar panels"].
  If no specific product mentioned, return [].
- Always output in this exact JSON format, no markdown fences.

Output JSON:
{
  "target_regions": ["..."],
  "target_customer_profile": "...",
  "product_keywords": ["..."],
  "company_name": "...",
  "description_insight": "..."
}"""


async def parse_description_node(state: HuntState) -> dict:
    """LangGraph node: parse free-form description into structured hunt parameters.

    Runs only when state.description is non-empty.
    Merges extracted values into state — does NOT overwrite user-provided fields.
    """
    description = (state.get("description") or "").strip()
    if not description:
        return {"current_stage": "parse_description"}

    logger.info("[ParseDescription] Parsing: %r", description[:100])

    llm = LLMTool(
        hunt_id=state.get("hunt_id", ""),
        agent="parse_description",
        hunt_round=0,
    )

    try:
        raw = await llm.generate(
            description,
            system=_SYSTEM_PROMPT,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        from tools.llm_output import parse_json
        parsed = parse_json(raw, context="ParseDescriptionAgent")

        if not parsed or not isinstance(parsed, dict):
            logger.warning("[ParseDescription] Failed to parse LLM output, using description as-is")
            return {"current_stage": "parse_description"}

        updates: dict = {"current_stage": "parse_description"}

        # ── Merge target_regions (description supplements user input) ────
        extracted_regions = parsed.get("target_regions") or []
        existing_regions = state.get("target_regions") or []
        if extracted_regions and not existing_regions:
            updates["target_regions"] = extracted_regions
            logger.info("[ParseDescription] Set regions: %s", extracted_regions)
        elif extracted_regions and existing_regions:
            # Merge: user-specified first, then description-extracted
            merged = list(existing_regions)
            for r in extracted_regions:
                if r not in merged:
                    merged.append(r)
            updates["target_regions"] = merged

        # ── Merge target_customer_profile ─────────────────────────────────
        extracted_profile = (parsed.get("target_customer_profile") or "").strip()
        existing_profile = (state.get("target_customer_profile") or "").strip()
        if extracted_profile and not existing_profile:
            updates["target_customer_profile"] = extracted_profile
            logger.info("[ParseDescription] Set customer profile: %r", extracted_profile)

        # ── Merge product_keywords ────────────────────────────────────────
        extracted_kw = [k for k in (parsed.get("product_keywords") or []) if isinstance(k, str) and k.strip()]
        existing_kw = state.get("product_keywords") or []
        if extracted_kw and not existing_kw:
            updates["product_keywords"] = extracted_kw
            logger.info("[ParseDescription] Set product keywords: %s", extracted_kw)
        elif extracted_kw and existing_kw:
            merged_kw = list(existing_kw)
            for k in extracted_kw:
                if k not in merged_kw:
                    merged_kw.append(k)
            updates["product_keywords"] = merged_kw

        # ── Inject description_insight into insight prompt via website_url hint ──
        # We use a special field so InsightAgent can include it in its prompt
        description_insight = parsed.get("description_insight", "")
        if description_insight:
            updates["description_insight"] = description_insight

        logger.info(
            "[ParseDescription] Done — regions=%s, profile=%r, keywords=%s",
            updates.get("target_regions", existing_regions),
            updates.get("target_customer_profile", existing_profile),
            updates.get("product_keywords", existing_kw),
        )

    except Exception as e:
        logger.error("[ParseDescription] Failed: %s", e)
    finally:
        await llm.close()

    return updates
