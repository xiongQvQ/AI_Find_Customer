"""Evaluate node and conditional edge — lightweight, no LLM calls.

Responsibilities:
1. evaluate_progress(): compute per-keyword effectiveness, build round_feedback
2. should_continue_hunting(): decide "continue" or "finish" based on 3 stop conditions
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from config.settings import get_settings
from graph.state import HuntState

logger = logging.getLogger(__name__)


# ── Helper functions ────────────────────────────────────────────────────


def _get_top_sources(leads: list[dict], top_n: int = 5) -> list[str]:
    """Return the most common lead source keywords (by leads_found attribution)."""
    sources = [lead.get("source_keyword", "") for lead in leads if lead.get("source_keyword")]
    return [s for s, _ in Counter(sources).most_common(top_n)]


def _get_industry_distribution(leads: list[dict]) -> dict[str, int]:
    """Return industry → count mapping."""
    industries = [lead.get("industry", "Unknown") for lead in leads]
    return dict(Counter(industries))


def _get_region_distribution(leads: list[dict]) -> dict[str, int]:
    """Return country_code → count mapping."""
    regions = [lead.get("country_code", "unknown") for lead in leads if lead.get("country_code")]
    return dict(Counter(regions))


def _classify_effectiveness(leads_found: int, result_count: int = 0, avg_match_score: float = 0.0) -> str:
    """Classify keyword effectiveness based on leads found, precision, and quality.

    Dimensions:
    - leads_found: raw volume
    - precision: leads_found / result_count (avoids rewarding high-noise keywords)
    - avg_match_score: average quality of leads found
    """
    if leads_found == 0:
        return "low"
    precision = leads_found / max(result_count, 1)
    if leads_found >= 3 and precision >= 0.05 and avg_match_score >= 0.45:
        return "high"
    if leads_found >= 1 and (precision >= 0.03 or avg_match_score >= 0.35):
        return "medium"
    return "low"


def _build_keyword_performance(
    keyword_search_stats: dict[str, Any],
    leads: list[dict] | None = None,
) -> list[dict]:
    """Build per-keyword performance list from search stats.

    Includes precision and avg_match_score per keyword for richer feedback.
    """
    # Build a per-keyword match_score lookup from leads
    kw_scores: dict[str, list[float]] = {}
    for lead in (leads or []):
        kw = lead.get("source_keyword", "")
        score = lead.get("match_score", 0.0)
        if kw:
            kw_scores.setdefault(kw, []).append(float(score))

    performance = []
    for kw, stats in keyword_search_stats.items():
        result_count = stats.get("result_count", 0) if isinstance(stats, dict) else 0
        leads_found = stats.get("leads_found", 0) if isinstance(stats, dict) else 0
        scores = kw_scores.get(kw, [])
        avg_score = sum(scores) / len(scores) if scores else 0.0
        precision = leads_found / max(result_count, 1)
        performance.append({
            "keyword": kw,
            "search_results": result_count,
            "leads_found": leads_found,
            "precision": round(precision, 3),
            "avg_match_score": round(avg_score, 3),
            "effectiveness": _classify_effectiveness(leads_found, result_count, avg_score),
        })
    return performance


# ── Graph node ──────────────────────────────────────────────────────────


def evaluate_progress(state: HuntState) -> dict:
    """Evaluate hunting progress and build feedback for the next round.

    This is a pure-logic function — zero LLM calls.
    It computes per-keyword effectiveness and overall progress metrics.
    """
    leads = state.get("leads", [])
    current_leads = len(leads)
    target_leads = state.get("target_lead_count", 200)
    current_round = state.get("hunt_round", 1)

    prev_leads = state.get("prev_round_lead_count", 0)
    new_leads_this_round = current_leads - prev_leads

    logger.info("[Evaluate] Round %d — %d/%d leads (new this round: %d)",
                current_round, current_leads, target_leads, new_leads_this_round)

    # Per-keyword effectiveness (pass leads for match_score enrichment)
    keyword_stats = state.get("keyword_search_stats", {})
    keyword_performance = _build_keyword_performance(keyword_stats, leads)

    best_keywords = [kp["keyword"] for kp in keyword_performance if kp["effectiveness"] == "high"]
    worst_keywords = [kp["keyword"] for kp in keyword_performance if kp["effectiveness"] == "low"]

    round_feedback = {
        "round": current_round,
        "total_leads": current_leads,
        "target": target_leads,
        "new_leads_this_round": new_leads_this_round,
        "keyword_performance": keyword_performance,
        "best_keywords": best_keywords,
        "worst_keywords": worst_keywords,
        "keywords_used": state.get("used_keywords", []),
        "top_sources": _get_top_sources(leads),
        "industry_distribution": _get_industry_distribution(leads),
        "region_distribution": _get_region_distribution(leads),
    }

    logger.info("[Evaluate] Best keywords: %s | Worst keywords: %s",
                best_keywords[:3], worst_keywords[:3])

    return {
        "hunt_round": current_round + 1,
        "prev_round_lead_count": current_leads,
        "round_feedback": round_feedback,
        "current_stage": "evaluate",
    }


# ── Conditional edge ────────────────────────────────────────────────────


def should_continue_hunting(state: HuntState) -> str:
    """Conditional edge: decide whether to continue hunting or finish.

    Stop conditions (any one triggers finish):
    1. Target met: leads >= target_lead_count
    2. Max rounds exceeded: hunt_round > max_rounds
    3. Diminishing returns: new leads this round < configured min_threshold (default 5)

    Returns:
        "continue" — loop back to keyword_gen
        "finish"   — proceed to email_craft
    """
    leads = state.get("leads", [])
    current_leads = len(leads)
    target = state.get("target_lead_count", 200)
    current_round = state.get("hunt_round", 1)
    max_rounds = state.get("max_rounds", 10)

    # Read new_leads_this_round from round_feedback (computed by evaluate_progress
    # BEFORE prev_round_lead_count was updated).  Fallback to re-computing only
    # if round_feedback is missing (e.g. first invocation).
    feedback = state.get("round_feedback")
    if isinstance(feedback, dict):
        new_this_round = feedback.get("new_leads_this_round", current_leads)
        evaluated_round = feedback.get("round", 1)
    else:
        new_this_round = current_leads - state.get("prev_round_lead_count", 0)
        evaluated_round = current_round - 1 if current_round > 1 else 1

    # Stop condition 1: target met
    if current_leads >= target:
        logger.info("[Evaluate] FINISH — target met (%d >= %d)", current_leads, target)
        return "finish"

    # Stop condition 2: max rounds exceeded
    if current_round > max_rounds:
        logger.info("[Evaluate] FINISH — max rounds exceeded (%d > %d)", current_round, max_rounds)
        return "finish"

    # Stop condition 3: diminishing returns (skip on round 1)
    # Use the configured threshold directly so the behavior matches user-facing
    # settings and remains predictable across different target sizes.
    diminishing_threshold = max(
        1,
        int(state.get("min_new_leads_threshold", get_settings().min_new_leads_threshold)),
    )
    if evaluated_round > 1 and new_this_round < diminishing_threshold:
        logger.info(
            "[Evaluate] FINISH — diminishing returns (%d new leads < %d threshold in round %d)",
            new_this_round, diminishing_threshold, evaluated_round,
        )
        return "finish"

    logger.info("[Evaluate] CONTINUE — %d/%d leads, round %d/%d (new this round: %d)",
                current_leads, target, current_round, max_rounds, new_this_round)
    return "continue"
