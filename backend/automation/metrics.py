"""Automation status and metrics helpers for headless mode."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from automation.job_queue import HuntJobQueue
from config.settings import get_settings
from emailing.store import EmailStore


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _since_iso(hours: int) -> str:
    return (_now() - timedelta(hours=max(1, hours))).isoformat()


def collect_automation_status(*, hunts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    store = EmailStore(settings.email_db_path)
    store.init_db()
    hunt_map = hunts or {}

    running_hunts = sum(1 for hunt in hunt_map.values() if str(hunt.get("status", "")) == "running")
    pending_hunts = sum(1 for hunt in hunt_map.values() if str(hunt.get("status", "")) == "pending")

    return {
        "hunt_jobs": {
            "queued": queue.count_by_status("queued"),
            "running": queue.count_by_status("running"),
            "failed": queue.count_by_status("failed"),
        },
        "hunts": {
            "running": running_hunts,
            "pending": pending_hunts,
        },
        "email_queue": {
            "pending": store.count_messages_by_status("pending"),
            "sent": store.count_messages_by_status("sent"),
            "failed": store.count_messages_by_status("failed"),
            "cancelled": store.count_messages_by_status("cancelled"),
        },
        "features": {
            "email_auto_send_enabled": bool(settings.email_auto_send_enabled),
            "email_reply_detection_enabled": bool(settings.email_reply_detection_enabled),
            "automation_summary_enabled": bool(settings.automation_summary_enabled),
            "automation_alerts_enabled": bool(settings.automation_alerts_enabled),
        },
    }


def collect_automation_metrics(*, hours: int = 24, hunts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    store = EmailStore(settings.email_db_path)
    store.init_db()
    since_iso = _since_iso(hours)
    hunt_map = hunts or {}

    recent_hunts = [
        hunt for hunt in hunt_map.values()
        if str(hunt.get("created_at", "") or "") >= since_iso
    ]
    completed_hunts = [hunt for hunt in recent_hunts if str(hunt.get("status", "")) == "completed"]
    failed_hunts = [hunt for hunt in recent_hunts if str(hunt.get("status", "")) == "failed"]

    new_leads = 0
    generated_sequences = 0
    for hunt in completed_hunts:
        result = hunt.get("result") or {}
        leads = result.get("leads") or []
        sequences = result.get("email_sequences") or []
        if isinstance(leads, list):
            new_leads += len(leads)
        if isinstance(sequences, list):
            generated_sequences += len(sequences)

    return {
        "window_hours": hours,
        "since": since_iso,
        "hunt_jobs": {
            "completed": queue.count_finished_since("completed", since_iso),
            "failed": queue.count_finished_since("failed", since_iso),
            "queued": queue.count_by_status("queued"),
            "running": queue.count_by_status("running"),
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
        },
        "recent_failures": store.list_recent_message_failures(since_iso=since_iso, limit=10),
    }

