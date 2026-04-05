from __future__ import annotations

import pytest

from api.app import _run_automation_consumer_once
from automation.job_queue import HuntJobQueue


@pytest.mark.asyncio
async def test_embedded_consumer_claims_and_completes_job(monkeypatch, tmp_path):
    queue_path = str(tmp_path / "queue.db")
    queue = HuntJobQueue(queue_path)
    queue.init_db()
    job_id = queue.enqueue(
        {"website_url": "https://www.gdushun.com/", "description": "Find distributors"},
        now_iso="2026-04-05T00:00:00+00:00",
    )

    settings = type(
        "S",
        (),
        {
            "automation_queue_db_path": queue_path,
            "automation_consumer_auto_start_campaign": True,
            "automation_consumer_status_poll_seconds": 15,
            "automation_consumer_request_timeout_seconds": 60,
            "automation_consumer_retry_delay_seconds": 120,
            "automation_consumer_poll_seconds": 5,
            "automation_embedded_consumer_enabled": True,
            "api_host": "127.0.0.1",
            "api_port": 8000,
            "api_access_token": "",
        },
    )()
    monkeypatch.setattr("api.app.get_settings", lambda: settings)
    monkeypatch.setattr(
        "api.app.run_hunt_payload",
        lambda args, payload: {"hunt_id": "hunt-embedded", "lead_count": 3, "email_sequence_count": 2, "campaign": None},
    )

    assert await _run_automation_consumer_once() is True
    job = queue.get(job_id)
    assert job is not None
    assert job["status"] == "completed"
    assert job["last_hunt_id"] == "hunt-embedded"
    assert job["progress_stage"] == "completed"
