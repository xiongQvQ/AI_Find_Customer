"""Tests for graph/evaluate.py — stop conditions, per-keyword feedback, helpers."""

import pytest

from graph.evaluate import (
    _build_keyword_performance,
    _classify_effectiveness,
    _get_industry_distribution,
    _get_region_distribution,
    _get_top_sources,
    evaluate_progress,
    should_continue_hunting,
)


# ── Helper function tests ───────────────────────────────────────────────


class TestClassifyEffectiveness:
    def test_high(self):
        # leads_found >= 3, precision >= 0.05 (3/50=0.06), avg_score >= 0.45
        assert _classify_effectiveness(3, result_count=50, avg_match_score=0.6) == "high"
        assert _classify_effectiveness(5, result_count=20, avg_match_score=0.5) == "high"

    def test_medium(self):
        # leads_found >= 1, precision >= 0.03 OR score >= 0.35, but not both high thresholds
        assert _classify_effectiveness(1, result_count=10, avg_match_score=0.4) == "medium"
        # precision=2/50=0.04 >= 0.03 → medium (score below 0.45 so not high)
        assert _classify_effectiveness(2, result_count=50, avg_match_score=0.3) == "medium"

    def test_low_zero_leads(self):
        assert _classify_effectiveness(0) == "low"

    def test_low_poor_precision_and_score(self):
        # leads_found=1 but precision=0.01 and score=0.2 — both below medium thresholds
        assert _classify_effectiveness(1, result_count=100, avg_match_score=0.2) == "low"

    def test_backward_compat_defaults(self):
        # With only leads_found, precision=leads/1 which is high, but score=0 → medium
        assert _classify_effectiveness(1) == "medium"
        assert _classify_effectiveness(0) == "low"


class TestGetTopSources:
    def test_empty(self):
        assert _get_top_sources([]) == []

    def test_counts_correctly(self):
        leads = [
            {"source_keyword": "solar inverter distributor"},
            {"source_keyword": "solar inverter distributor"},
            {"source_keyword": "PV buyer Germany"},
            {"source_keyword": "solar inverter distributor"},
            {"source_keyword": "PV buyer Germany"},
            {"source_keyword": "renewable energy wholesaler"},
        ]
        result = _get_top_sources(leads, top_n=2)
        assert result[0] == "solar inverter distributor"
        assert result[1] == "PV buyer Germany"
        assert len(result) == 2

    def test_skips_empty_source_keyword(self):
        leads = [{"source_keyword": ""}, {"source_keyword": "kw1"}, {}]
        result = _get_top_sources(leads)
        assert result == ["kw1"]


class TestGetIndustryDistribution:
    def test_empty(self):
        assert _get_industry_distribution([]) == {}

    def test_counts(self):
        leads = [
            {"industry": "Solar"},
            {"industry": "Solar"},
            {"industry": "Electronics"},
        ]
        dist = _get_industry_distribution(leads)
        assert dist == {"Solar": 2, "Electronics": 1}

    def test_missing_industry_defaults_to_unknown(self):
        leads = [{"company": "X"}, {"industry": "Solar"}]
        dist = _get_industry_distribution(leads)
        assert dist["Unknown"] == 1
        assert dist["Solar"] == 1


class TestGetRegionDistribution:
    def test_empty(self):
        assert _get_region_distribution([]) == {}

    def test_counts(self):
        leads = [
            {"country_code": "de"},
            {"country_code": "de"},
            {"country_code": "fr"},
        ]
        dist = _get_region_distribution(leads)
        assert dist == {"de": 2, "fr": 1}

    def test_skips_empty_country(self):
        leads = [{"country_code": ""}, {"country_code": "us"}]
        dist = _get_region_distribution(leads)
        assert dist == {"us": 1}


