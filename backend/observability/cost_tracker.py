"""Per-hunt cost and token usage tracker.

Design:
- One HuntCostTracker instance per hunt_id, stored in a module-level registry.
- LLMTool.generate() and react_loop() call record_llm_call() after every
  litellm.acompletion() to accumulate tokens + USD cost.
- search_node calls record_search_call() to count API calls per provider.
- At hunt completion, to_summary() produces a structured cost report that is
  written into the hunt result and persisted to disk.

Thread-safety: asyncio single-threaded event loop — no locks needed.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── Registry: hunt_id → HuntCostTracker ─────────────────────────────────────
_registry: dict[str, "HuntCostTracker"] = {}


def get_tracker(hunt_id: str) -> "HuntCostTracker":
    """Return the tracker for hunt_id, creating it if absent."""
    if hunt_id not in _registry:
        _registry[hunt_id] = HuntCostTracker(hunt_id=hunt_id)
    return _registry[hunt_id]


def remove_tracker(hunt_id: str) -> None:
    """Remove tracker from registry (call after saving to result)."""
    _registry.pop(hunt_id, None)


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class LLMCallRecord:
    """Aggregated token/cost stats for one (agent, model) bucket."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    call_count: int = 0

    def add(self, prompt: int, completion: int, cost: float) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion
        self.cost_usd += cost
        self.call_count += 1

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "call_count": self.call_count,
        }


@dataclass
class SearchCallRecord:
    """Count of search API calls per provider."""
    call_count: int = 0
    result_count: int = 0

    def add(self, results: int = 0) -> None:
        self.call_count += 1
        self.result_count += results

    def to_dict(self) -> dict:
        return {
            "call_count": self.call_count,
            "result_count": self.result_count,
        }


@dataclass
class HuntCostTracker:
    """Tracks all LLM + search API costs for a single hunt."""

    hunt_id: str

    # (agent_name, model_name) → LLMCallRecord
    _llm: dict[tuple[str, str], LLMCallRecord] = field(
        default_factory=lambda: defaultdict(LLMCallRecord)
    )

    # provider_name → SearchCallRecord
    _search: dict[str, SearchCallRecord] = field(
        default_factory=lambda: defaultdict(SearchCallRecord)
    )

    # per-round totals: round_number → {"cost_usd": float, "total_tokens": int}
    _rounds: dict[int, dict[str, float]] = field(
        default_factory=lambda: defaultdict(lambda: {"cost_usd": 0.0, "total_tokens": 0})
    )

    def record_llm_call(
        self,
        *,
        agent: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        hunt_round: int = 0,
    ) -> None:
        """Record one LLM call's token usage and cost."""
        key = (agent, model)
        self._llm[key].add(prompt_tokens, completion_tokens, cost_usd)
        self._rounds[hunt_round]["cost_usd"] += cost_usd
        self._rounds[hunt_round]["total_tokens"] += prompt_tokens + completion_tokens
        logger.debug(
            "[CostTracker] hunt=%s agent=%s model=%s prompt=%d completion=%d cost=$%.6f",
            self.hunt_id[:8], agent, model, prompt_tokens, completion_tokens, cost_usd,
        )

    def record_search_call(
        self,
        *,
        provider: str,
        result_count: int = 0,
    ) -> None:
        """Record one search API call."""
        self._search[provider].add(result_count)

    # ── Aggregated views ─────────────────────────────────────────────────

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self._llm.values())

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self._llm.values())

    @property
    def total_llm_calls(self) -> int:
        return sum(r.call_count for r in self._llm.values())

    def by_agent(self) -> dict[str, dict]:
        """Aggregate cost/tokens grouped by agent name."""
        result: dict[str, dict[str, Any]] = {}
        for (agent, model), rec in self._llm.items():
            if agent not in result:
                result[agent] = {
                    "prompt_tokens": 0, "completion_tokens": 0,
                    "total_tokens": 0, "cost_usd": 0.0, "call_count": 0,
                    "models": {},
                }
            r = result[agent]
            r["prompt_tokens"] += rec.prompt_tokens
            r["completion_tokens"] += rec.completion_tokens
            r["total_tokens"] += rec.total_tokens
            r["cost_usd"] += rec.cost_usd
            r["call_count"] += rec.call_count
            r["models"][model] = rec.to_dict()
        # Round floats
        for a in result.values():
            a["cost_usd"] = round(a["cost_usd"], 6)
        return result

    def by_round(self) -> dict[int, dict]:
        """Per-round cost/token totals."""
        return {
            rnd: {
                "cost_usd": round(v["cost_usd"], 6),
                "total_tokens": int(v["total_tokens"]),
            }
            for rnd, v in sorted(self._rounds.items())
        }

    def search_summary(self) -> dict[str, dict]:
        """Search API call counts per provider."""
        return {provider: rec.to_dict() for provider, rec in self._search.items()}

    def to_summary(self) -> dict:
        """Full cost summary — written into hunt result."""
        n_rounds = max((r for r in self._rounds if r > 0), default=0)
        avg_cost = (self.total_cost_usd / n_rounds) if n_rounds > 0 else 0.0
        return {
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_tokens": self.total_tokens,
            "total_llm_calls": self.total_llm_calls,
            "rounds_completed": n_rounds,
            "avg_cost_per_round_usd": round(avg_cost, 6),
            "by_agent": self.by_agent(),
            "by_round": self.by_round(),
            "search_api": self.search_summary(),
        }
