"""Automation monitoring routes for headless mode."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.routes import _hunts
from api.security import require_api_access
from automation.metrics import collect_automation_metrics, collect_automation_status

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


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

