"""Tests for observability/cost_tracker.py — CostTracker unit tests."""

import pytest

from observability.cost_tracker import (
    HuntCostTracker,
    get_tracker,
    remove_tracker,
    _registry,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure each test starts with a clean registry."""
    _registry.clear()
    yield
    _registry.clear()


# ── HuntCostTracker unit tests ───────────────────────────────────────────────

class TestHuntCostTrackerLLM:
    def test_record_single_llm_call(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(
            agent="keyword_gen", model="gpt-4o-mini",
            prompt_tokens=100, completion_tokens=50, cost_usd=0.001,
        )
        assert t.total_tokens == 150
        assert t.total_llm_calls == 1
        assert abs(t.total_cost_usd - 0.001) < 1e-9

    def test_accumulates_multiple_calls(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=200, completion_tokens=100, cost_usd=0.01)
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=150, completion_tokens=80, cost_usd=0.008)
        assert t.total_tokens == 530
        assert t.total_llm_calls == 2
        assert abs(t.total_cost_usd - 0.018) < 1e-9

    def test_by_agent_groups_correctly(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.001)
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=200, completion_tokens=100, cost_usd=0.01)
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=80, completion_tokens=40, cost_usd=0.0008)

        by_agent = t.by_agent()
        assert "keyword_gen" in by_agent
        assert "insight" in by_agent
        assert by_agent["keyword_gen"]["total_tokens"] == 270
        assert by_agent["keyword_gen"]["call_count"] == 2
        assert by_agent["insight"]["total_tokens"] == 300
        assert by_agent["insight"]["call_count"] == 1

    def test_by_agent_includes_model_breakdown(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="lead_extract", model="gpt-4o",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.005)
        by_agent = t.by_agent()
        assert "gpt-4o" in by_agent["lead_extract"]["models"]

    def test_by_round_tracks_per_round(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.001, hunt_round=1)
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=120, completion_tokens=60, cost_usd=0.0012, hunt_round=2)
        t.record_llm_call(agent="lead_extract", model="gpt-4o",
                          prompt_tokens=200, completion_tokens=100, cost_usd=0.01, hunt_round=1)

        by_round = t.by_round()
        assert 1 in by_round
        assert 2 in by_round
        assert by_round[1]["total_tokens"] == 450  # 150 + 300
        assert abs(by_round[1]["cost_usd"] - 0.011) < 1e-9
        assert by_round[2]["total_tokens"] == 180

    def test_zero_cost_recorded_safely(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.0)
        assert t.total_cost_usd == 0.0
        assert t.total_tokens == 150

    def test_multiple_models_same_agent(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="lead_extract", model="gpt-4o",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.005)
        t.record_llm_call(agent="lead_extract", model="gpt-4o-mini",
                          prompt_tokens=80, completion_tokens=40, cost_usd=0.001)
        by_agent = t.by_agent()
        assert by_agent["lead_extract"]["call_count"] == 2
        assert len(by_agent["lead_extract"]["models"]) == 2


class TestHuntCostTrackerSearch:
    def test_record_search_call(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_search_call(provider="google", result_count=10)
        t.record_search_call(provider="google", result_count=8)
        t.record_search_call(provider="baidu", result_count=5)

        summary = t.search_summary()
        assert "google" in summary
        assert "baidu" in summary
        assert summary["google"]["call_count"] == 2
        assert summary["google"]["result_count"] == 18
        assert summary["baidu"]["call_count"] == 1
        assert summary["baidu"]["result_count"] == 5

    def test_search_summary_empty(self):
        t = HuntCostTracker(hunt_id="h1")
        assert t.search_summary() == {}


class TestHuntCostTrackerSummary:
    def test_to_summary_structure(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.001, hunt_round=1)
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=200, completion_tokens=100, cost_usd=0.01, hunt_round=0)
        t.record_search_call(provider="google", result_count=10)

        s = t.to_summary()
        assert "total_cost_usd" in s
        assert "total_tokens" in s
        assert "total_llm_calls" in s
        assert "rounds_completed" in s
        assert "avg_cost_per_round_usd" in s
        assert "by_agent" in s
        assert "by_round" in s
        assert "search_api" in s

    def test_to_summary_totals(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.001, hunt_round=1)
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=200, completion_tokens=100, cost_usd=0.01, hunt_round=1)

        s = t.to_summary()
        assert s["total_tokens"] == 450
        assert s["total_llm_calls"] == 2
        assert abs(s["total_cost_usd"] - 0.011) < 1e-9

    def test_avg_cost_per_round(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.002, hunt_round=1)
        t.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.002, hunt_round=2)

        s = t.to_summary()
        assert s["rounds_completed"] == 2
        assert abs(s["avg_cost_per_round_usd"] - 0.002) < 1e-9

    def test_empty_tracker_summary_safe(self):
        t = HuntCostTracker(hunt_id="h1")
        s = t.to_summary()
        assert s["total_cost_usd"] == 0.0
        assert s["total_tokens"] == 0
        assert s["total_llm_calls"] == 0
        assert s["rounds_completed"] == 0
        assert s["avg_cost_per_round_usd"] == 0.0
        assert s["by_agent"] == {}
        assert s["by_round"] == {}
        assert s["search_api"] == {}

    def test_cost_usd_rounded_to_6_decimals(self):
        t = HuntCostTracker(hunt_id="h1")
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=1, completion_tokens=1, cost_usd=0.0000001234567)
        s = t.to_summary()
        # Should be rounded to 6 decimal places
        assert len(str(s["total_cost_usd"]).split(".")[-1]) <= 6


# ── Registry tests ───────────────────────────────────────────────────────────

class TestRegistry:
    def test_get_tracker_creates_new(self):
        t = get_tracker("hunt-abc")
        assert t.hunt_id == "hunt-abc"
        assert "hunt-abc" in _registry

    def test_get_tracker_returns_same_instance(self):
        t1 = get_tracker("hunt-xyz")
        t2 = get_tracker("hunt-xyz")
        assert t1 is t2

    def test_remove_tracker(self):
        get_tracker("hunt-del")
        assert "hunt-del" in _registry
        remove_tracker("hunt-del")
        assert "hunt-del" not in _registry

    def test_remove_nonexistent_tracker_safe(self):
        remove_tracker("does-not-exist")  # Should not raise

    def test_tracker_accumulates_across_calls(self):
        t = get_tracker("hunt-acc")
        t.record_llm_call(agent="insight", model="gpt-4o",
                          prompt_tokens=100, completion_tokens=50, cost_usd=0.005)
        # Get same tracker again and record more
        t2 = get_tracker("hunt-acc")
        t2.record_llm_call(agent="keyword_gen", model="gpt-4o-mini",
                           prompt_tokens=80, completion_tokens=40, cost_usd=0.001)
        assert t.total_llm_calls == 2
        assert t.total_tokens == 270
