from pathlib import Path

import pytest

from emailing.scheduler import run_scheduler_once
from emailing.store import EmailStore


@pytest.mark.asyncio
async def test_scheduler_sends_pending_message(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "email.db"
    store = EmailStore(str(db_path))
    store.init_db()
    store.upsert_account({
        "id": "acct_1",
        "provider_type": "smtp",
        "from_name": "B2Binsights",
        "from_email": "sales@example.com",
        "reply_to": "sales@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "sales@example.com",
        "smtp_secret_encrypted": "enc",
        "imap_host": "",
        "imap_port": 993,
        "imap_username": "",
        "imap_secret_encrypted": "",
        "use_tls": 1,
        "status": "active",
        "daily_send_limit": 50,
        "hourly_send_limit": 10,
        "last_test_at": "",
        "created_at": "2026-03-09T00:00:00Z",
        "updated_at": "2026-03-09T00:00:00Z",
    })
    store.create_campaign({
        "id": "cmp_1",
        "hunt_id": "hunt_1",
        "email_account_id": "acct_1",
        "name": "Test",
        "status": "active",
        "language_mode": "auto_by_region",
        "default_language": "en",
        "fallback_language": "en",
        "tone": "professional",
        "step1_delay_days": 0,
        "step2_delay_days": 3,
        "step3_delay_days": 3,
        "min_fit_score": 0.6,
        "min_contactability_score": 0.45,
        "created_at": "2026-03-09T00:00:00Z",
        "updated_at": "2026-03-09T00:00:00Z",
    })
    store.create_sequence({
        "id": "seq_1",
        "campaign_id": "cmp_1",
        "hunt_id": "hunt_1",
        "lead_key": "w:acme.com",
        "lead_email": "buyer@acme.com",
        "lead_name": "Acme",
        "decision_maker_name": "Jane",
        "decision_maker_title": "Purchasing Manager",
        "locale": "en",
        "status": "scheduled",
        "current_step": 0,
        "stop_reason": "",
        "replied_at": "",
        "last_sent_at": "",
        "next_scheduled_at": "2026-03-09T00:00:00Z",
        "created_at": "2026-03-09T00:00:00Z",
        "updated_at": "2026-03-09T00:00:00Z",
    })
    store.create_message({
        "id": "msg_1",
        "sequence_id": "seq_1",
        "step_number": 1,
        "goal": "intro",
        "locale": "en",
        "subject": "Hello",
        "body_text": "Body",
        "status": "pending",
        "scheduled_at": "2026-03-09T00:00:00Z",
        "sent_at": "",
        "provider_message_id": "",
        "thread_key": "",
        "failure_reason": "",
        "created_at": "2026-03-09T00:00:00Z",
        "updated_at": "2026-03-09T00:00:00Z",
    })

    monkeypatch.setattr("emailing.scheduler.load_hunt", lambda hunt_id: {"result": {}})
    monkeypatch.setattr("emailing.scheduler.save_hunt", lambda hunt_id, hunt: None)

    async def fake_sender(*args, **kwargs):
        return {
            "ok": True,
            "provider_message_id": "<mid>",
            "thread_key": "thread-1",
        }

    result = await run_scheduler_once(store, now_iso="2026-03-09T01:00:00Z", sender=fake_sender)
    assert result["sent"] == 1
    assert store.list_pending_messages_ready("2026-03-09T02:00:00Z") == []


@pytest.mark.asyncio
async def test_scheduler_stops_underperforming_template_sequence(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "email.db"
    store = EmailStore(str(db_path))
    store.init_db()
    store.upsert_account({
        "id": "acct_1",
        "provider_type": "smtp",
        "from_name": "B2Binsights",
        "from_email": "sales@example.com",
        "reply_to": "sales@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "sales@example.com",
        "smtp_secret_encrypted": "enc",
        "imap_host": "",
        "imap_port": 993,
        "imap_username": "",
        "imap_secret_encrypted": "",
        "use_tls": 1,
        "status": "active",
        "daily_send_limit": 50,
        "hourly_send_limit": 10,
        "last_test_at": "",
        "created_at": "2026-03-09T00:00:00Z",
        "updated_at": "2026-03-09T00:00:00Z",
    })
    store.create_campaign({
        "id": "cmp_1",
        "hunt_id": "hunt_1",
        "email_account_id": "acct_1",
        "name": "Test",
        "status": "active",
        "language_mode": "auto_by_region",
        "default_language": "en",
        "fallback_language": "en",
        "tone": "professional",
        "step1_delay_days": 0,
        "step2_delay_days": 3,
        "step3_delay_days": 3,
        "min_fit_score": 0.6,
        "min_contactability_score": 0.45,
        "created_at": "2026-03-09T00:00:00Z",
        "updated_at": "2026-03-09T00:00:00Z",
    })
    for idx in range(1, 11):
        store.create_sequence({
            "id": f"seq_{idx}",
            "campaign_id": "cmp_1",
            "hunt_id": "hunt_1",
            "lead_key": f"lead_{idx}",
            "lead_email": f"buyer{idx}@acme.com",
            "lead_name": f"Acme {idx}",
            "decision_maker_name": "Jane",
            "decision_maker_title": "Purchasing Manager",
            "locale": "en_US",
            "generation_mode": "template_pool",
            "template_id": "tpl_bad",
            "template_group": "en_US|decision_maker_verified|general",
            "template_usage_index": idx,
            "template_max_send_count": 100,
            "status": "scheduled",
            "current_step": 0,
            "stop_reason": "",
            "replied_at": "",
            "last_sent_at": "",
            "next_scheduled_at": "2026-03-09T00:00:00Z",
            "created_at": "2026-03-09T00:00:00Z",
            "updated_at": "2026-03-09T00:00:00Z",
        })
        store.create_message({
            "id": f"msg_{idx}",
            "sequence_id": f"seq_{idx}",
            "step_number": 1,
            "goal": "intro",
            "locale": "en",
            "subject": "Hello",
            "body_text": "Body",
            "status": "pending" if idx == 1 else "sent",
            "scheduled_at": "2026-03-09T00:00:00Z",
            "sent_at": "2026-03-09T00:10:00Z" if idx != 1 else "",
            "provider_message_id": "",
            "thread_key": "",
            "failure_reason": "",
            "created_at": "2026-03-09T00:00:00Z",
            "updated_at": "2026-03-09T00:00:00Z",
        })

    monkeypatch.setattr("emailing.scheduler.load_hunt", lambda hunt_id: {"result": {}})
    monkeypatch.setattr("emailing.scheduler.save_hunt", lambda hunt_id, hunt: None)

    async def fake_sender(*args, **kwargs):
        raise AssertionError("sender should not run for blocked template")

    result = await run_scheduler_once(store, now_iso="2026-03-09T01:00:00Z", sender=fake_sender)

    assert result["sent"] == 0
    assert result["skipped"] == 1
    sequence = store.get_sequence("seq_1")
    assert sequence is not None
    assert sequence["status"] == "stopped"
    assert sequence["stop_reason"] == "template_underperforming"
    message = store.get_message("msg_1")
    assert message is not None
    assert message["status"] == "cancelled"
