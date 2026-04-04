from __future__ import annotations

import argparse
import pytest

from automation.job_queue import HuntJobQueue
from scripts.hunt_queue import run_consumer, run_producer


def test_producer_enqueues_job(monkeypatch, tmp_path):
    queue_path = str(tmp_path / "queue.db")
    monkeypatch.setattr(
        "scripts.hunt_queue.get_settings",
        lambda: type("S", (), {"automation_queue_db_path": queue_path, "api_port": 8000, "api_access_token": ""})(),
    )

    args = argparse.Namespace(
        payload_file="",
        website_url=None,
        description="Find distributors",
        product_keywords=["micro switch"],
        target_customer_profile="Distributors",
        target_regions=["United States"],
        target_lead_count=100,
        max_rounds=8,
        min_new_leads_threshold=5,
        enable_email_craft=True,
        email_template_examples=[],
        email_template_notes="",
        continuous=False,
        enqueue_interval_seconds=60,
        max_pending_jobs=1,
    )

    assert run_producer(args) == 0
    queue = HuntJobQueue(queue_path)
    queue.init_db()
    assert queue.count_by_status("queued") == 1


def test_consumer_claims_job_and_runs_hunt(monkeypatch, tmp_path):
    queue_path = str(tmp_path / "queue.db")
    monkeypatch.setattr(
        "scripts.hunt_queue.get_settings",
        lambda: type("S", (), {"automation_queue_db_path": queue_path, "api_port": 8000, "api_access_token": ""})(),
    )
    queue = HuntJobQueue(queue_path)
    queue.init_db()
    job_id = queue.enqueue({"description": "Find distributors"}, now_iso="2026-04-04T00:00:00+00:00")

    monkeypatch.setattr(
        "scripts.hunt_queue.run_hunt_payload",
        lambda args, payload: {"hunt_id": "hunt-123", "lead_count": 100, "email_sequence_count": 20, "campaign": {"campaign_id": "camp-456", "status": "active"}},
    )

    args = argparse.Namespace(
        api_base_url="http://127.0.0.1:8000",
        api_token="",
        continuous=False,
        poll_seconds=1,
        retry_delay_seconds=120,
        status_poll_seconds=15,
        request_timeout_seconds=60,
        auto_start_campaign=True,
        campaign_name_prefix="Auto Campaign",
    )

    assert run_consumer(args) == 0
    job = queue.get(job_id)
    assert job is not None
    assert job["status"] == "completed"
    assert job["last_hunt_id"] == "hunt-123"


def test_consumer_requeues_failed_hunt_with_last_hunt_id(monkeypatch, tmp_path):
    queue_path = str(tmp_path / "queue.db")
    monkeypatch.setattr(
        "scripts.hunt_queue.get_settings",
        lambda: type("S", (), {"automation_queue_db_path": queue_path, "api_port": 8000, "api_access_token": ""})(),
    )
    queue = HuntJobQueue(queue_path)
    queue.init_db()
    job_id = queue.enqueue({"website_url": "https://www.gdushun.com/"}, now_iso="2026-04-04T00:00:00+00:00")

    monkeypatch.setattr(
        "scripts.hunt_queue.run_hunt_payload",
        lambda args, payload: (_ for _ in ()).throw(RuntimeError("hunt hunt-999 failed: minimax 429")),
    )

    args = argparse.Namespace(
        api_base_url="http://127.0.0.1:8000",
        api_token="",
        continuous=False,
        poll_seconds=1,
        retry_delay_seconds=120,
        status_poll_seconds=15,
        request_timeout_seconds=60,
        auto_start_campaign=True,
        campaign_name_prefix="Auto Campaign",
    )

    assert run_consumer(args) == 1
    job = queue.get(job_id)
    assert job is not None
    assert job["status"] == "queued"
    assert job["last_hunt_id"] == "hunt-999"
    assert "minimax 429" in job["last_error"]
