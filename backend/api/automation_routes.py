"""Automation monitoring and job submission routes for queue mode."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.hunt_store import load_hunt, now_iso
from api.routes import _hunts
from api.security import require_api_access
from automation.job_queue import HuntJobQueue
from automation.metrics import collect_automation_metrics, collect_automation_status
from config.settings import get_settings

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


class AutomationJobRequest(BaseModel):
    website_url: str = ""
    description: str = ""
    product_keywords: list[str] = Field(default_factory=list)
    target_customer_profile: str = ""
    target_regions: list[str] = Field(default_factory=list)
    uploaded_file_ids: list[str] = Field(default_factory=list)
    target_lead_count: int = Field(default=200, ge=1, le=10000)
    max_rounds: int = Field(default=10, ge=1, le=50)
    min_new_leads_threshold: int = Field(default=5, ge=1, le=100)
    enable_email_craft: bool = False
    email_template_examples: list[str] = Field(default_factory=list)
    email_template_notes: str = ""


class AutomationJobContinueRequest(BaseModel):
    target_lead_count: int = Field(default=200, ge=1, le=10000)
    max_rounds: int = Field(default=10, ge=1, le=50)
    min_new_leads_threshold: int = Field(default=5, ge=1, le=100)
    enable_email_craft: bool = False
    email_template_examples: list[str] = Field(default_factory=list)
    email_template_notes: str = ""


def _queue() -> HuntJobQueue:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    return queue


def _serialize_job(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    hunt_id = str(job.get("last_hunt_id", "") or "")
    hunt = load_hunt(hunt_id) if hunt_id else None
    return {
        "job_id": str(job.get("id", "") or ""),
        "status": str(job.get("status", "") or ""),
        "created_at": str(job.get("created_at", "") or ""),
        "updated_at": str(job.get("updated_at", "") or ""),
        "started_at": str(job.get("started_at", "") or ""),
        "finished_at": str(job.get("finished_at", "") or ""),
        "attempt_count": int(job.get("attempt_count", 0) or 0),
        "last_error": str(job.get("last_error", "") or ""),
        "last_hunt_id": hunt_id,
        "website_url": str(payload.get("website_url", "") or ""),
        "description": str(payload.get("description", "") or ""),
        "product_keywords": list(payload.get("product_keywords", []) or []),
        "target_regions": list(payload.get("target_regions", []) or []),
        "target_lead_count": int(payload.get("target_lead_count", 0) or 0),
        "enable_email_craft": bool(payload.get("enable_email_craft", False)),
        "hunt_status": str((hunt or {}).get("status", "") or ""),
        "hunt_stage": str((hunt or {}).get("current_stage", "") or ""),
        "hunt_error": str((hunt or {}).get("error", "") or ""),
        "leads_count": int(((hunt or {}).get("result") or {}).get("leads_count", 0) or 0),
    }


@router.post("/jobs", dependencies=[Depends(require_api_access)])
async def create_automation_job(request: AutomationJobRequest):
    queue = _queue()
    job_id = queue.enqueue(request.model_dump(), now_iso=now_iso())
    job = queue.get(job_id)
    return _serialize_job(job or {"id": job_id, "payload": request.model_dump()})


@router.get("/jobs", dependencies=[Depends(require_api_access)])
async def list_automation_jobs(limit: int = Query(default=50, ge=1, le=200)):
    queue = _queue()
    return [_serialize_job(job) for job in queue.list_jobs(limit=limit)]


@router.get("/jobs/{job_id}", dependencies=[Depends(require_api_access)])
async def get_automation_job(job_id: str):
    queue = _queue()
    job = queue.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Automation job not found")
    return _serialize_job(job)


@router.get("/jobs/by-hunt/{hunt_id}", dependencies=[Depends(require_api_access)])
async def get_automation_job_by_hunt(hunt_id: str):
    queue = _queue()
    job = queue.get_by_hunt_id(hunt_id)
    if not job:
        raise HTTPException(status_code=404, detail="Automation job not found for hunt")
    return _serialize_job(job)


@router.post("/jobs/from-hunt/{hunt_id}", dependencies=[Depends(require_api_access)])
async def create_automation_job_from_hunt(hunt_id: str, request: AutomationJobContinueRequest):
    hunt = load_hunt(hunt_id)
    if not hunt:
        raise HTTPException(status_code=404, detail="Hunt not found")

    payload = hunt.get("payload") if isinstance(hunt.get("payload"), dict) else {}
    if not payload:
        raise HTTPException(status_code=422, detail="Hunt has no reusable payload")

    next_payload = {
        "website_url": str(payload.get("website_url", "") or ""),
        "description": str(payload.get("description", "") or ""),
        "product_keywords": list(payload.get("product_keywords", []) or []),
        "target_customer_profile": str(payload.get("target_customer_profile", "") or ""),
        "target_regions": list(payload.get("target_regions", []) or []),
        "uploaded_file_ids": list(payload.get("uploaded_file_ids", []) or []),
        "target_lead_count": int(request.target_lead_count),
        "max_rounds": int(request.max_rounds),
        "min_new_leads_threshold": int(request.min_new_leads_threshold),
        "enable_email_craft": bool(request.enable_email_craft),
        "email_template_examples": list(request.email_template_examples),
        "email_template_notes": str(request.email_template_notes or ""),
    }

    queue = _queue()
    job_id = queue.enqueue(next_payload, now_iso=now_iso())
    job = queue.get(job_id)
    return _serialize_job(job or {"id": job_id, "payload": next_payload})


@router.get("/status", dependencies=[Depends(require_api_access)])
async def get_automation_status():
    return collect_automation_status(hunts=_hunts)


@router.get("/metrics", dependencies=[Depends(require_api_access)])
async def get_automation_metrics(hours: int = Query(default=24, ge=1, le=168)):
    return collect_automation_metrics(hours=hours, hunts=_hunts)


@router.get("/health", dependencies=[Depends(require_api_access)])
async def get_automation_health():
    status = collect_automation_status(hunts=_hunts)
    metrics = collect_automation_metrics(hours=2, hunts=_hunts)
    return {
        "status": "ok",
        "backlog_hunt_jobs": status["hunt_jobs"]["queued"],
        "backlog_email_messages": status["email_queue"]["pending"],
        "recent_failed_emails": metrics["emails"]["failed"],
    }
