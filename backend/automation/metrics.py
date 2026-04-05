"""Automation status and metrics helpers for headless mode."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from automation.job_queue import HuntJobQueue
from automation.runtime import get_runtime_state
from api.hunt_store import load_all_hunts
from config.settings import get_settings
from emailing.store import EmailStore


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _since_iso(hours: int) -> str:
    return (_now() - timedelta(hours=max(1, hours))).isoformat()


def _resolve_hunt_map(hunts: dict[str, dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    if hunts is not None:
        return hunts
    return load_all_hunts()


def collect_automation_status(*, hunts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    store = EmailStore(settings.email_db_path)
    store.init_db()
    hunt_map = _resolve_hunt_map(hunts)

    running_hunts = [hunt for hunt in hunt_map.values() if str(hunt.get("status", "")) == "running"]
    pending_hunts = sum(1 for hunt in hunt_map.values() if str(hunt.get("status", "")) == "pending")
    running_details = []
    for hunt in running_hunts[:5]:
        running_details.append({
            "hunt_id": str(hunt.get("hunt_id", "") or ""),
            "website_url": str(hunt.get("payload", {}).get("website_url", "") or ""),
            "current_stage": str(hunt.get("current_stage", "") or ""),
            "leads_count": int(hunt.get("leads_count", 0) or 0),
            "email_sequences_count": int(hunt.get("email_sequences_count", 0) or 0),
        })

    return {
        "hunt_jobs": {
            "queued": queue.count_by_status("queued"),
            "running": queue.count_by_status("running"),
            "failed": queue.count_by_status("failed"),
        },
        "hunts": {
            "running": len(running_hunts),
            "pending": pending_hunts,
            "running_details": running_details,
        },
        "email_queue": {
            "pending": store.count_messages_by_status("pending"),
            "sent": store.count_messages_by_status("sent"),
            "failed": store.count_messages_by_status("failed"),
            "cancelled": store.count_messages_by_status("cancelled"),
            "active_campaigns": store.count_campaigns_by_status("active"),
            "draft_campaigns": store.count_campaigns_by_status("draft"),
            "active_sequences": store.count_sequences_by_status("scheduled", "running"),
            "replied_sequences": store.count_sequences_by_status("replied"),
        },
        "features": {
            "email_auto_send_enabled": bool(settings.email_auto_send_enabled),
            "email_reply_detection_enabled": bool(settings.email_reply_detection_enabled),
            "automation_summary_enabled": bool(settings.automation_summary_enabled),
            "automation_alerts_enabled": bool(settings.automation_alerts_enabled),
        },
        "workers": get_runtime_state(),
    }


def collect_automation_metrics(*, hours: int = 24, hunts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    store = EmailStore(settings.email_db_path)
    store.init_db()
    since_iso = _since_iso(hours)
    hunt_map = _resolve_hunt_map(hunts)

    recent_hunts = [
        (hunt_id, hunt) for hunt_id, hunt in hunt_map.items()
        if str(hunt.get("created_at", "") or "") >= since_iso
    ]
    completed_hunts = [(hunt_id, hunt) for hunt_id, hunt in recent_hunts if str(hunt.get("status", "")) == "completed"]
    failed_hunts = [(hunt_id, hunt) for hunt_id, hunt in recent_hunts if str(hunt.get("status", "")) == "failed"]

    new_leads = 0
    generated_sequences = 0
    recent_completed = []
    recent_failed_details = []
    for hunt_id, hunt in completed_hunts:
        result = hunt.get("result") or {}
        leads = result.get("leads") or []
        sequences = result.get("email_sequences") or []
        if isinstance(leads, list):
            new_leads += len(leads)
        if isinstance(sequences, list):
            generated_sequences += len(sequences)
        recent_completed.append({
            "hunt_id": str(hunt.get("hunt_id", "") or hunt_id),
            "website_url": str(hunt.get("payload", {}).get("website_url", "") or ""),
            "lead_count": len(leads) if isinstance(leads, list) else 0,
            "email_sequence_count": len(sequences) if isinstance(sequences, list) else 0,
            "status": str(hunt.get("status", "") or ""),
        })
    recent_completed = recent_completed[-3:]

    retrying_jobs = queue.list_recent_retrying_jobs(since_iso=since_iso, limit=10)
    retry_lookup: dict[str, dict[str, Any]] = {}
    for job in retrying_jobs:
        last_hunt_id = str(job.get("last_hunt_id", "") or "")
        if last_hunt_id:
            retry_lookup[last_hunt_id] = job

    for hunt_id, hunt in failed_hunts[-5:]:
        resolved_hunt_id = str(hunt.get("hunt_id", "") or hunt_id)
        retry_job = retry_lookup.get(resolved_hunt_id)
        retry_status = "not_scheduled"
        retry_attempts = 0
        if retry_job:
            retry_status = f"{str(retry_job.get('status', '') or 'queued')}_retry"
            retry_attempts = int(retry_job.get("attempt_count", 0) or 0)
        recent_failed_details.append({
            "hunt_id": resolved_hunt_id,
            "website_url": str(hunt.get("payload", {}).get("website_url", "") or ""),
            "current_stage": str(hunt.get("current_stage", "") or ""),
            "error": str(hunt.get("error", "") or ""),
            "retry_status": retry_status,
            "retry_attempts": retry_attempts,
        })

    return {
        "window_hours": hours,
        "since": since_iso,
        "hunt_jobs": {
            "completed": queue.count_finished_since("completed", since_iso),
            "failed": queue.count_finished_since("failed", since_iso),
            "queued": queue.count_by_status("queued"),
            "running": queue.count_by_status("running"),
            "retrying": queue.count_retrying_since(since_iso),
        },
        "hunts": {
            "created": len(recent_hunts),
            "completed": len(completed_hunts),
            "failed": len(failed_hunts),
            "new_leads": new_leads,
            "generated_email_sequences": generated_sequences,
        },
        "emails": {
            "queued": store.count_messages_by_status("pending"),
            "sent": store.count_messages_since("sent", since_iso=since_iso, time_field="sent_at"),
            "failed": store.count_messages_since("failed", since_iso=since_iso, time_field="updated_at"),
            "replied": store.count_reply_events_since(since_iso),
            "active_campaigns": store.count_campaigns_by_status("active"),
            "draft_campaigns": store.count_campaigns_by_status("draft"),
            "active_sequences": store.count_sequences_by_status("scheduled", "running"),
            "replied_sequences": store.count_sequences_by_status("replied"),
        },
        "recent_failures": store.list_recent_message_failures(since_iso=since_iso, limit=10),
        "recent_sent_messages": store.list_sent_messages_since(since_iso=since_iso, limit=10),
        "recent_reply_events": store.list_reply_events_since(since_iso=since_iso, limit=10),
        "top_failure_reasons": store.list_message_failure_reasons(since_iso=since_iso, limit=5),
        "recent_completed_hunts": recent_completed,
        "recent_failed_hunts": recent_failed_details,
    }
