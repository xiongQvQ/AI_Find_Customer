from __future__ import annotations

from automation.job_queue import HuntJobQueue
from automation.metrics import collect_automation_metrics, collect_automation_status
from emailing.store import EmailStore


def test_collect_automation_status_and_metrics(monkeypatch, tmp_path):
    queue_path = str(tmp_path / "queue.db")
    email_db = str(tmp_path / "email.db")

    queue = HuntJobQueue(queue_path)
    queue.init_db()
    running_id = queue.enqueue({"description": "Find more buyers"}, now_iso="2026-04-04T00:00:00+00:00")
    claimed_completed = queue.claim_next(worker_id="worker-a", now_iso="2026-04-04T00:00:01+00:00")
    assert claimed_completed is not None
    queue.mark_completed(running_id, hunt_id="hunt-1", finished_at="9999-04-04T01:00:00+00:00")
    retry_id = queue.enqueue({"website_url": "https://retry.example.com"}, now_iso="9999-04-04T00:00:00+00:00")
    claimed_retry = queue.claim_next(worker_id="worker-b", now_iso="9999-04-04T00:05:00+00:00")
    assert claimed_retry is not None
    queue.requeue(
        retry_id,
        available_at="9999-04-04T00:10:00+00:00",
        error_message="hunt hunt-failed failed: minimax 429",
        updated_at="9999-04-04T00:06:00+00:00",
        hunt_id="hunt-failed",
    )

    store = EmailStore(email_db)
    store.init_db()
    store.create_campaign({
        "id": "cmp_1",
        "hunt_id": "hunt_1",
        "email_account_id": "acct_1",
        "name": "Campaign",
        "status": "active",
        "language_mode": "auto_by_region",
        "default_language": "en",
        "fallback_language": "en",
        "tone": "professional",
        "step1_delay_days": 0,
        "step2_delay_days": 3,
        "step3_delay_days": 7,
        "min_fit_score": 0.6,
        "min_contactability_score": 0.45,
        "created_at": "9999-04-04T00:00:00+00:00",
        "updated_at": "9999-04-04T00:00:00+00:00",
    })
    store.create_sequence({
        "id": "seq_1",
        "campaign_id": "cmp_1",
        "hunt_id": "hunt_1",
        "lead_key": "lead_1",
        "lead_email": "buyer@example.com",
        "lead_name": "Buyer",
        "decision_maker_name": "Jane",
        "decision_maker_title": "Manager",
        "locale": "en_US",
        "status": "running",
        "current_step": 1,
        "stop_reason": "",
        "replied_at": "",
        "last_sent_at": "",
        "next_scheduled_at": "",
        "created_at": "9999-04-04T00:00:00+00:00",
        "updated_at": "9999-04-04T00:00:00+00:00",
    })
    store.create_message({
        "id": "msg_1",
        "sequence_id": "seq_1",
        "step_number": 1,
        "goal": "intro",
        "locale": "en_US",
        "subject": "Hello",
        "body_text": "Body",
        "status": "sent",
        "scheduled_at": "9999-04-04T00:00:00+00:00",
        "sent_at": "9999-04-04T01:00:00+00:00",
        "provider_message_id": "",
        "thread_key": "",
        "failure_reason": "",
        "created_at": "9999-04-04T00:00:00+00:00",
        "updated_at": "9999-04-04T01:00:00+00:00",
    })
    store.create_message({
        "id": "msg_2",
        "sequence_id": "seq_1",
        "step_number": 2,
        "goal": "followup",
        "locale": "en_US",
        "subject": "Hello again",
        "body_text": "Body",
        "status": "failed",
        "scheduled_at": "9999-04-04T00:00:00+00:00",
        "sent_at": "",
        "provider_message_id": "",
        "thread_key": "",
        "failure_reason": "smtp_timeout",
        "created_at": "9999-04-04T00:00:00+00:00",
        "updated_at": "9999-04-04T01:30:00+00:00",
    })
    store.create_reply_event({
        "id": "reply_1",
        "sequence_id": "seq_1",
        "message_id": "msg_1",
        "from_email": "buyer@example.com",
        "subject": "Re: Hello",
        "snippet": "Interested",
        "received_at": "9999-04-04T02:00:00+00:00",
        "raw_ref": "raw-1",
        "created_at": "9999-04-04T02:00:00+00:00",
    })

    monkeypatch.setattr(
        "automation.metrics.get_settings",
        lambda: type("S", (), {
            "automation_queue_db_path": queue_path,
            "email_db_path": email_db,
            "email_auto_send_enabled": True,
            "email_reply_detection_enabled": True,
            "automation_summary_enabled": True,
            "automation_alerts_enabled": True,
        })(),
    )

    hunts = {
        "hunt_1": {
            "status": "completed",
            "created_at": "9999-04-04T00:00:00+00:00",
            "result": {
                "leads": [{"company_name": "A"}, {"company_name": "B"}],
                "email_sequences": [{}, {}],
            },
        },
        "hunt-failed": {
            "status": "failed",
            "created_at": "9999-04-04T00:30:00+00:00",
            "current_stage": "lead_extract",
            "error": "minimax 429",
            "payload": {"website_url": "https://retry.example.com"},
        }
    }

    status = collect_automation_status(hunts=hunts)
    metrics = collect_automation_metrics(hours=24, hunts=hunts)

    assert status["hunt_jobs"]["queued"] >= 0
    assert status["email_queue"]["sent"] == 1
    assert status["email_queue"]["active_campaigns"] == 1
    assert metrics["hunts"]["new_leads"] == 2
    assert metrics["hunt_jobs"]["retrying"] == 1
    assert metrics["emails"]["sent"] == 1
    assert metrics["emails"]["failed"] == 1
    assert metrics["emails"]["replied"] == 1
    assert metrics["recent_failed_hunts"][0]["retry_status"] == "queued_retry"
    assert metrics["recent_failures"][0]["failure_reason"] == "smtp_timeout"
    assert metrics["top_failure_reasons"][0]["failure_reason"] == "smtp_timeout"
    assert metrics["recent_completed_hunts"][0]["lead_count"] == 2


def test_collect_automation_metrics_loads_persisted_hunts_when_not_provided(monkeypatch, tmp_path):
    queue_path = str(tmp_path / "queue.db")
    email_db = str(tmp_path / "email.db")

    queue = HuntJobQueue(queue_path)
    queue.init_db()

    store = EmailStore(email_db)
    store.init_db()

    monkeypatch.setattr(
        "automation.metrics.get_settings",
        lambda: type("S", (), {
            "automation_queue_db_path": queue_path,
            "email_db_path": email_db,
            "email_auto_send_enabled": True,
            "email_reply_detection_enabled": True,
            "automation_summary_enabled": True,
            "automation_alerts_enabled": True,
        })(),
    )
    monkeypatch.setattr(
        "automation.metrics.load_all_hunts",
        lambda: {
            "hunt_2": {
                "status": "completed",
                "created_at": "9999-04-04T00:00:00+00:00",
                "result": {
                    "leads": [{"company_name": "A"}],
                    "email_sequences": [{}, {}, {}],
                },
            }
        },
    )

    metrics = collect_automation_metrics(hours=24)

    assert metrics["hunts"]["completed"] == 1
    assert metrics["hunts"]["new_leads"] == 1
    assert metrics["hunts"]["generated_email_sequences"] == 3
