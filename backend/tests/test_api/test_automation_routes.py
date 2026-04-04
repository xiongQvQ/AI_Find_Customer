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
