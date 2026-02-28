"""KeywordGenAgent — generates 5-8 search keywords per round, adapting via per-keyword feedback."""

from __future__ import annotations

import json
import logging
from typing import Any

from config.settings import get_settings
from graph.state import HuntState
from tools.llm_client import LLMTool
from agents.search_agent import _REGION_GEO

logger = logging.getLogger(__name__)

KEYWORD_GEN_SYSTEM_PROMPT = """You are an expert B2B keyword strategist. Generate search keywords to find potential B2B buyers, distributors, importers, and wholesalers for a specific product.

## Keyword Dimension Coverage
Each batch of {n} keywords MUST cover multiple dimensions — do NOT generate all keywords from the same dimension:

1. **Product + buyer role** — e.g. "solar inverter distributor Germany", "PV module importer Poland"
2. **Industry + application** — e.g. "renewable energy wholesaler Europe", "off-grid solar installer Italy"
3. **Value proposition** — e.g. "high efficiency solar panel supplier", "low voltage inverter OEM partner"
4. **Buyer type** — e.g. "electrical equipment wholesale company", "energy storage system reseller"
5. **Region + trade term** — e.g. "solar products import export Spain", "photovoltaic dealer Eastern Europe"
6. **B2B platform** — e.g. "site:europages.com solar inverter", "site:kompass.com PV distributor"
7. **Certification/standard** — e.g. "CE certified solar inverter buyer", "IEC 62109 compliant distributor"

## Rules
1. Generate exactly {n} keywords as a JSON array of strings.
2. Each keyword must be a specific, search-ready phrase (3-8 words).
3. Do NOT repeat any previously used keywords.
4. Every keyword MUST target the specified regions — never generate keywords for other regions.
5. Spread keywords across at least 4 different dimensions above.
6. If feedback is provided: generate MORE keywords similar to high-performing ones, AVOID patterns of low-performing ones, and try UNTESTED dimensions.
7. Prefer long-tail specific phrases over generic ones — they find more targeted leads.

## Local Language Requirement
{local_language_instruction}

Output MUST be a valid JSON object with a "keywords" key containing an array of strings:
{{"keywords": ["solar inverter distributor Germany", "PV module importer Poland", "renewable energy wholesaler Europe", ...]}}"""


# ── Language detection ───────────────────────────────────────────────────
# Maps hl language codes to human-readable names for prompt injection
_HL_TO_LANGUAGE: dict[str, str] = {
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "cs": "Czech",
    "ro": "Romanian",
    "hu": "Hungarian",
    "tr": "Turkish",
    "ru": "Russian",
    "uk": "Ukrainian",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "el": "Greek",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-cn": "Chinese (Simplified)",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ar": "Arabic",
}


def _detect_local_languages(target_regions: list[str]) -> list[str]:
    """Detect ALL non-English languages across all target regions.

    Returns a list of unique human-readable language names (e.g. ['German', 'Polish']),
    or an empty list if all regions are English-speaking or unrecognized.
    """
    seen: set[str] = set()
    languages: list[str] = []
    for region in target_regions:
        key = region.strip().lower()
        geo = _REGION_GEO.get(key, {})
        hl = geo.get("hl", "en")
        if hl != "en" and hl in _HL_TO_LANGUAGE:
            lang = _HL_TO_LANGUAGE[hl]
            if lang not in seen:
                seen.add(lang)
                languages.append(lang)
    return languages


