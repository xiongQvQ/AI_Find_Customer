"""Tests for api/routes.py — FastAPI endpoints with httpx TestClient."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from api.app import create_app
from api.routes import _hunts

# Patch save_hunt globally so tests never write to disk
pytestmark = pytest.mark.usefixtures("_mock_save_hunt")


@pytest.fixture(autouse=True)
def _mock_save_hunt():
    with patch("api.routes.save_hunt"):
        yield


@pytest.fixture
def app():
    """Create a fresh app instance per test."""
    _hunts.clear()
    return create_app()


@pytest.fixture
async def client(app):
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "ai-hunter"


class TestCreateHunt:
    @pytest.mark.asyncio
    @patch("api.routes._run_hunt", new_callable=AsyncMock)
    async def test_create_hunt_returns_id(self, mock_run, client):
        resp = await client.post("/api/v1/hunts", json={
            "website_url": "https://solartech.de",
            "product_keywords": ["solar inverter"],
            "target_regions": ["Europe"],
            "target_lead_count": 100,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "hunt_id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    @patch("api.routes._run_hunt", new_callable=AsyncMock)
    async def test_create_hunt_minimal_request(self, mock_run, client):
        resp = await client.post("/api/v1/hunts", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "hunt_id" in data

    @pytest.mark.asyncio
    async def test_create_hunt_invalid_lead_count(self, client):
        resp = await client.post("/api/v1/hunts", json={
            "target_lead_count": 0,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_hunt_rejects_uploaded_file_outside_upload_dir(self, client, tmp_path):
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("secret", encoding="utf-8")

        resp = await client.post("/api/v1/hunts", json={
            "uploaded_file_ids": [str(outside_file)],
        })

        assert resp.status_code == 400
        assert "uploaded_file_ids" in resp.json()["detail"]


class TestUploadFiles:
    @pytest.mark.asyncio
    async def test_upload_enforces_size_limit(self, client, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "api.routes.get_settings",
            lambda: type("S", (), {"upload_dir": str(tmp_path), "max_upload_size_mb": 0})(),
        )

        resp = await client.post(
            "/api/v1/upload",
            files={"files": ("tiny.txt", b"x", "text/plain")},
        )

        assert resp.status_code == 413
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.asyncio
    async def test_api_access_token_required_when_configured(self, monkeypatch):
        monkeypatch.setenv("API_ACCESS_TOKEN", "secret-token")
        from config.settings import get_settings

        get_settings.cache_clear()
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            unauthorized = await client.get("/api/v1/hunts")
            authorized = await client.get("/api/v1/hunts", headers={"X-API-Key": "secret-token"})

        get_settings.cache_clear()
        assert unauthorized.status_code == 401
        assert authorized.status_code == 200


class TestHuntStatus:
    @pytest.mark.asyncio
    async def test_status_pending(self, client):
        # Manually inject a pending hunt to avoid background task race
        _hunts["pending-123"] = {
            "status": "pending",
            "result": None,
            "current_stage": None,
            "hunt_round": 0,
            "leads_count": 0,
            "email_sequences_count": 0,
            "error": None,
        }

        resp = await client.get("/api/v1/hunts/pending-123/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["hunt_id"] == "pending-123"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_status_not_found(self, client):
        resp = await client.get("/api/v1/hunts/nonexistent-id/status")
        assert resp.status_code == 404


class TestHuntResult:
    @pytest.mark.asyncio
    async def test_result_not_found(self, client):
        resp = await client.get("/api/v1/hunts/nonexistent-id/result")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_result_not_ready(self, client):
        # Manually inject a running hunt to avoid background task race
        _hunts["running-456"] = {
            "status": "running",
            "result": None,
            "current_stage": "search",
            "hunt_round": 1,
            "leads_count": 0,
            "email_sequences_count": 0,
            "error": None,
        }

        resp = await client.get("/api/v1/hunts/running-456/result")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert data["leads"] == []

    @pytest.mark.asyncio
    async def test_result_completed(self, client):
        # Manually inject a completed hunt
        _hunts["test-123"] = {
            "status": "completed",
            "result": {
                "insight": {"company_name": "Test"},
                "leads": [{"company_name": "Lead1"}],
                "email_sequences": [],
                "used_keywords": ["kw1"],
                "hunt_round": 2,
                "round_feedback": {"round": 2},
            },
            "current_stage": "email_craft",
            "hunt_round": 2,
            "leads_count": 1,
            "email_sequences_count": 0,
            "error": None,
        }

        resp = await client.get("/api/v1/hunts/test-123/result")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["insight"]["company_name"] == "Test"
        assert len(data["leads"]) == 1
        assert data["hunt_round"] == 2

    @pytest.mark.asyncio
    async def test_result_dedupes_duplicate_leads(self, client):
        _hunts["dup-123"] = {
            "status": "completed",
            "result": {
                "insight": {"company_name": "Test"},
                "leads": [
                    {"company_name": "Lead1", "website": "https://lead1.com"},
                    {"company_name": "Lead1 copy", "website": "https://lead1.com"},
                ],
                "email_sequences": [],
                "used_keywords": [],
                "hunt_round": 1,
                "round_feedback": None,
            },
            "current_stage": "lead_extract",
            "hunt_round": 1,
            "leads_count": 2,
            "email_sequences_count": 0,
            "error": None,
        }

        resp = await client.get("/api/v1/hunts/dup-123/result")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["leads"]) == 1


class TestListHunts:
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        resp = await client.get("/api/v1/hunts")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    @patch("api.routes._run_hunt", new_callable=AsyncMock)
    async def test_list_after_create(self, mock_run, client):
        await client.post("/api/v1/hunts", json={"product_keywords": ["test"]})
        await client.post("/api/v1/hunts", json={"product_keywords": ["test2"]})

        resp = await client.get("/api/v1/hunts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        for item in data:
            assert "hunt_id" in item
            assert "status" in item
            assert "created_at" in item
            assert "product_keywords" in item

    @pytest.mark.asyncio
    async def test_list_uses_unique_lead_count(self, client):
        _hunts["dup-list"] = {
            "status": "completed",
            "result": {
                "leads": [
                    {"company_name": "Lead1", "website": "https://lead1.com"},
                    {"company_name": "Lead1 copy", "website": "https://lead1.com"},
                    {"company_name": "Lead2", "website": "https://lead2.com"},
                ],
            },
            "leads_count": 3,
            "created_at": "2026-03-07T00:00:00+00:00",
            "website_url": "https://example.com",
            "product_keywords": [],
            "target_customer_profile": "",
            "target_regions": [],
            "hunt_round": 1,
            "email_sequences_count": 0,
        }

        resp = await client.get("/api/v1/hunts")
        assert resp.status_code == 200
        data = resp.json()
        item = next(x for x in data if x["hunt_id"] == "dup-list")
        assert item["leads_count"] == 2


# ── _slim_state unit tests ───────────────────────────────────────────────

from api.routes import _slim_state, ResumeRequest, _MAX_SEARCH_RESULTS_ON_RESUME


def _make_prior_result(**overrides) -> dict:
    """Build a realistic completed hunt result for testing."""
    base = {
        "website_url": "https://solartech.de",
        "product_keywords": ["solar inverter"],
        "target_regions": ["Germany"],
        "uploaded_files": [],
        "insight": {"company_name": "SolarTech", "products": ["solar inverter"]},
        "leads": [{"company_name": f"Lead{i}", "website": f"https://lead{i}.com"} for i in range(10)],
        "used_keywords": ["solar inverter distributor", "PV module importer"],
        "keyword_search_stats": {
            "solar inverter distributor": {"result_count": 8, "leads_found": 3},
        },
        "search_results": [
            {"title": f"Result {i}", "link": f"https://result{i}.com", "snippet": "..."}
            for i in range(100)
        ],
        "seen_urls": [f"https://result{i}.com" for i in range(100)],
        "matched_platforms": [{"name": "Europages", "domain": "europages.com", "weight": 1.0}],
        "hunt_round": 5,
        "round_feedback": {"round": 5, "total_leads": 10},
    }
    base.update(overrides)
    return base


def _make_resume_request(**overrides) -> ResumeRequest:
    defaults = {
        "target_lead_count": 400,
        "max_rounds": 15,
        "min_new_leads_threshold": 5,
        "enable_email_craft": False,
    }
    defaults.update(overrides)
    return ResumeRequest(**defaults)


class TestSlimState:
    def test_insight_preserved(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["insight"] == prior["insight"]

    def test_leads_preserved(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["leads"] == prior["leads"]
        assert len(state["leads"]) == 10

    def test_used_keywords_preserved(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["used_keywords"] == prior["used_keywords"]

    def test_keyword_search_stats_preserved(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["keyword_search_stats"] == prior["keyword_search_stats"]

    def test_seen_urls_preserved_fully(self):
        """seen_urls must be preserved in full — it's the dedup mechanism."""
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert len(state["seen_urls"]) == 100
        assert "https://result0.com" in state["seen_urls"]
        assert "https://result99.com" in state["seen_urls"]

    def test_search_results_trimmed(self):
        """search_results is trimmed to _MAX_SEARCH_RESULTS_ON_RESUME rows."""
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert len(state["search_results"]) == _MAX_SEARCH_RESULTS_ON_RESUME
        # Should keep the LAST N rows
        assert state["search_results"][-1]["link"] == "https://result99.com"

    def test_search_results_not_trimmed_when_small(self):
        """search_results smaller than limit are kept as-is."""
        prior = _make_prior_result(search_results=[
            {"title": "R", "link": "https://r.com", "snippet": "x"}
        ])
        state = _slim_state(prior, _make_resume_request())
        assert len(state["search_results"]) == 1

    def test_hunt_round_reset_to_1(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["hunt_round"] == 1

    def test_prev_round_lead_count_set_to_prior_leads(self):
        """Baseline for new session = number of leads already found."""
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["prev_round_lead_count"] == 10

    def test_round_feedback_rebuilt_from_keyword_stats(self):
        """round_feedback is rebuilt from keyword_search_stats so KeywordGenAgent
        has historical performance context on the first round after resume."""
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        fb = state["round_feedback"]
        assert fb is not None
        assert "keyword_performance" in fb
        assert "best_keywords" in fb
        assert "worst_keywords" in fb
        assert fb["round"] == "prior_session_summary"
        # The fixture has one keyword with leads_found=3 — should be high/medium
        kw_names = [kp["keyword"] for kp in fb["keyword_performance"]]
        assert "solar inverter distributor" in kw_names

    def test_round_feedback_none_when_no_keyword_stats(self):
        """round_feedback stays None when there are no historical keyword stats."""
        prior = _make_prior_result(keyword_search_stats={})
        state = _slim_state(prior, _make_resume_request())
        assert state["round_feedback"] is None

    def test_keywords_cleared(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["keywords"] == []

    def test_email_sequences_cleared(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["email_sequences"] == []

    def test_messages_cleared(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request())
        assert state["messages"] == []

    def test_new_target_lead_count_applied(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request(target_lead_count=500))
        assert state["target_lead_count"] == 500

    def test_new_min_new_leads_threshold_applied(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request(min_new_leads_threshold=8))
        assert state["min_new_leads_threshold"] == 8

    def test_new_max_rounds_applied(self):
        prior = _make_prior_result()
        state = _slim_state(prior, _make_resume_request(max_rounds=20))
        assert state["max_rounds"] == 20

    def test_seen_urls_fallback_from_search_results(self):
        """If seen_urls is absent, fall back to extracting links from search_results."""
        prior = _make_prior_result()
        prior.pop("seen_urls")  # simulate old hunt without seen_urls field
        state = _slim_state(prior, _make_resume_request())
        assert len(state["seen_urls"]) == 100
        assert "https://result0.com" in state["seen_urls"]

    def test_empty_prior_result_safe(self):
        """_slim_state handles an empty prior result without raising."""
        state = _slim_state({}, _make_resume_request())
        assert state["leads"] == []
        assert state["seen_urls"] == []
        assert state["insight"] is None
        assert state["hunt_round"] == 1


# ── Resume route tests ───────────────────────────────────────────────────

class TestResumeHunt:
    def _inject_completed_hunt(self, hunt_id: str, leads: int = 10):
        """Inject a completed hunt into _hunts for testing."""
        _hunts[hunt_id] = {
            "status": "completed",
            "website_url": "https://solartech.de",
            "product_keywords": ["solar inverter"],
            "target_regions": ["Germany"],
            "hunt_round": 5,
            "leads_count": leads,
            "email_sequences_count": 0,
            "error": None,
            "result": {
                "website_url": "https://solartech.de",
                "product_keywords": ["solar inverter"],
                "target_regions": ["Germany"],
                "uploaded_files": [],
                "insight": {"company_name": "SolarTech"},
                "leads": [{"company_name": f"Lead{i}"} for i in range(leads)],
                "used_keywords": ["solar inverter distributor"],
                "keyword_search_stats": {"solar inverter distributor": {"result_count": 5, "leads_found": 2}},
                "search_results": [{"title": f"R{i}", "link": f"https://r{i}.com", "snippet": "x"} for i in range(20)],
                "seen_urls": [f"https://r{i}.com" for i in range(20)],
                "matched_platforms": [],
                "hunt_round": 5,
                "round_feedback": None,
            },
        }

    @pytest.mark.asyncio
    @patch("api.routes._run_resume_hunt", new_callable=AsyncMock)
    async def test_resume_completed_hunt(self, mock_resume, client):
        self._inject_completed_hunt("hunt-abc")
        resp = await client.post("/api/v1/hunts/hunt-abc/resume", json={
            "target_lead_count": 400,
            "max_rounds": 15,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["hunt_id"] == "hunt-abc"
        assert data["status"] == "pending"
        mock_resume.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_not_found(self, client):
        resp = await client.post("/api/v1/hunts/nonexistent/resume", json={})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_resume_running_hunt_rejected(self, client):
        _hunts["running-hunt"] = {"status": "running", "result": {}}
        resp = await client.post("/api/v1/hunts/running-hunt/resume", json={})
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_resume_pending_hunt_rejected(self, client):
        _hunts["pending-hunt"] = {"status": "pending", "result": None}
        resp = await client.post("/api/v1/hunts/pending-hunt/resume", json={})
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_resume_no_result_rejected(self, client):
        _hunts["empty-hunt"] = {"status": "completed", "result": None}
        resp = await client.post("/api/v1/hunts/empty-hunt/resume", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @patch("api.routes._run_resume_hunt", new_callable=AsyncMock)
    async def test_resume_failed_hunt_allowed(self, mock_resume, client):
        """Failed hunts can also be resumed (retry from last saved state)."""
        self._inject_completed_hunt("failed-hunt")
        _hunts["failed-hunt"]["status"] = "failed"
        resp = await client.post("/api/v1/hunts/failed-hunt/resume", json={
            "target_lead_count": 200,
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @patch("api.routes._run_resume_hunt", new_callable=AsyncMock)
    async def test_resume_passes_correct_args_to_background(self, mock_resume, client):
        """Verify resume sanitizes disabled email generation before background execution."""
        self._inject_completed_hunt("hunt-xyz", leads=5)
        await client.post("/api/v1/hunts/hunt-xyz/resume", json={
            "target_lead_count": 300,
            "max_rounds": 12,
            "enable_email_craft": True,
        })
        args = mock_resume.call_args[0]
        assert args[0] == "hunt-xyz"
        resume_req = args[1]
        assert resume_req.target_lead_count == 300
        assert resume_req.max_rounds == 12
        assert resume_req.enable_email_craft is False
        prior = args[2]
        assert len(prior["leads"]) == 5

    @pytest.mark.asyncio
    @patch("api.routes._run_resume_hunt", new_callable=AsyncMock)
    async def test_resume_status_set_to_pending(self, mock_resume, client):
        """After resume call, hunt status is set to pending."""
        self._inject_completed_hunt("hunt-status")
        await client.post("/api/v1/hunts/hunt-status/resume", json={})
        assert _hunts["hunt-status"]["status"] == "pending"

    @pytest.mark.asyncio
    @patch("api.routes._run_resume_hunt", new_callable=AsyncMock)
    async def test_resume_default_params(self, mock_resume, client):
        """Resume with empty body uses default target_lead_count=200, max_rounds=10."""
        self._inject_completed_hunt("hunt-defaults")
        await client.post("/api/v1/hunts/hunt-defaults/resume", json={})
        resume_req = mock_resume.call_args[0][1]
        assert resume_req.target_lead_count == 200
        assert resume_req.max_rounds == 10
