"""LangGraph state definition — the single source of truth flowing through the graph."""

from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph.message import add_messages


class HuntState(TypedDict):
    """
    LangGraph State — replaces the original HuntSession + SharedContext.

    Every node reads from and writes to this state dict.
    Fields are grouped by pipeline stage and loop control.
    """

    # ── User input ──────────────────────────────────────────────────────
    website_url: str
    product_keywords: list[str]
    target_customer_profile: str           # e.g. '批发商和代理商', 'distributors'
    description: str                       # free-form natural language description of hunt goal
    target_regions: list[str]
    uploaded_files: list[str]
    target_lead_count: int
    max_rounds: int
    min_new_leads_threshold: int
    enable_email_craft: bool               # whether to generate emails after hunting

    # ── Stage 1: Insight (runs once) ────────────────────────────────────
    insight: Optional[dict]

    # ── Stage 2: Keywords (per-round, small batch 5-8) ──────────────────
    keywords: list[str]                     # current round keywords
    used_keywords: list[str]                # all keywords used across rounds

    # ── Stage 3: Search results ─────────────────────────────────────────
    search_results: list[dict]              # accumulated across rounds (trimmed on resume)
    seen_urls: list[str]                    # deduplicated URL set — survives resume compression
    matched_platforms: list[dict]           # B2B platforms matched to ICP
    keyword_search_stats: dict[str, Any]    # per-keyword search effectiveness

    # ── Stage 4: Leads (accumulated across rounds) ──────────────────────
    leads: list[dict]

    # ── Stage 5: Email sequences ────────────────────────────────────────
    email_sequences: list[dict]

    # ── Loop control ────────────────────────────────────────────────────
    hunt_round: int                         # current round number (1, 2, 3...)
    prev_round_lead_count: int              # lead count at end of previous round
    round_feedback: Optional[dict]          # feedback summary for KeywordGenAgent

    # ── Metadata ────────────────────────────────────────────────────────
    current_stage: str
    hunt_id: str                             # hunt identifier for cost tracking
    messages: Annotated[list, add_messages]  # agent reasoning trace
