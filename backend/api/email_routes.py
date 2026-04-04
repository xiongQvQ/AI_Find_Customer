"""Email campaign API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.hunt_store import load_hunt, save_hunt, now_iso
from api.security import require_api_access
from config.settings import get_settings
from emailing.readiness import ensure_imap_tested, ensure_smtp_ready, ensure_smtp_tested
from emailing.reply_detector import run_reply_detection_once
from emailing.scheduler import run_scheduler_once
from emailing.store import EmailStore

router = APIRouter(prefix="/api/v1", tags=["email"])


def _store() -> EmailStore:
    store = EmailStore(get_settings().email_db_path)
    store.init_db()
    return store


def _default_account(store: EmailStore) -> dict[str, Any]:
    settings = get_settings()
    account_id = "default"
    existing = store.get_account(account_id)
    current = now_iso()
    payload = {
        "id": account_id,
        "provider_type": settings.email_provider_type,
        "from_name": settings.email_from_name,
        "from_email": settings.email_from_address,
        "reply_to": settings.email_reply_to or settings.email_from_address,
        "smtp_host": settings.email_smtp_host,
        "smtp_port": settings.email_smtp_port,
        "smtp_username": settings.email_smtp_username,
        "smtp_secret_encrypted": settings.email_smtp_password,
        "imap_host": settings.email_imap_host,
        "imap_port": settings.email_imap_port,
        "imap_username": settings.email_imap_username,
        "imap_secret_encrypted": settings.email_imap_password,
        "use_tls": 1 if settings.email_use_tls else 0,
        "status": "active",
        "daily_send_limit": settings.email_daily_send_limit,
        "hourly_send_limit": settings.email_hourly_send_limit,
        "last_test_at": "",
        "created_at": existing.get("created_at", current) if existing else current,
        "updated_at": current,
    }
    store.upsert_account(payload)
    return store.get_account(account_id) or payload


def _campaign_summary(store: EmailStore, campaign_id: str) -> dict[str, Any]:
    settings = get_settings()
    campaign = store.get_campaign(campaign_id)
    sequences = store.list_sequences_for_campaign(campaign_id)
    template_summary = store.get_template_performance_for_campaign(
        campaign_id,
        underperforming_min_assigned=int(getattr(settings, "email_template_underperforming_min_assigned", 10) or 10),
        underperforming_min_reply_rate=float(getattr(settings, "email_template_underperforming_min_reply_rate", 1.0) or 1.0),
    )
    return {
        "campaign": campaign,
        "sequence_count": len(sequences),
        "sent_count": store.count_messages_for_campaign(campaign_id, status="sent"),
        "pending_count": store.count_messages_for_campaign(campaign_id, status="pending"),
        "failed_count": store.count_messages_for_campaign(campaign_id, status="failed"),
        "template_summary": list(template_summary.values()),
        "sequences": sequences,
    }


def _write_summary_to_hunt(store: EmailStore, hunt_id: str, campaign_id: str) -> None:
    hunt = load_hunt(hunt_id)
    if not hunt:
        return
    result = hunt.setdefault("result", {})
    settings = get_settings()
    campaign = store.get_campaign(campaign_id)
    sequences = store.list_sequences_for_campaign(campaign_id)
    template_summary = store.get_template_performance_for_campaign(
        campaign_id,
        underperforming_min_assigned=int(getattr(settings, "email_template_underperforming_min_assigned", 10) or 10),
        underperforming_min_reply_rate=float(getattr(settings, "email_template_underperforming_min_reply_rate", 1.0) or 1.0),
    )
    result["email_campaign_summary"] = {
        "campaign_id": campaign_id,
        "status": campaign.get("status", "draft") if campaign else "draft",
        "sequences_total": len(sequences),
        "sent_count": store.count_messages_for_campaign(campaign_id, status="sent"),
        "failed_count": store.count_messages_for_campaign(campaign_id, status="failed"),
        "pending_count": store.count_messages_for_campaign(campaign_id, status="pending"),
        "replied_count": sum(1 for seq in sequences if seq.get("status") == "replied"),
        "template_summary": list(template_summary.values()),
    }
    generated_sequences = result.get("email_sequences")
    if isinstance(generated_sequences, list):
        for sequence in generated_sequences:
            if not isinstance(sequence, dict):
                continue
            template_id = str(sequence.get("template_id") or "")
            if template_id and template_id in template_summary:
                performance = template_summary[template_id]
                sequence["template_assigned_count"] = performance.get("assigned_count", sequence.get("template_assigned_count", 0))
                sequence["template_remaining_capacity"] = performance.get("remaining_capacity", sequence.get("template_remaining_capacity", 0))
                sequence["template_performance"] = {
                    "sent_count": performance.get("sent_count", 0),
                    "replied_count": performance.get("replied_count", 0),
                    "reply_rate": performance.get("reply_rate", 0.0),
                    "status": performance.get("status", "warming_up"),
                    "optimization_needed": bool(performance.get("optimization_needed", False)),
                    "recommended_action": str(performance.get("recommended_action", "keep_collecting_data") or "keep_collecting_data"),
                    "reason": str(performance.get("reason", "") or ""),
                }
    save_hunt(hunt_id, hunt)


class CreateCampaignRequest(BaseModel):
    name: str = "Outbound Campaign"


class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    sequence_count: int


@router.post("/hunts/{hunt_id}/email-campaigns", response_model=CampaignResponse, dependencies=[Depends(require_api_access)])
async def create_email_campaign(hunt_id: str, payload: CreateCampaignRequest):
    hunt = load_hunt(hunt_id)
    if not hunt or not isinstance(hunt.get("result"), dict):
        raise HTTPException(status_code=404, detail="Hunt result not found")
    sequences = hunt["result"].get("email_sequences", [])
    if not isinstance(sequences, list) or not sequences:
        raise HTTPException(status_code=400, detail="No generated email sequences found for this hunt")

    settings = get_settings()
    try:
        ensure_smtp_ready(settings)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    store = _store()
    account = _default_account(store)
    campaign_id = str(uuid.uuid4())
    created = now_iso()
    store.create_campaign({
        "id": campaign_id,
        "hunt_id": hunt_id,
        "email_account_id": account["id"],
        "name": payload.name,
        "status": "draft",
        "language_mode": settings.email_language_mode,
        "default_language": settings.email_default_language,
        "fallback_language": settings.email_fallback_language,
        "tone": settings.email_tone,
        "step1_delay_days": settings.email_step1_delay_days,
        "step2_delay_days": settings.email_step2_delay_days,
        "step3_delay_days": settings.email_step3_delay_days,
        "min_fit_score": settings.email_min_fit_score_to_send,
        "min_contactability_score": settings.email_min_contactability_score_to_send,
        "created_at": created,
        "updated_at": created,
    })
    base_time = datetime.now(timezone.utc)
    for seq in sequences:
        lead = seq.get("lead") or {}
        target = seq.get("target") or {}
        emails = seq.get("emails") or []
        template_perf = seq.get("template_performance") or {}
        template_status = str(template_perf.get("status", "") or "")
        if not target.get("target_email") or not emails:
            continue
        if template_status in {"underperforming", "exhausted"}:
            continue
        sequence_id = str(uuid.uuid4())
        store.create_sequence({
            "id": sequence_id,
            "campaign_id": campaign_id,
            "hunt_id": hunt_id,
            "lead_key": str((lead.get("website") or lead.get("company_name") or sequence_id)).lower(),
            "lead_email": str(target.get("target_email") or ""),
            "lead_name": str(lead.get("company_name") or ""),
            "decision_maker_name": str(target.get("target_name") or ""),
            "decision_maker_title": str(target.get("target_title") or ""),
            "locale": str(seq.get("locale") or "en_US"),
            "generation_mode": str(seq.get("generation_mode") or "personalized"),
            "template_id": str(seq.get("template_id") or ""),
            "template_group": str(seq.get("template_group") or ""),
            "template_usage_index": int(seq.get("template_usage_index", 0) or 0),
            "template_max_send_count": int(seq.get("template_max_send_count", 0) or 0),
            "status": "scheduled",
            "current_step": 0,
            "stop_reason": "",
            "replied_at": "",
            "last_sent_at": "",
            "next_scheduled_at": "",
            "created_at": created,
            "updated_at": created,
        })
        next_scheduled = ""
        for email in emails:
            step_number = int(email.get("sequence_number", 1) or 1)
            delay_days = int(email.get("suggested_send_day", 0) or 0)
            scheduled_at = (base_time + timedelta(days=delay_days)).isoformat()
            if step_number == 1:
                next_scheduled = scheduled_at
            store.create_message({
                "id": str(uuid.uuid4()),
                "sequence_id": sequence_id,
                "step_number": step_number,
                "goal": str(email.get("email_type", "") or ""),
                "locale": str(seq.get("locale") or "en_US"),
                "subject": str(email.get("subject", "") or ""),
                "body_text": str(email.get("body_text", "") or ""),
                "status": "pending",
                "scheduled_at": scheduled_at,
                "sent_at": "",
                "provider_message_id": "",
                "thread_key": "",
                "failure_reason": "",
                "created_at": created,
                "updated_at": created,
            })
        store.update_sequence_status(sequence_id, status="scheduled", updated_at=created, next_scheduled_at=next_scheduled)

    _write_summary_to_hunt(store, hunt_id, campaign_id)
    summary = _campaign_summary(store, campaign_id)
    return CampaignResponse(campaign_id=campaign_id, status="draft", sequence_count=summary["sequence_count"])


@router.get("/hunts/{hunt_id}/email-campaigns", dependencies=[Depends(require_api_access)])
async def list_email_campaigns(hunt_id: str):
    store = _store()
    campaigns = store.list_campaigns_for_hunt(hunt_id)
    return [{"campaign": c, **_campaign_summary(store, c["id"])} for c in campaigns]


@router.post("/email-campaigns/{campaign_id}/start", dependencies=[Depends(require_api_access)])
async def start_email_campaign(campaign_id: str):
    store = _store()
    campaign = store.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    settings = get_settings()
    try:
        ensure_smtp_tested(settings)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if str(campaign.get("email_account_id", "")) == "default":
        _default_account(store)
    updated = now_iso()
    store.update_campaign_status(campaign_id, "active", updated_at=updated)
    _write_summary_to_hunt(store, str(campaign["hunt_id"]), campaign_id)
    return {"campaign_id": campaign_id, "status": "active"}


@router.post("/email-campaigns/{campaign_id}/pause", dependencies=[Depends(require_api_access)])
async def pause_email_campaign(campaign_id: str):
    store = _store()
    campaign = store.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    updated = now_iso()
    store.update_campaign_status(campaign_id, "paused", updated_at=updated)
    _write_summary_to_hunt(store, str(campaign["hunt_id"]), campaign_id)
    return {"campaign_id": campaign_id, "status": "paused"}


@router.get("/email-sequences/{sequence_id}", dependencies=[Depends(require_api_access)])
async def get_email_sequence(sequence_id: str):
    store = _store()
    sequence = store.get_sequence(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    messages = store.list_messages_for_sequence(sequence_id)
    reply_events = store.list_reply_events_for_sequence(sequence_id)
    return {"sequence": sequence, "messages": messages, "reply_events": reply_events}


@router.post("/email-scheduler/run", dependencies=[Depends(require_api_access)])
async def run_email_scheduler():
    store = _store()
    try:
        ensure_smtp_tested(get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return await run_scheduler_once(store)


@router.post("/email-replies/check", dependencies=[Depends(require_api_access)])
async def run_email_reply_check():
    store = _store()
    settings = get_settings()
    try:
        ensure_imap_tested(settings)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    account = _default_account(store)
    return await run_reply_detection_once(store, account)