def _build_prompt(state: HuntState) -> str:
    """Build the keyword generation prompt from state."""
    parts = []

    # Full insight context
    insight = state.get("insight")
    if insight and isinstance(insight, dict):
        insight_lines = ["## Company & Product Insight (use ALL of this to generate relevant keywords)"]
        if insight.get("company_name"):
            insight_lines.append(f"Company: {insight['company_name']}")
        if insight.get("products"):
            insight_lines.append(f"Products: {', '.join(insight['products'])}")
        if insight.get("industries"):
            insight_lines.append(f"Target industries: {', '.join(insight['industries'])}")
        if insight.get("value_propositions"):
            insight_lines.append(f"Value propositions: {'; '.join(insight['value_propositions'])}")
        if insight.get("target_customer_profile"):
            insight_lines.append(f"Ideal customer profile: {insight['target_customer_profile']}")
        if insight.get("summary"):
            insight_lines.append(f"Company summary: {insight['summary']}")
        # Seed keywords from insight (high-quality starting points)
        seed_kw = insight.get("recommended_keywords_seed", [])
        if seed_kw:
            insight_lines.append(f"Insight-recommended seed keywords (use as inspiration, not verbatim): {', '.join(seed_kw[:10])}")
        parts.append("\n".join(insight_lines))

    # Target customer profile (highest priority for buyer-type keywords)
    target_profile = state.get("target_customer_profile", "").strip()
    if target_profile:
        parts.append(
            f"## Target Customer Profile (CRITICAL — focus keywords on finding these types)\n"
            f"{target_profile}\n"
            f"Generate keywords that specifically target these customer types. "
            f"For example, if the profile is '批发商和代理商', include keywords like "
            f"'[product] 批发商', '[product] distributor', '[product] wholesaler', etc."
        )

    # User-provided seed keywords (products)
    if state.get("product_keywords"):
        parts.append(f"## Product Keywords (seed)\n{', '.join(state['product_keywords'])}")

    # Target regions — mandatory constraint
    target_regions = state.get("target_regions", [])
    if target_regions:
        parts.append(
            f"## Target Regions (MANDATORY — ALL keywords MUST target these regions ONLY)\n"
            f"{', '.join(target_regions)}\n"
            f"CRITICAL: Every keyword you generate MUST be focused on finding buyers/distributors "
            f"in these specific regions. Do NOT generate keywords targeting other regions (e.g. China, "
            f"Asia, Middle East) unless they are explicitly listed above."
        )

    # Previously used keywords — only show last 2 rounds to limit token usage.
    # Older keywords are already deduplicated in code before LLM call.
    used = state.get("used_keywords", [])
    n_per_round = state.get("keywords_per_round", 8)
    recent_used = used[-(n_per_round * 2):] if len(used) > n_per_round * 2 else used
    if recent_used:
        parts.append(
            f"## Recently Used Keywords (DO NOT repeat — older ones also excluded in code)\n"
            f"{', '.join(recent_used)}"
        )

    # Per-keyword feedback from evaluate
    feedback = state.get("round_feedback")
    if feedback and isinstance(feedback, dict):
        parts.append(f"## Round {feedback.get('round', '?')} Performance Feedback")
        parts.append(
            f"Progress: {feedback.get('total_leads', 0)} leads collected "
            f"/ {feedback.get('target', 200)} target "
            f"(+{feedback.get('new_leads_this_round', 0)} this round)"
        )

        # Full per-keyword performance table
        kw_perf = feedback.get("keyword_performance", [])
        if kw_perf:
            perf_lines = [
                "### Per-Keyword Performance",
                "| Keyword | Search Results | Leads Found | Effectiveness |",
                "|---------|---------------|-------------|---------------|",
            ]
            for kp in kw_perf:
                perf_lines.append(
                    f"| {kp.get('keyword', '')} | {kp.get('search_results', 0)} | "
                    f"{kp.get('leads_found', 0)} | {kp.get('effectiveness', 'unknown')} |"
                )
            parts.append("\n".join(perf_lines))

        best = feedback.get("best_keywords", [])
        worst = feedback.get("worst_keywords", [])
        if best:
            parts.append(f"HIGH performing (generate similar patterns): {', '.join(best)}")
        if worst:
            parts.append(f"LOW performing (avoid these patterns): {', '.join(worst)}")

        top_sources = feedback.get("top_sources", [])
        if top_sources:
            parts.append(f"Top lead sources this round: {', '.join(top_sources)}")

        industry_dist = feedback.get("industry_distribution", {})
        if industry_dist:
            parts.append(f"Industry distribution of leads found: {json.dumps(industry_dist)}")

        region_dist = feedback.get("region_distribution", {})
        if region_dist:
            parts.append(f"Region distribution of leads found: {json.dumps(region_dist)}")

        # Suggest untried dimensions if we have feedback
        parts.append(
            "## Strategy Hint\n"
            "Look at the performance table above. If product+buyer keywords are saturated, "
            "try industry+application, value-proposition, or B2B platform dimensions next."
        )

    return "\n\n".join(parts)


async def keyword_gen_node(state: HuntState) -> dict:
    """LangGraph node: generate 5-8 keywords per round using LLM + feedback.

    Returns:
        Dict with 'keywords' (current round) and 'used_keywords' (accumulated).
    """
    settings = get_settings()
    n_keywords = settings.default_keywords_per_round
    current_round = state.get("hunt_round", 1)
    used_count = len(state.get("used_keywords", []))

    logger.info("[KeywordGenAgent] Round %d — generating %d keywords (used so far: %d)",
                current_round, n_keywords, used_count)

    prompt = _build_prompt(state)

    # Code-level language detection: inject explicit instruction so LLM doesn't guess
    target_regions = state.get("target_regions", [])
    local_langs = _detect_local_languages(target_regions)
    if local_langs:
        langs_str = " and ".join(local_langs)
        per_lang_pct = 70 // len(local_langs)
        local_language_instruction = (
            f"The target regions use {langs_str} as primary language(s). "
            f"Generate approximately {per_lang_pct}% of keywords per local language "
            f"and the remainder in English. "
            f"This is essential to find local SMEs who may not have English websites."
        )
    else:
        local_language_instruction = (
            "The target region is English-speaking. Generate all keywords in English."
        )

    system = KEYWORD_GEN_SYSTEM_PROMPT.format(
        n=n_keywords,
        local_language_instruction=local_language_instruction,
    )

    llm = LLMTool(
        hunt_id=state.get("hunt_id", ""),
        agent="keyword_gen",
        hunt_round=state.get("hunt_round", 0),
    )
    try:
        raw = await llm.generate(
            prompt,
            system=system,
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        from tools.llm_output import parse_json
        parsed = parse_json(raw, context="KeywordGenAgent")
        if parsed is None:
            raise ValueError("Unparseable LLM output")

        # Handle both {"keywords": [...]} and bare [...]
        if isinstance(parsed, list):
            keywords = parsed
        elif isinstance(parsed, dict):
            keywords = parsed.get("keywords", [])
        else:
            keywords = []

        # Ensure strings and deduplicate against used
        used = set(kw.lower() for kw in state.get("used_keywords", []))
        keywords = [
            kw for kw in keywords
            if isinstance(kw, str) and kw.lower() not in used
        ][:n_keywords]

    except Exception as e:
        logger.error("KeywordGenAgent failed: %s", e)
        # Fallback: use seed keywords from insight
        insight = state.get("insight", {}) or {}
        keywords = insight.get("recommended_keywords_seed", [])[:n_keywords]
    finally:
        await llm.close()

    logger.info("[KeywordGenAgent] Generated %d keywords: %s", len(keywords), keywords)

    new_used = state.get("used_keywords", []) + keywords

    return {
        "keywords": keywords,
        "used_keywords": new_used,
        "current_stage": "keyword_gen",
    }
