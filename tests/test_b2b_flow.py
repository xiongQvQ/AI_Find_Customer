"""
Tests for core/b2b_flow.py

All tests are offline — LLM and search calls are mocked.
Run with:
    python -m pytest tests/test_b2b_flow.py -v
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Fixtures / helpers ─────────────────────────────────────────────────────

def _make_search_hits(n=3, domain_prefix="company"):
    return [
        {
            "title": f"Company {i}",
            "url": f"https://{domain_prefix}{i}.com/about",
            "domain": f"{domain_prefix}{i}.com",
            "snippet": f"We are company {i}.",
            "score": 0.8,
            "provider": "serper",
        }
        for i in range(n)
    ]


def _make_llm_scores(n=3):
    return json.dumps([
        {"is_company": True, "is_relevant": True, "score": 8.0, "reason": "Good lead"}
        for _ in range(n)
    ])


# ── FlowResult dataclass ───────────────────────────────────────────────────

class TestFlowResult:
    def test_to_dict_has_all_fields(self):
        from core.b2b_flow import FlowResult
        r = FlowResult(title="T", url="https://x.com", domain="x.com")
        d = r.to_dict()
        assert "title" in d
        assert "llm_score" in d
        assert "is_company" in d
        assert "llm_scored" in d

    def test_default_llm_scored_false(self):
        from core.b2b_flow import FlowResult
        r = FlowResult()
        assert r.llm_scored is False
        assert r.llm_score == 0.0


# ── get_platform_labels ────────────────────────────────────────────────────

class TestGetPlatformLabels:
    def test_returns_list_of_strings(self):
        from core.b2b_flow import get_platform_labels
        labels = get_platform_labels()
        assert isinstance(labels, list)
        assert len(labels) >= 5
        assert all(isinstance(l, str) for l in labels)

    def test_includes_expected_platforms(self):
        from core.b2b_flow import get_platform_labels
        labels = get_platform_labels()
        expected = {"Alibaba", "Europages", "Kompass", "ThomasNet"}
        assert expected.issubset(set(labels))


# ── B2BFlow._dedup ─────────────────────────────────────────────────────────

class TestDedup:
    def setup_method(self):
        from core.b2b_flow import B2BFlow
        self.flow = B2BFlow("solar inverter", ["Germany"])

    def test_dedup_removes_same_domain(self):
        from core.b2b_flow import FlowResult
        results = [
            FlowResult(title="A", url="https://acme.com/1", domain="acme.com"),
            FlowResult(title="B", url="https://acme.com/2", domain="acme.com"),
            FlowResult(title="C", url="https://beta.de",   domain="beta.de"),
        ]
        deduped = self.flow._dedup(results)
        domains = [r.domain for r in deduped]
        assert domains.count("acme.com") == 1
        assert len(deduped) == 2

    def test_dedup_keeps_first_occurrence(self):
        from core.b2b_flow import FlowResult
        results = [
            FlowResult(title="First",  url="https://acme.com/1", domain="acme.com"),
            FlowResult(title="Second", url="https://acme.com/2", domain="acme.com"),
        ]
        deduped = self.flow._dedup(results)
        assert deduped[0].title == "First"

    def test_dedup_handles_no_domain(self):
        from core.b2b_flow import FlowResult
        results = [
            FlowResult(title="A", url="https://x.com/1", domain=""),
            FlowResult(title="B", url="https://x.com/1", domain=""),  # same URL
            FlowResult(title="C", url="https://x.com/2", domain=""),  # different URL
        ]
        deduped = self.flow._dedup(results)
        assert len(deduped) == 2

    def test_dedup_empty_list(self):
        assert self.flow._dedup([]) == []


# ── B2BFlow._get_platforms ─────────────────────────────────────────────────

class TestGetPlatforms:
    def setup_method(self):
        from core.b2b_flow import B2BFlow
        self.flow = B2BFlow("pump", ["USA"])

    def test_none_returns_all(self):
        from core.b2b_flow import B2B_PLATFORM_SITES
        platforms = self.flow._get_platforms(None)
        assert len(platforms) == len(B2B_PLATFORM_SITES)

    def test_filter_by_label(self):
        platforms = self.flow._get_platforms(["Alibaba", "Europages"])
        labels = [l for l, _ in platforms]
        assert set(labels) == {"Alibaba", "Europages"}

    def test_case_insensitive(self):
        platforms = self.flow._get_platforms(["alibaba"])
        assert len(platforms) == 1

    def test_unknown_label_excluded(self):
        platforms = self.flow._get_platforms(["NotExist"])
        assert len(platforms) == 0


# ── B2BFlow._llm_score_batch ───────────────────────────────────────────────

class TestLlmScoreBatch:
    def _make_flow(self):
        from core.b2b_flow import B2BFlow
        return B2BFlow("solar inverter", ["Germany"])

    def test_scores_assigned_correctly(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        from core.b2b_flow import B2BFlow, FlowResult
        flow = B2BFlow("solar inverter", ["Germany"])

        results = [FlowResult(title=f"Co {i}", url=f"https://co{i}.com", domain=f"co{i}.com") for i in range(3)]
        scores_json = _make_llm_scores(3)

        with patch("core.llm_client.call_llm", return_value=scores_json):
            scored = flow._llm_score_batch(results)

        assert all(r.llm_scored for r in scored)
        assert all(r.llm_score == 8.0 for r in scored)
        assert all(r.is_company for r in scored)

    def test_skips_when_llm_unavailable(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        from core.b2b_flow import B2BFlow, FlowResult
        flow = B2BFlow("pump", ["USA"])

        results = [FlowResult(title="X", url="https://x.com", domain="x.com")]
        scored = flow._llm_score_batch(results)
        assert scored[0].llm_scored is False

    def test_handles_llm_error_gracefully(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        from core.b2b_flow import B2BFlow, FlowResult
        flow = B2BFlow("pump", ["USA"])

        results = [FlowResult(title="X", url="https://x.com", domain="x.com")]
        with patch("core.llm_client.call_llm", side_effect=RuntimeError("boom")):
            scored = flow._llm_score_batch(results)
        # Should not raise; result stays with llm_scored=False
        assert len(scored) == 1


# ── B2BFlow.run — full pipeline integration ────────────────────────────────

class TestB2BFlowRun:
    def _setup(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.setenv("SERPER_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from importlib import reload
        import core.llm_client as lc
        import core.search_client as sc
        reload(lc)
        reload(sc)

    def test_run_no_llm_no_b2b(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        fake_keywords = ["solar inverter distributor Germany", "PV importer Poland"]
        fake_hits = _make_search_hits(3)

        with patch("keyword_generator.generate_keywords", return_value=fake_keywords), \
             patch("core.search_client.search", return_value=fake_hits), \
             patch("time.sleep"):

            flow = B2BFlow("solar inverter", ["Germany"])
            result = flow.run(
                keyword_count=2,
                num_search_results=3,
                gl="de",
                run_b2b_platforms=False,
                llm_filter=False,
            )

        assert result["success"] is True
        assert len(result["keywords"]) == 2
        assert result["stats"]["keywords_generated"] == 2
        assert result["stats"]["searches_run"] == 2
        # 3 hits per keyword, deduped by domain
        assert result["stats"]["after_dedup"] == 3

    def test_run_with_llm_filtering(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        fake_keywords = ["kw1", "kw2"]
        # 4 unique domains
        hits_kw1 = _make_search_hits(2, "alpha")   # alpha0.com, alpha1.com
        hits_kw2 = _make_search_hits(2, "beta")    # beta0.com, beta1.com

        def _mock_search(query, num_results, gl):
            if "kw1" in query:
                return hits_kw1
            return hits_kw2

        # LLM returns: 2 high score, 2 low score
        scores = json.dumps([
            {"is_company": True, "is_relevant": True,  "score": 8.0, "reason": "Good"},
            {"is_company": True, "is_relevant": False, "score": 3.0, "reason": "Low"},
            {"is_company": True, "is_relevant": True,  "score": 7.0, "reason": "Ok"},
            {"is_company": True, "is_relevant": False, "score": 2.0, "reason": "Bad"},
        ])

        with patch("keyword_generator.generate_keywords", return_value=fake_keywords), \
             patch("core.search_client.search", side_effect=_mock_search), \
             patch("core.llm_client.call_llm", return_value=scores), \
             patch("time.sleep"):

            flow = B2BFlow("solar inverter", ["Germany"])
            result = flow.run(
                keyword_count=2,
                run_b2b_platforms=False,
                llm_filter=True,
                min_llm_score=5.0,
            )

        assert result["success"] is True
        assert len(result["filtered_results"]) == 2
        scores_only = [r["llm_score"] for r in result["filtered_results"]]
        assert all(s >= 5.0 for s in scores_only)

    def test_run_with_b2b_platforms(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        fake_keywords = ["kw1"]
        kw_hits = _make_search_hits(2, "regular")
        b2b_hits = _make_search_hits(2, "alibaba")

        def _mock_search(query, num_results, gl):
            if "site:alibaba.com" in query:
                return b2b_hits
            return kw_hits

        with patch("keyword_generator.generate_keywords", return_value=fake_keywords), \
             patch("core.search_client.search", side_effect=_mock_search), \
             patch("time.sleep"):

            flow = B2BFlow("pump", ["USA"])
            result = flow.run(
                keyword_count=1,
                run_b2b_platforms=True,
                b2b_platforms=["Alibaba"],
                llm_filter=False,
            )

        assert result["success"] is True
        # 2 from keyword + 2 from alibaba = 4 unique domains
        assert result["stats"]["after_dedup"] == 4
        sources = {r["source_type"] for r in result["all_results"]}
        assert "keyword_search" in sources
        assert "b2b_platform" in sources

    def test_extra_keywords_appended(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        with patch("keyword_generator.generate_keywords", return_value=["ai-kw"]), \
             patch("core.search_client.search", return_value=[]), \
             patch("time.sleep"):

            flow = B2BFlow("pump", ["USA"])
            result = flow.run(
                keyword_count=1,
                run_b2b_platforms=False,
                llm_filter=False,
                extra_keywords=["manual-kw-1", "manual-kw-2"],
            )

        assert "ai-kw" in result["keywords"]
        assert "manual-kw-1" in result["keywords"]
        assert "manual-kw-2" in result["keywords"]

    def test_run_handles_search_error_gracefully(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        with patch("keyword_generator.generate_keywords", return_value=["kw1", "kw2"]), \
             patch("core.search_client.search", side_effect=RuntimeError("network error")), \
             patch("time.sleep"):

            flow = B2BFlow("pump", ["USA"])
            result = flow.run(
                keyword_count=2,
                run_b2b_platforms=False,
                llm_filter=False,
            )

        # Should not raise; returns success=True with 0 results
        assert result["success"] is True
        assert result["stats"]["after_dedup"] == 0

    def test_run_keyword_gen_failure_returns_error(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        with patch("keyword_generator.generate_keywords", side_effect=ValueError("LLM_MODEL not set")):
            flow = B2BFlow("pump", ["USA"])
            result = flow.run(keyword_count=5, llm_filter=False)

        assert result["success"] is False
        assert result["error"]

    def test_progress_callback_called(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        steps = []
        def _cb(step, pct):
            steps.append((step, pct))

        with patch("keyword_generator.generate_keywords", return_value=["kw"]), \
             patch("core.search_client.search", return_value=[]), \
             patch("time.sleep"):

            flow = B2BFlow("pump", ["USA"])
            flow.run(
                keyword_count=1,
                run_b2b_platforms=False,
                llm_filter=False,
                progress_cb=_cb,
            )

        assert len(steps) > 0
        # Last step should be 100%
        assert steps[-1][1] == 1.0

    def test_sorted_by_score_descending(self, monkeypatch):
        self._setup(monkeypatch)
        from core.b2b_flow import B2BFlow

        fake_keywords = ["kw1"]
        hits = _make_search_hits(3, "co")

        scores = json.dumps([
            {"is_company": True, "is_relevant": True, "score": 3.0, "reason": "low"},
            {"is_company": True, "is_relevant": True, "score": 9.0, "reason": "high"},
            {"is_company": True, "is_relevant": True, "score": 6.0, "reason": "mid"},
        ])

        with patch("keyword_generator.generate_keywords", return_value=fake_keywords), \
             patch("core.search_client.search", return_value=hits), \
             patch("core.llm_client.call_llm", return_value=scores), \
             patch("time.sleep"):

            flow = B2BFlow("pump", ["USA"])
            result = flow.run(
                keyword_count=1,
                run_b2b_platforms=False,
                llm_filter=True,
                min_llm_score=0.0,
            )

        scored = result["scored_results"]
        score_values = [r["llm_score"] for r in scored]
        assert score_values == sorted(score_values, reverse=True)
