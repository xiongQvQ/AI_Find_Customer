"""SSE streaming endpoint — real-time hunt progress updates via Server-Sent Events.

Uses queue-based broadcast from routes._broadcast for instant event delivery
instead of polling.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.routes import _hunts, _sse_queues
from api.security import require_api_access

logger = logging.getLogger(__name__)

sse_router = APIRouter()


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {json_data}\n\n"


async def _event_generator(hunt_id: str, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Generate SSE events for a hunt's progress.

    Listens on a per-subscriber asyncio.Queue that receives events
    broadcast by _run_hunt in routes.py.
    """
    try:
        # Send current state as initial heartbeat
        hunt = _hunts[hunt_id]
        yield _sse_event("heartbeat", {
            "status": hunt["status"],
            "current_stage": hunt.get("current_stage"),
            "hunt_round": hunt.get("hunt_round", 0),
            "leads_count": hunt.get("leads_count", 0),
            "email_sequences_count": hunt.get("email_sequences_count", 0),
        })

        # Replay all completed stage snapshots so late-joining clients get history
        for snapshot in hunt.get("stage_snapshots", {}).values():
            yield _sse_event("stage_data", snapshot)

        # If already completed/failed, send final event and close
        if hunt["status"] == "completed":
            result = hunt.get("result") or {}
            yield _sse_event("completed", {
                "leads_count": len(result.get("leads", [])) if isinstance(result, dict) else 0,
                "email_sequences_count": len(result.get("email_sequences", [])) if isinstance(result, dict) else 0,
                "hunt_round": result.get("hunt_round", 0) if isinstance(result, dict) else 0,
            })
            return
        if hunt["status"] == "failed":
            yield _sse_event("failed", {"error": hunt.get("error", "Unknown error")})
            return

        # Listen for broadcast events
        while True:
            try:
                event, data = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield _sse_event(event, data)
                if event in ("completed", "failed"):
                    return
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                h = _hunts.get(hunt_id, {})
                yield _sse_event("heartbeat", {
                    "status": h.get("status", "unknown"),
                    "current_stage": h.get("current_stage"),
                    "hunt_round": h.get("hunt_round", 0),
                    "leads_count": h.get("leads_count", 0),
                    "email_sequences_count": h.get("email_sequences_count", 0),
                })
                # Check if hunt ended while we were waiting
                if h.get("status") in ("completed", "failed"):
                    return
    finally:
        # Unregister subscriber
        if hunt_id in _sse_queues:
            try:
                _sse_queues[hunt_id].remove(queue)
            except ValueError:
                pass
            if not _sse_queues[hunt_id]:
                del _sse_queues[hunt_id]


@sse_router.get("/hunts/{hunt_id}/stream", dependencies=[Depends(require_api_access)])
async def stream_hunt(hunt_id: str):
    """Stream real-time hunt progress via SSE.

    Event types:
    - stage_change: Pipeline stage changed (insight, keyword_gen, search, etc.)
    - round_change: New hunting round started
    - progress: Lead count updated
    - lead_progress: Per-URL extraction progress (scraping, lead_found, scrape_done, etc.)
    - completed: Hunt finished successfully
    - failed: Hunt failed with error
    - heartbeat: Keep-alive ping
    """
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    # Create a per-subscriber queue
    queue: asyncio.Queue = asyncio.Queue()
    if hunt_id not in _sse_queues:
        _sse_queues[hunt_id] = []
    _sse_queues[hunt_id].append(queue)

    return StreamingResponse(
        _event_generator(hunt_id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