class TestBuildKeywordPerformance:
    def test_empty(self):
        assert _build_keyword_performance({}) == []

    def test_builds_correctly(self):
        stats = {
            "solar inverter distributor": {"result_count": 25, "leads_found": 8},
            "PV buyer": {"result_count": 5, "leads_found": 0},
            "renewable energy supplier": {"result_count": 15, "leads_found": 2},
        }
        # Provide leads with match_scores so 'solar inverter distributor' gets high
        leads = [
            {"source_keyword": "solar inverter distributor", "match_score": 0.7}
            for _ in range(8)
        ] + [
            {"source_keyword": "renewable energy supplier", "match_score": 0.4}
            for _ in range(2)
        ]
        perf = _build_keyword_performance(stats, leads)
        assert len(perf) == 3

        by_kw = {p["keyword"]: p for p in perf}
        assert by_kw["solar inverter distributor"]["effectiveness"] == "high"
        assert by_kw["PV buyer"]["effectiveness"] == "low"
        assert by_kw["renewable energy supplier"]["effectiveness"] == "medium"
        # Verify new fields are present
        assert "precision" in by_kw["solar inverter distributor"]
        assert "avg_match_score" in by_kw["solar inverter distributor"]

    def test_handles_non_dict_stats(self):
        stats = {"bad_keyword": "not_a_dict"}
        perf = _build_keyword_performance(stats)
        assert perf[0]["search_results"] == 0
        assert perf[0]["effectiveness"] == "low"


# ── evaluate_progress tests ─────────────────────────────────────────────


class TestEvaluateProgress:
    def _make_state(self, **overrides):
        base = {
            "leads": [],
            "target_lead_count": 200,
            "hunt_round": 1,
            "prev_round_lead_count": 0,
            "used_keywords": [],
            "keyword_search_stats": {},
        }
        base.update(overrides)
        return base

    def test_increments_round(self):
        state = self._make_state(hunt_round=3)
        result = evaluate_progress(state)
        assert result["hunt_round"] == 4

    def test_updates_prev_lead_count(self):
        leads = [{"company": f"C{i}"} for i in range(25)]
        state = self._make_state(leads=leads, prev_round_lead_count=10)
        result = evaluate_progress(state)
        assert result["prev_round_lead_count"] == 25

    def test_feedback_contains_new_leads_count(self):
        leads = [{"company": f"C{i}"} for i in range(30)]
        state = self._make_state(leads=leads, prev_round_lead_count=20, hunt_round=2)
        result = evaluate_progress(state)
        fb = result["round_feedback"]
        assert fb["new_leads_this_round"] == 10
        assert fb["total_leads"] == 30
        assert fb["round"] == 2

    def test_feedback_contains_per_keyword_performance(self):
        stats = {
            "kw1": {"result_count": 20, "leads_found": 5},
            "kw2": {"result_count": 3, "leads_found": 0},
        }
        # Provide leads with high match_score so kw1 is classified as 'high'
        leads = [{"source_keyword": "kw1", "match_score": 0.7} for _ in range(5)]
        state = self._make_state(keyword_search_stats=stats, leads=leads)
        result = evaluate_progress(state)
        fb = result["round_feedback"]

        assert len(fb["keyword_performance"]) == 2
        assert "kw1" in fb["best_keywords"]
        assert "kw2" in fb["worst_keywords"]

    def test_feedback_contains_distributions(self):
        leads = [
            {"industry": "Solar", "country_code": "de", "source_keyword": "solar kw"},
            {"industry": "Solar", "country_code": "fr", "source_keyword": "solar kw"},
            {"industry": "Electronics", "country_code": "de", "source_keyword": "electronics kw"},
        ]
        state = self._make_state(leads=leads)
        result = evaluate_progress(state)
        fb = result["round_feedback"]

        assert fb["industry_distribution"] == {"Solar": 2, "Electronics": 1}
        assert fb["region_distribution"] == {"de": 2, "fr": 1}
        assert fb["top_sources"][0] == "solar kw"

    def test_sets_current_stage(self):
        state = self._make_state()
        result = evaluate_progress(state)
        assert result["current_stage"] == "evaluate"


# ── should_continue_hunting tests ───────────────────────────────────────


