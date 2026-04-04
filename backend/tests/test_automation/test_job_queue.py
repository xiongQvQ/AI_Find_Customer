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
