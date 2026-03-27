"""Simple scheduler for pending outbound emails."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

from api.hunt_store import load_hunt, save_hunt
from config.settings import get_settings
from emailing.email_sender import send_email
from emailing.store import EmailStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _refresh_hunt_email_summary(store: EmailStore, hunt_id: str, campaign_id: str) -> None:
    hunt = load_hunt(hunt_id)
    if not hunt:
        return
    campaign = store.get_campaign(campaign_id)
    sequences = store.list_sequences_for_campaign(campaign_id)
    settings = get_settings()
    template_summary = store.get_template_performance_for_campaign(
        campaign_id,
        underperforming_min_assigned=int(getattr(settings, "email_template_underperforming_min_assigned", 10) or 10),
        underperforming_min_reply_rate=float(getattr(settings, "email_template_underperforming_min_reply_rate", 1.0) or 1.0),
    )
    summary = {
        "campaign_id": campaign_id,
        "status": campaign.get("status", "draft") if campaign else "draft",
        "sequences_total": len(sequences),
        "sent_count": store.count_messages_for_campaign(campaign_id, status="sent"),
        "failed_count": store.count_messages_for_campaign(campaign_id, status="failed"),
        "pending_count": store.count_messages_for_campaign(campaign_id, status="pending"),
        "replied_count": sum(1 for seq in sequences if seq.get("status") == "replied"),
        "template_summary": list(template_summary.values()),
    }
    result = hunt.setdefault("result", {})
    result["email_campaign_summary"] = summary
    save_hunt(hunt_id, hunt)


async def run_scheduler_once(
    store: EmailStore,
    *,
    now_iso: str | None = None,
    sender: Callable[..., Awaitable[dict[str, Any]]] = send_email,
) -> dict[str, int]:
    """Send pending email jobs that are ready."""
    current = now_iso or _now_iso()
    jobs = store.list_pending_messages_ready(current)
    sent = 0
    failed = 0
    skipped = 0
    for job in jobs:
        sequence = store.get_sequence(str(job.get("sequence_id", "")))
        if not sequence or sequence.get("status") in {"replied", "stopped", "completed", "failed"}:
            skipped += 1
            continue
        campaign = store.get_campaign(str(sequence.get("campaign_id", "")))
        if not campaign or campaign.get("status") != "active":
            skipped += 1
            continue
        account = store.get_account(str(campaign.get("email_account_id", "")))
        if not account or account.get("status") != "active":
            store.mark_message_failed(str(job["id"]), failure_reason="inactive_email_account", updated_at=current)
            failed += 1
            continue
        template_id = str(sequence.get("template_id", "") or "")
        if template_id:
            settings = get_settings()
            template_summary = store.get_template_performance_for_campaign(
                str(sequence.get("campaign_id", "")),
                underperforming_min_assigned=int(getattr(settings, "email_template_underperforming_min_assigned", 10) or 10),
                underperforming_min_reply_rate=float(getattr(settings, "email_template_underperforming_min_reply_rate", 1.0) or 1.0),
            )
            template_perf = template_summary.get(template_id)
            template_status = str((template_perf or {}).get("status", "") or "")
            if template_status in {"underperforming", "exhausted"}:
                store.cancel_future_pending_messages(str(sequence["id"]), updated_at=current)
                store.update_sequence_status(
                    str(sequence["id"]),
                    status="stopped",
                    updated_at=current,
                    stop_reason=f"template_{template_status}",
                    next_scheduled_at="",
                )
                skipped += 1
                _refresh_hunt_email_summary(store, str(sequence["hunt_id"]), str(sequence["campaign_id"]))
                continue

        result = await sender(
            account,
            to_email=str(sequence.get("lead_email", "") or ""),
            subject=str(job.get("subject", "") or ""),
            body_text=str(job.get("body_text", "") or ""),
            reply_to=str(account.get("reply_to", "") or ""),
            thread_key=str(job.get("thread_key", "") or ""),
        )
        if result.get("ok"):
            store.mark_message_sent(
                str(job["id"]),
                provider_message_id=str(result.get("provider_message_id", "") or ""),
                thread_key=str(result.get("thread_key", "") or ""),
                sent_at=current,
            )
            step_number = int(job.get("step_number", 1) or 1)
            next_message = store.get_message_for_step(str(sequence["id"]), step_number + 1)
            next_scheduled = str(next_message.get("scheduled_at", "") or "") if next_message else ""
            store.update_sequence_status(
                str(sequence["id"]),
                status="completed" if not next_message else "running",
                updated_at=current,
                current_step=step_number,
                last_sent_at=current,
                next_scheduled_at=next_scheduled,
            )
            sent += 1
        else:
            store.mark_message_failed(
                str(job["id"]),
                failure_reason=str(result.get("error_type", "") or result.get("error", "") or "send_failed"),
                updated_at=current,
            )
            store.update_sequence_status(
                str(sequence["id"]),
                status="failed",
                updated_at=current,
                stop_reason=str(result.get("error_type", "") or "send_failed"),
            )
            failed += 1
        _refresh_hunt_email_summary(store, str(sequence["hunt_id"]), str(sequence["campaign_id"]))
    return {"sent": sent, "failed": failed, "skipped": skipped}
