from __future__ import annotations

from automation.job_queue import HuntJobQueue


def test_enqueue_claim_and_complete(tmp_path):
    queue = HuntJobQueue(str(tmp_path / "queue.db"))
    queue.init_db()

    job_id = queue.enqueue({"description": "Find buyers"}, now_iso="2026-04-04T00:00:00+00:00")
    assert queue.count_by_status("queued") == 1

    job = queue.claim_next(worker_id="worker-a", now_iso="2026-04-04T00:00:01+00:00")
    assert job is not None
    assert job["id"] == job_id
    assert job["status"] == "running"
    assert queue.count_by_status("running") == 1

    queue.mark_completed(job_id, hunt_id="hunt-123", finished_at="2026-04-04T00:10:00+00:00")
    completed = queue.get(job_id)
    assert completed is not None
    assert completed["status"] == "completed"
    assert completed["last_hunt_id"] == "hunt-123"


def test_requeue_failed_job(tmp_path):
    queue = HuntJobQueue(str(tmp_path / "queue.db"))
    queue.init_db()
    job_id = queue.enqueue({"description": "Find buyers"}, now_iso="2026-04-04T00:00:00+00:00")
    claimed = queue.claim_next(worker_id="worker-a", now_iso="2026-04-04T00:00:01+00:00")
    assert claimed is not None

    queue.requeue(
        job_id,
        available_at="2026-04-04T00:05:00+00:00",
        error_message="temporary failure",
        updated_at="2026-04-04T00:01:00+00:00",
        hunt_id="hunt-456",
    )
    job = queue.get(job_id)
    assert job is not None
    assert job["status"] == "queued"
    assert job["last_error"] == "temporary failure"
    assert job["last_hunt_id"] == "hunt-456"


def test_cancel_and_retry_job(tmp_path):
    queue = HuntJobQueue(str(tmp_path / "queue.db"))
    queue.init_db()

    job_id = queue.enqueue({"description": "Find buyers"}, now_iso="2026-04-04T00:00:00+00:00")
    queue.cancel(job_id, updated_at="2026-04-04T00:05:00+00:00")
    cancelled = queue.get(job_id)
    assert cancelled is not None
    assert cancelled["status"] == "failed"
    assert cancelled["last_error"] == "Cancelled by user"

    queue.retry_now(job_id, updated_at="2026-04-04T00:06:00+00:00")
    retried = queue.get(job_id)
    assert retried is not None
    assert retried["status"] == "queued"
    assert retried["finished_at"] == ""


def test_recover_interrupted_running_jobs(tmp_path):
    queue = HuntJobQueue(str(tmp_path / "queue.db"))
    queue.init_db()

    job_id = queue.enqueue({"description": "Find buyers"}, now_iso="2026-04-04T00:00:00+00:00")
    claimed = queue.claim_next(worker_id="worker-a", now_iso="2026-04-04T00:00:01+00:00")
    assert claimed is not None

    recovered = queue.recover_interrupted_running_jobs(updated_at="2026-04-04T00:02:00+00:00")
    assert recovered == 1

    recovered_job = queue.get(job_id)
    assert recovered_job is not None
    assert recovered_job["status"] == "queued"
    assert recovered_job["claimed_by"] == ""
    assert recovered_job["started_at"] == ""
    assert recovered_job["progress_stage"] == "queued"
    assert "Recovered after API restart" in recovered_job["progress_message"]


def test_template_seed_prewarm_lifecycle(tmp_path):
    queue = HuntJobQueue(str(tmp_path / "queue.db"))
    queue.init_db()

    job_id = queue.enqueue(
        {
            "website_url": "https://www.gdushun.com/",
            "description": "Find distributors",
            "enable_email_craft": True,
        },
        now_iso="2026-04-04T00:00:00+00:00",
    )
    queued = queue.get(job_id)
    assert queued is not None
    assert queued["template_seed_status"] == "pending"

    assert queue.mark_template_seed_preparing(job_id, updated_at="2026-04-04T00:00:05+00:00") is True
    preparing = queue.get(job_id)
    assert preparing is not None
    assert preparing["template_seed_status"] == "preparing"

    queue.attach_template_seed(
        job_id,
        template_seed={"source": "pre_generated", "template_profile": {}, "template_plan": {}},
        updated_at="2026-04-04T00:00:10+00:00",
    )
    ready = queue.get(job_id)
    assert ready is not None
    assert ready["template_seed_status"] == "ready"
    assert ready["template_seed_source"] == "pre_generated"
    assert isinstance(ready["payload"]["template_seed"], dict)


def test_claim_next_skips_seed_jobs_while_preparing(tmp_path):
    queue = HuntJobQueue(str(tmp_path / "queue.db"))
    queue.init_db()

    slow_job = queue.enqueue(
        {"description": "Find buyers", "enable_email_craft": True},
        now_iso="2026-04-04T00:00:00+00:00",
    )
    fast_job = queue.enqueue(
        {"description": "Find buyers without email"},
        now_iso="2026-04-04T00:00:01+00:00",
    )
    assert queue.mark_template_seed_preparing(slow_job, updated_at="2026-04-04T00:00:02+00:00") is True

    claimed = queue.claim_next(worker_id="worker-a", now_iso="2026-04-04T00:00:03+00:00")
    assert claimed is not None
    assert claimed["id"] == fast_job
