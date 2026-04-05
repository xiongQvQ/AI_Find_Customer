from fastapi.testclient import TestClient

from api.app import create_app


def test_automation_routes(monkeypatch):
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr(
        "api.automation_routes.collect_automation_status",
        lambda hunts=None: {
            "hunt_jobs": {"queued": 1, "running": 2, "failed": 0},
            "hunts": {"running": 1, "pending": 0},
            "email_queue": {"pending": 3, "sent": 4, "failed": 1, "cancelled": 0},
            "features": {"email_auto_send_enabled": True, "email_reply_detection_enabled": True, "automation_summary_enabled": True, "automation_alerts_enabled": True},
        },
    )
    monkeypatch.setattr(
        "api.automation_routes.collect_automation_metrics",
        lambda hours=24, hunts=None: {
            "window_hours": hours,
            "emails": {"failed": 2},
            "hunt_jobs": {"queued": 1},
            "recent_failures": [],
        },
    )

    status = client.get("/api/v1/automation/status")
    metrics = client.get("/api/v1/automation/metrics?hours=2")
    health = client.get("/api/v1/automation/health")

    assert status.status_code == 200
    assert status.json()["hunt_jobs"]["queued"] == 1
    assert metrics.status_code == 200
    assert metrics.json()["window_hours"] == 2
    assert health.status_code == 200
    assert health.json()["backlog_email_messages"] == 3


def test_automation_job_routes(monkeypatch):
    app = create_app()
    client = TestClient(app)

    fake_job = {
        "id": "job-1",
        "status": "queued",
        "created_at": "2026-04-05T00:00:00+00:00",
        "updated_at": "2026-04-05T00:00:00+00:00",
        "started_at": "",
        "finished_at": "",
        "attempt_count": 1,
        "last_error": "",
        "last_hunt_id": "",
        "payload": {
            "website_url": "https://www.gdushun.com/",
            "description": "Find distributors",
            "product_keywords": ["micro switch"],
            "target_regions": ["United States"],
            "target_lead_count": 100,
            "enable_email_craft": True,
        },
    }

    class FakeQueue:
        def init_db(self):
            return None

        def enqueue(self, payload, now_iso):
            return "job-1"

        def get(self, job_id):
            if job_id == "missing":
                return None
            return fake_job

        def get_by_hunt_id(self, hunt_id):
            if hunt_id == "missing-hunt":
                return None
            job = dict(fake_job)
            job["last_hunt_id"] = hunt_id
            return job

        def list_jobs(self, limit=100):
            return [fake_job]

    monkeypatch.setattr("api.automation_routes._queue", lambda: FakeQueue())
    monkeypatch.setattr("api.automation_routes.load_hunt", lambda hunt_id: None)

    created = client.post("/api/v1/automation/jobs", json={
        "website_url": "https://www.gdushun.com/",
        "description": "Find distributors",
        "product_keywords": ["micro switch"],
        "target_regions": ["United States"],
        "target_lead_count": 100,
        "enable_email_craft": True,
    })
    listed = client.get("/api/v1/automation/jobs")
    detail = client.get("/api/v1/automation/jobs/job-1")
    by_hunt = client.get("/api/v1/automation/jobs/by-hunt/hunt-1")
    missing = client.get("/api/v1/automation/jobs/missing")
    missing_by_hunt = client.get("/api/v1/automation/jobs/by-hunt/missing-hunt")

    assert created.status_code == 200
    assert created.json()["job_id"] == "job-1"
    assert listed.status_code == 200
    assert listed.json()[0]["website_url"] == "https://www.gdushun.com/"
    assert detail.status_code == 200
    assert detail.json()["target_lead_count"] == 100
    assert by_hunt.status_code == 200
    assert by_hunt.json()["last_hunt_id"] == "hunt-1"
    assert missing.status_code == 404
    assert missing_by_hunt.status_code == 404


def test_create_automation_job_from_hunt(monkeypatch):
    app = create_app()
    client = TestClient(app)

    queued_payloads = []

    class FakeQueue:
        def init_db(self):
            return None

        def enqueue(self, payload, now_iso):
            queued_payloads.append(payload)
            return "job-2"

        def get(self, job_id):
            return {
                "id": "job-2",
                "status": "queued",
                "created_at": "2026-04-05T00:00:00+00:00",
                "updated_at": "2026-04-05T00:00:00+00:00",
                "started_at": "",
                "finished_at": "",
                "attempt_count": 0,
                "last_error": "",
                "last_hunt_id": "",
                "payload": queued_payloads[-1] if queued_payloads else {},
            }

    monkeypatch.setattr("api.automation_routes._queue", lambda: FakeQueue())
    monkeypatch.setattr(
        "api.automation_routes.load_hunt",
        lambda hunt_id: {
            "payload": {
                "website_url": "https://www.gdushun.com/",
                "description": "Find distributors",
                "product_keywords": ["micro switch"],
                "target_customer_profile": "Distributors",
                "target_regions": ["United States"],
                "uploaded_file_ids": ["file-1"],
            }
        } if hunt_id == "hunt-1" else None,
    )

    resp = client.post("/api/v1/automation/jobs/from-hunt/hunt-1", json={
        "target_lead_count": 300,
        "max_rounds": 12,
        "min_new_leads_threshold": 2,
        "enable_email_craft": True,
        "email_template_examples": ["Dear Sir/Madam"],
        "email_template_notes": "Keep it concise",
    })
    missing = client.post("/api/v1/automation/jobs/from-hunt/missing", json={})

    assert resp.status_code == 200
    assert resp.json()["job_id"] == "job-2"
    assert queued_payloads[0]["website_url"] == "https://www.gdushun.com/"
    assert queued_payloads[0]["target_lead_count"] == 300
    assert queued_payloads[0]["enable_email_craft"] is True
    assert missing.status_code == 404


def test_cancel_and_retry_automation_job(monkeypatch):
    app = create_app()
    client = TestClient(app)

    state = {
        "id": "job-3",
        "status": "queued",
        "created_at": "2026-04-05T00:00:00+00:00",
        "updated_at": "2026-04-05T00:00:00+00:00",
        "started_at": "",
        "finished_at": "",
        "attempt_count": 1,
        "last_error": "",
        "last_hunt_id": "",
        "payload": {"website_url": "https://www.gdushun.com/"},
    }

    class FakeQueue:
        def init_db(self):
            return None

        def get(self, job_id):
            if job_id != "job-3":
                return None
            return state.copy()

        def cancel(self, job_id, updated_at):
            state["status"] = "failed"
            state["finished_at"] = updated_at
            state["updated_at"] = updated_at
            state["last_error"] = "Cancelled by user"

        def retry_now(self, job_id, updated_at):
            state["status"] = "queued"
            state["updated_at"] = updated_at
            state["finished_at"] = ""

    monkeypatch.setattr("api.automation_routes._queue", lambda: FakeQueue())
    monkeypatch.setattr("api.automation_routes.load_hunt", lambda hunt_id: None)

    cancelled = client.post("/api/v1/automation/jobs/job-3/cancel")
    retried = client.post("/api/v1/automation/jobs/job-3/retry")
    missing = client.post("/api/v1/automation/jobs/missing/retry")

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "failed"
    assert "Cancelled by user" in cancelled.json()["last_error"]
    assert retried.status_code == 200
    assert retried.json()["status"] == "queued"
    assert missing.status_code == 404