class TestShouldContinueHunting:
    def _make_state(self, **overrides):
        base = {
            "leads": [],
            "target_lead_count": 200,
            "hunt_round": 1,
            "max_rounds": 10,
            "prev_round_lead_count": 0,
            "round_feedback": None,
        }
        base.update(overrides)
        return base

    def _feedback(self, round_num: int, new_leads: int) -> dict:
        """Helper to build a round_feedback dict like evaluate_progress produces."""
        return {"round": round_num, "new_leads_this_round": new_leads}

    def test_continue_when_below_target(self):
        leads = [{"company": f"C{i}"} for i in range(50)]
        state = self._make_state(
            leads=leads, hunt_round=2,
            round_feedback=self._feedback(round_num=1, new_leads=50),
        )
        assert should_continue_hunting(state) == "continue"

    def test_finish_when_target_met(self):
        leads = [{"company": f"C{i}"} for i in range(200)]
        state = self._make_state(leads=leads, target_lead_count=200)
        assert should_continue_hunting(state) == "finish"

    def test_finish_when_target_exceeded(self):
        leads = [{"company": f"C{i}"} for i in range(250)]
        state = self._make_state(leads=leads, target_lead_count=200)
        assert should_continue_hunting(state) == "finish"

    def test_finish_when_max_rounds_exceeded(self):
        leads = [{"company": f"C{i}"} for i in range(50)]
        state = self._make_state(leads=leads, hunt_round=11, max_rounds=10)
        assert should_continue_hunting(state) == "finish"

    def test_finish_on_diminishing_returns(self):
        leads = [{"company": f"C{i}"} for i in range(53)]
        state = self._make_state(
            leads=leads,
            hunt_round=3,
            round_feedback=self._feedback(round_num=2, new_leads=3),
        )
        assert should_continue_hunting(state) == "finish"

    def test_no_diminishing_returns_on_round_1(self):
        leads = [{"company": f"C{i}"} for i in range(3)]
        state = self._make_state(
            leads=leads,
            hunt_round=2,
            round_feedback=self._feedback(round_num=1, new_leads=3),
        )
        assert should_continue_hunting(state) == "continue"

    def test_continue_with_leads_above_threshold(self):
        # target=200 → threshold = max(3, min(10, int(200*0.05))) = 10
        # new_leads=11 >= 10 → continue
        leads = [{"company": f"C{i}"} for i in range(61)]
        state = self._make_state(
            leads=leads,
            hunt_round=3,
            round_feedback=self._feedback(round_num=2, new_leads=11),
        )
        assert should_continue_hunting(state) == "continue"

    def test_finish_with_leads_below_threshold(self):
        # target=200 → threshold=10; new_leads=9 < 10 → finish
        leads = [{"company": f"C{i}"} for i in range(59)]
        state = self._make_state(
            leads=leads,
            hunt_round=3,
            round_feedback=self._feedback(round_num=2, new_leads=9),
        )
        assert should_continue_hunting(state) == "finish"

    def test_threshold_scales_with_small_target(self):
        # target=20 → threshold = max(3, min(10, int(20*0.05))) = max(3,1) = 3
        # new_leads=2 < 3 → finish
        leads = [{"company": f"C{i}"} for i in range(12)]
        state = self._make_state(
            leads=leads,
            target_lead_count=20,
            hunt_round=3,
            round_feedback=self._feedback(round_num=2, new_leads=2),
        )
        assert should_continue_hunting(state) == "finish"

    def test_defaults_when_fields_missing(self):
        state = {"leads": [{"company": "X"}]}
        result = should_continue_hunting(state)
        assert result == "continue"

    def test_uses_round_feedback_not_prev_lead_count(self):
        """Regression: after evaluate_progress merges its output, prev_round_lead_count
        equals current leads. should_continue_hunting must read from round_feedback
        to get the correct new_leads_this_round, not re-compute from stale state."""
        leads = [{"company": f"C{i}"} for i in range(102)]
        state = self._make_state(
            leads=leads,
            hunt_round=2,
            # evaluate_progress already set prev_round_lead_count = 102
            prev_round_lead_count=102,
            # But round_feedback correctly records 102 new leads from round 1
            round_feedback=self._feedback(round_num=1, new_leads=102),
        )
        # Should CONTINUE because round 1 had 102 new leads (not diminishing)
        assert should_continue_hunting(state) == "continue"
