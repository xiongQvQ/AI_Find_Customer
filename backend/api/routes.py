"""API routes — hunt endpoints, health check, status, SSE stream."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Literal

import os
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from agents.parse_description_agent import parse_description_node
from agents.insight_agent import insight_node
from agents.keyword_gen_agent import keyword_gen_node
from agents.search_agent import search_node
from agents.lead_extract_agent import lead_extract_node, set_progress_callback
from agents.email_craft_agent import email_craft_node
from config.settings import get_settings
from emailing.template_pipeline import compose_template_plan, extract_template_profile
from emailing.imap_client import search_recent_replies
from emailing.readiness import ensure_imap_ready, ensure_imap_tested, ensure_smtp_ready
from tools.llm_client import LLMTool
from emailing.smtp_client import send_smtp_email
from api.hunt_store import load_all_hunts, save_hunt, now_iso
from api.security import require_api_access
from graph.builder import build_graph
from graph.evaluate import evaluate_progress, should_continue_hunting, _build_keyword_performance
from observability.cost_tracker import get_tracker, remove_tracker

logger = logging.getLogger(__name__)

router = APIRouter()
# ── In-memory hunt store — hydrated from disk on startup ─────────────────
_hunts: dict[str, dict] = load_all_hunts(mark_interrupted=True)
# SSE event queues per hunt — subscribers listen here
_sse_queues: dict[str, list[asyncio.Queue]] = {}
_reply_detection_task: asyncio.Task[Any] | None = None


class HuntCancelledError(RuntimeError):
    """Raised when a running hunt was cancelled by the operator."""


def request_hunt_cancel(hunt_id: str, reason: str = "Cancelled by user") -> bool:
    hunt = _hunts.get(hunt_id)
    if not hunt:
        return False
    hunt["cancel_requested"] = True
    hunt["cancel_reason"] = reason
    save_hunt(hunt_id, hunt)
    logger.info("[Hunt %s] cancellation requested: %s", hunt_id[:8], reason)
    return True


def _raise_if_hunt_cancelled(hunt_id: str) -> None:
    hunt = _hunts.get(hunt_id) or {}
    if bool(hunt.get("cancel_requested")):
        raise HuntCancelledError(str(hunt.get("cancel_reason") or "Cancelled by user"))


def _lead_key(lead: dict[str, Any]) -> str:
    website = str(lead.get("website", "") or "").strip().lower()
    if website:
        return f"w:{website}"
    company_name = str(lead.get("company_name", "") or "").strip().lower()
    if company_name:
        return f"c:{company_name}"
    emails = lead.get("emails") or []
    if isinstance(emails, list) and emails:
        return f"e:{str(emails[0]).strip().lower()}"
    return "raw:" + json.dumps(lead, sort_keys=True, ensure_ascii=False)


def _dedupe_leads(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for lead in leads:
        if isinstance(lead, dict):
            merged[_lead_key(lead)] = lead
    return list(merged.values())


def _unique_leads_count(leads: list[dict[str, Any]]) -> int:
    return len(_dedupe_leads(leads))


def _validate_uploaded_file_ids(file_ids: list[str]) -> list[str]:
    """Accept only files that exist under the managed upload directory."""
    if not file_ids:
        return []

    upload_root = Path(get_settings().upload_dir).resolve()
    validated: list[str] = []
    for raw_path in file_ids:
        resolved = Path(raw_path).resolve()
        try:
            resolved.relative_to(upload_root)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="uploaded_file_ids must reference files returned by /upload.") from exc
        if not resolved.is_file():
            raise HTTPException(status_code=400, detail=f"Uploaded file not found: {resolved.name}")
        validated.append(str(resolved))
    return validated


# ── Request / Response models ───────────────────────────────────────────

class HuntRequest(BaseModel):
    website_url: str = ""
    description: str = Field(default="", description="Free-form description, e.g. '我想找东南亚的旅行社'")
    product_keywords: list[str] = Field(default_factory=list)
    target_customer_profile: str = Field(default="", description="Target customer type, e.g. '批发商和代理商', 'distributors and wholesalers'")
    target_regions: list[str] = Field(default_factory=list)
    uploaded_file_ids: list[str] = Field(default_factory=list, description="File paths returned by /upload endpoint")
    target_lead_count: int = Field(default=200, ge=1, le=10000)
    max_rounds: int = Field(default=10, ge=1, le=50)
    min_new_leads_threshold: int = Field(default=5, ge=1, le=100)
    enable_email_craft: bool = Field(default=False, description="Whether to generate emails after hunting")
    email_template_examples: list[str] = Field(default_factory=list, description="Optional historical outreach emails or template samples from the user")
    email_template_notes: str = Field(default="", description="Optional notes about preferred style, offer, or constraints")
    template_seed: dict[str, Any] | None = None


class ResumeRequest(BaseModel):
    target_lead_count: int = Field(default=200, ge=1, le=10000)
    max_rounds: int = Field(default=10, ge=1, le=50)
    min_new_leads_threshold: int = Field(default=5, ge=1, le=100)
    enable_email_craft: bool = Field(default=False)
    email_template_examples: list[str] = Field(default_factory=list)
    email_template_notes: str = ""
    template_seed: dict[str, Any] | None = None


class TemplateSeedRequest(BaseModel):
    website_url: str = ""
    description: str = ""
    product_keywords: list[str] = Field(default_factory=list)
    target_customer_profile: str = ""
    target_regions: list[str] = Field(default_factory=list)
    uploaded_file_ids: list[str] = Field(default_factory=list)
    email_template_examples: list[str] = Field(default_factory=list)
    email_template_notes: str = ""


class TemplateSeedResponse(BaseModel):
    template_seed: dict[str, Any]


class HuntResponse(BaseModel):
    hunt_id: str
    status: str


class HuntStatus(BaseModel):
    hunt_id: str
    status: str
    current_stage: str | None = None
    hunt_round: int = 0
    leads_count: int = 0
    email_sequences_count: int = 0
    error: str | None = None


class HuntResult(BaseModel):
    hunt_id: str
    status: str
    insight: dict | None = None
    leads: list[dict] = Field(default_factory=list)
    email_sequences: list[dict] = Field(default_factory=list)
    used_keywords: list[str] = Field(default_factory=list)
    hunt_round: int = 0
    round_feedback: dict | None = None
    keyword_search_stats: dict = Field(default_factory=dict)
    search_result_count: int = 0


class EmailSequenceDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = ""


class EmailSequenceDecisionResponse(BaseModel):
    hunt_id: str
    sequence_index: int
    decision: str
    auto_send_eligible: bool
    manual_review: dict[str, Any]


class SendEmailDraftRequest(BaseModel):
    sequence_number: int = Field(default=1, ge=1, le=3)


class SendEmailDraftResponse(BaseModel):
    hunt_id: str
    sequence_index: int
    sequence_number: int
    sent_to: str
    subject: str
    status: str


class DetectReplyResponse(BaseModel):
    hunt_id: str
    sequence_index: int
    reply_count: int
    replies: list[dict[str, str]]


# ── SSE helpers ────────────────────────────────────────────────────────

def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _broadcast(hunt_id: str, event: str, data: dict) -> None:
    """Push an SSE event to all subscribers of a hunt."""
    for q in _sse_queues.get(hunt_id, []):
        q.put_nowait((event, data))


def _clean_email(value: str) -> str:
    return str(value or "").replace("(inferred)", "").strip()


def _fallback_template_seed(request: TemplateSeedRequest, insight: dict[str, Any]) -> dict[str, Any]:
    synthetic_buyer = {
        "company_name": request.target_customer_profile or "Target Buyer",
        "industry": request.target_customer_profile or "Potential distributor or importer",
        "description": request.description,
        "website": "",
        "country_code": "",
    }
    return {
        "source": "pre_generated",
        "prepared_from": {
            "website_url": request.website_url,
            "description": request.description,
            "product_keywords": list(request.product_keywords),
            "target_customer_profile": request.target_customer_profile,
            "target_regions": list(request.target_regions),
        },
        "synthetic_buyer": synthetic_buyer,
        "insight_snapshot": insight,
        "template_profile": {
            "source": "auto_generated",
            "tone": "professional",
            "subject_style": "specific and low-pressure",
        },
        "template_plan": {
            "template_source": "auto_generated",
            "recipient_profile": synthetic_buyer["industry"],
            "cta_strategy": "Ask a low-friction qualification question.",
        },
        "notes": request.email_template_notes,
    }


def _template_seed_cache_key(request: TemplateSeedRequest) -> str:
    payload = {
        "website_url": request.website_url.strip(),
        "description": request.description.strip(),
        "product_keywords": sorted(str(item).strip() for item in request.product_keywords if str(item).strip()),
        "target_customer_profile": request.target_customer_profile.strip(),
        "target_regions": sorted(str(item).strip() for item in request.target_regions if str(item).strip()),
        "uploaded_file_ids": sorted(str(item).strip() for item in request.uploaded_file_ids if str(item).strip()),
        "email_template_examples": [str(item).strip() for item in request.email_template_examples if str(item).strip()],
        "email_template_notes": request.email_template_notes.strip(),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_template_seed_cache() -> dict[str, Any]:
    path = Path(get_settings().template_seed_cache_path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[TemplateSeed] Failed to read cache, ignoring: %s", exc)
        return {}
    return data if isinstance(data, dict) else {}


def _save_template_seed_cache(cache: dict[str, Any]) -> None:
    path = Path(get_settings().template_seed_cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


async def _prepare_template_seed(request: TemplateSeedRequest) -> dict[str, Any]:
    cache_key = _template_seed_cache_key(request)
    cached = _load_template_seed_cache().get(cache_key)
    if isinstance(cached, dict):
        result = dict(cached)
        result["cache_status"] = "hit"
        return result

    uploaded_files = _validate_uploaded_file_ids(request.uploaded_file_ids)
    insight_state = {
        "website_url": request.website_url,
        "description": request.description,
        "product_keywords": list(request.product_keywords),
        "target_customer_profile": request.target_customer_profile,
        "target_regions": list(request.target_regions),
        "uploaded_files": uploaded_files,
        "target_lead_count": 1,
        "max_rounds": 1,
        "min_new_leads_threshold": 1,
        "enable_email_craft": True,
        "email_template_examples": list(request.email_template_examples),
        "email_template_notes": request.email_template_notes,
        "template_seed": None,
        "insight": None,
        "keywords": [],
        "used_keywords": [],
        "search_results": [],
        "seen_urls": [],
        "matched_platforms": [],
        "keyword_search_stats": {},
        "leads": [],
        "email_sequences": [],
        "hunt_round": 0,
        "prev_round_lead_count": 0,
        "round_feedback": None,
        "current_stage": "template_seed",
        "hunt_id": f"template-seed-{uuid.uuid4().hex[:8]}",
        "messages": [],
    }

    insight_payload: dict[str, Any] = {}
    try:
        insight_payload = await insight_node(insight_state)
    except Exception as exc:
        logger.warning("[TemplateSeed] Insight generation failed, using minimal fallback: %s", exc)
    insight = insight_payload.get("insight") if isinstance(insight_payload, dict) else None
    if not isinstance(insight, dict):
        insight = {
            "company_name": request.website_url or "Seller Company",
            "products": list(request.product_keywords),
            "industries": [request.target_customer_profile] if request.target_customer_profile else [],
            "value_propositions": [],
            "target_customer_profile": request.target_customer_profile,
            "summary": request.description,
        }

    synthetic_buyer = {
        "company_name": request.target_customer_profile or "Target Buyer",
        "industry": request.target_customer_profile or "Potential distributor or importer",
        "description": request.description or "Prospective buyer discovered by hunting workflow.",
        "website": "",
        "country_code": "",
    }
    llm = LLMTool(model_type="email", hunt_id="", agent="template_seed", hunt_round=0)
    try:
        template_profile = await extract_template_profile(
            llm,
            examples=list(request.email_template_examples),
            lead=synthetic_buyer,
            insight=insight,
            notes=request.email_template_notes,
        )
        template_plan = await compose_template_plan(
            llm,
            lead=synthetic_buyer,
            insight=insight,
            template_profile=template_profile,
            notes=request.email_template_notes,
        )
        prepared = {
            "source": "pre_generated",
            "prepared_from": {
                "website_url": request.website_url,
                "description": request.description,
                "product_keywords": list(request.product_keywords),
                "target_customer_profile": request.target_customer_profile,
                "target_regions": list(request.target_regions),
            },
            "synthetic_buyer": synthetic_buyer,
            "insight_snapshot": insight,
            "template_profile": template_profile,
            "template_plan": template_plan,
            "notes": request.email_template_notes,
        }
        cache = _load_template_seed_cache()
        cache[cache_key] = prepared
        _save_template_seed_cache(cache)
        prepared["cache_status"] = "miss"
        return prepared
    except Exception as exc:
        logger.warning("[TemplateSeed] Preparation failed, using fallback seed: %s", exc)
        fallback = _fallback_template_seed(request, insight)
        cache = _load_template_seed_cache()
        cache[cache_key] = fallback
        _save_template_seed_cache(cache)
        fallback["cache_status"] = "miss"
        return fallback
    finally:
        await llm.close()


def _sequence_is_send_approved(sequence: dict[str, Any]) -> bool:
    manual_review = sequence.get("manual_review")
    if isinstance(manual_review, dict):
        if manual_review.get("decision") == "approved":
            return True
        if manual_review.get("decision") == "rejected":
            return False
    if not bool(getattr(get_settings(), "email_require_approval_before_send", True)):
        return True
    return bool(sequence.get("auto_send_eligible"))


def _sequence_recipient(sequence: dict[str, Any]) -> str:
    target = sequence.get("target") or {}
    if isinstance(target, dict):
        target_email = _clean_email(str(target.get("target_email", "") or ""))
        if target_email:
            return target_email

    lead = sequence.get("lead") or {}
    if isinstance(lead, dict):
        for item in lead.get("emails", []) or []:
            recipient = _clean_email(str(item))
            if recipient:
                return recipient
    return ""


async def _scan_hunt_replies() -> None:
    settings = get_settings()
    if not bool(settings.email_reply_detection_enabled):
        return
    try:
        ensure_imap_tested(settings)
    except ValueError as exc:
        logger.debug("[ReplyDetection] Skipping automated reply scan because IMAP is not verified: %s", exc)
        return

    for hunt_id, hunt in list(_hunts.items()):
        result = hunt.get("result") or {}
        sequences = result.get("email_sequences", []) or []
        changed = False
        for sequence in sequences:
            if not isinstance(sequence, dict):
                continue
            lead = sequence.get("lead") or {}
            if not isinstance(lead, dict):
                continue
            recipient = _sequence_recipient(sequence)
            if not recipient:
                continue
            sent_any = any(
                isinstance(draft, dict) and str(draft.get("send_status", "") or "") == "sent"
                for draft in sequence.get("emails", []) or []
            )
            if not sent_any:
                continue

            previous_count = int(((sequence.get("reply_detection") or {}).get("reply_count", 0)) or 0)
            try:
                replies = await asyncio.to_thread(search_recent_replies, settings, from_address=recipient)
            except Exception as exc:
                logger.debug("[ReplyDetection] IMAP scan failed for %s: %s", recipient, exc)
                continue

            sequence["reply_detection"] = {
                "checked_at": now_iso(),
                "reply_count": len(replies),
                "replies": replies,
            }
            lead["reply_status"] = "replied" if replies else "no_reply"
            changed = True

            if len(replies) > previous_count:
                _broadcast(hunt_id, "email_reply_detected", {
                    "reply_count": len(replies),
                    "lead_company": lead.get("company_name", ""),
                    "recipient": recipient,
                })

        if changed:
            hunt["result"] = result
            save_hunt(hunt_id, hunt)


async def _reply_detection_loop() -> None:
    while True:
        settings = get_settings()
        interval = max(int(settings.email_reply_check_interval_seconds or 180), 30)
        try:
            await _scan_hunt_replies()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("[ReplyDetection] Loop error: %s", exc)
        await asyncio.sleep(interval)


def start_background_workers() -> None:
    global _reply_detection_task
    settings = get_settings()
    if bool(settings.email_reply_detection_enabled) and _reply_detection_task is None:
        _reply_detection_task = asyncio.create_task(_reply_detection_loop())


async def stop_background_workers() -> None:
    global _reply_detection_task
    if _reply_detection_task is not None:
        _reply_detection_task.cancel()
        try:
            await _reply_detection_task
        except asyncio.CancelledError:
            pass
        _reply_detection_task = None


def _broadcast_stage_data(hunt_id: str, completed_stage: str, state: dict) -> None:
    """Broadcast detail data for a stage that just completed."""
    payload: dict[str, Any] = {"stage": completed_stage}

    if completed_stage == "insight":
        insight = state.get("insight")
        if insight:
            payload["insight"] = insight

    elif completed_stage == "keyword_gen":
        payload["keywords"] = state.get("keywords", [])
        payload["hunt_round"] = state.get("hunt_round", 1)

    elif completed_stage == "search":
        results = state.get("search_results", [])
        payload["result_count"] = len(results)
        payload["keyword_search_stats"] = state.get("keyword_search_stats", {})
        payload["hunt_round"] = state.get("hunt_round", 1)

    elif completed_stage == "lead_extract":
        payload["leads_count"] = _unique_leads_count(state.get("leads", []))
        payload["hunt_round"] = state.get("hunt_round", 1)

    elif completed_stage == "evaluate":
        payload["round_feedback"] = state.get("round_feedback")
        payload["hunt_round"] = state.get("hunt_round", 1)

    elif completed_stage == "email_craft":
        payload["email_count"] = len(state.get("email_sequences", []))

    else:
        return  # unknown stage, skip

    # Save snapshot so new SSE connections can replay completed stage data
    if hunt_id in _hunts:
        snapshots = _hunts[hunt_id].setdefault("stage_snapshots", {})
        snapshots[completed_stage] = payload

    _broadcast(hunt_id, "stage_data", payload)


# ── Background task runner ──────────────────────────────────────────────

async def _run_hunt(hunt_id: str, request: HuntRequest) -> None:
    """Run the full hunt pipeline in the background."""
    _hunts[hunt_id]["status"] = "running"
    logger.info(
        "[Hunt %s] Starting — url=%s, files=%d, desc=%r, keywords=%s, profile=%s, regions=%s, email=%s",
        hunt_id[:8], request.website_url or "(none)",
        len(request.uploaded_file_ids),
        request.description[:60] if request.description else "",
        request.product_keywords, request.target_customer_profile,
        request.target_regions, request.enable_email_craft,
    )

    initial_state = {
        "website_url": request.website_url,
        "description": request.description,
        "product_keywords": request.product_keywords,
        "target_customer_profile": request.target_customer_profile,
        "target_regions": request.target_regions,
        "uploaded_files": list(request.uploaded_file_ids),
        "target_lead_count": request.target_lead_count,
        "max_rounds": request.max_rounds,
        "min_new_leads_threshold": request.min_new_leads_threshold,
        "enable_email_craft": request.enable_email_craft,
        "email_template_examples": list(request.email_template_examples),
        "email_template_notes": request.email_template_notes,
        "template_seed": request.template_seed or None,
        "insight": None,
        "keywords": [],
        "used_keywords": [],
        "search_results": [],
        "seen_urls": [],
        "matched_platforms": [],
        "keyword_search_stats": {},
        "leads": [],
        "email_sequences": [],
        "hunt_round": 1,
        "prev_round_lead_count": 0,
        "round_feedback": None,
        "current_stage": "start",
        "hunt_id": hunt_id,
        "messages": [],
    }

    # Wire per-URL progress callback → SSE broadcast + incremental disk save
    def _on_lead_progress(data: dict) -> None:
        _broadcast(hunt_id, "lead_progress", data)
        # Incrementally persist each lead as it's found — survives kill -9
        if data.get("event") == "lead_found" and data.get("lead"):
            hunt = _hunts.get(hunt_id)
            if hunt is not None:
                result = hunt.setdefault("result", {})
                leads = result.setdefault("leads", [])
                leads.append(data["lead"])
                hunt["leads_count"] = _unique_leads_count(leads)
                save_hunt(hunt_id, hunt)

    set_progress_callback(_on_lead_progress)

    try:
        _raise_if_hunt_cancelled(hunt_id)
        graph = build_graph(
            parse_description_node=parse_description_node,
            insight_node=insight_node,
            keyword_gen_node=keyword_gen_node,
            search_node=search_node,
            lead_extract_node=lead_extract_node,
            evaluate_node=evaluate_progress,
            should_continue_fn=should_continue_hunting,
            email_craft_node=email_craft_node,
        )

        # Use astream to get intermediate state updates and accumulate final result
        prev_stage = "start"
        prev_round = 1
        accumulated: dict[str, Any] = dict(initial_state)

        async for chunk in graph.astream(initial_state):
            _raise_if_hunt_cancelled(hunt_id)
            # chunk is {node_name: node_output_dict}
            for node_name, node_output in chunk.items():
                if node_name == "__end__":
                    continue

                # Merge node output into accumulated state
                accumulated.update(node_output)

                stage = node_output.get("current_stage", prev_stage)
                hunt_round = accumulated.get("hunt_round", prev_round)
                leads_count = _unique_leads_count(accumulated.get("leads", []))
                email_count = len(accumulated.get("email_sequences", []))

                # Update in-memory store
                _hunts[hunt_id].update({
                    "current_stage": stage,
                    "hunt_round": hunt_round,
                    "leads_count": leads_count,
                    "email_sequences_count": email_count,
                })

                # Broadcast stage change + stage-specific detail data
                if stage != prev_stage:
                    logger.info("[Hunt %s] Stage: %s → %s (round %d, leads %d)",
                                hunt_id[:8], prev_stage, stage, hunt_round, leads_count)
                    _broadcast(hunt_id, "stage_change", {
                        "stage": stage,
                        "hunt_round": hunt_round,
                        "leads_count": leads_count,
                    })

                    # Broadcast detail data for the stage that just completed
                    _broadcast_stage_data(hunt_id, prev_stage, accumulated)

                    # Checkpoint: persist accumulated state so kill -9 doesn't lose data
                    _hunts[hunt_id]["result"] = dict(accumulated)
                    save_hunt(hunt_id, _hunts[hunt_id])

                    prev_stage = stage

                # Broadcast round change
                if hunt_round != prev_round:
                    logger.info("[Hunt %s] Round %d → %d", hunt_id[:8], prev_round, hunt_round)
                    _broadcast(hunt_id, "round_change", {
                        "hunt_round": hunt_round,
                    })
                    prev_round = hunt_round

                # Broadcast progress
                _broadcast(hunt_id, "progress", {
                    "leads_count": leads_count,
                    "email_sequences_count": email_count,
                    "hunt_round": hunt_round,
                    "stage": stage,
                })
                _raise_if_hunt_cancelled(hunt_id)

        # Stream finished — accumulated has the full merged state
        cost_summary = get_tracker(hunt_id).to_summary()
        remove_tracker(hunt_id)
        accumulated["cost_summary"] = cost_summary

        _hunts[hunt_id].update({
            "status": "completed",
            "result": accumulated,
            "current_stage": accumulated.get("current_stage", "done"),
            "hunt_round": accumulated.get("hunt_round", 0),
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "email_sequences_count": len(accumulated.get("email_sequences", [])),
            "completed_at": now_iso(),
            "cost_summary": cost_summary,
        })
        save_hunt(hunt_id, _hunts[hunt_id])

        logger.info("[Hunt %s] Completed — %d leads, %d email sequences, %d rounds",
                    hunt_id[:8], _unique_leads_count(accumulated.get("leads", [])),
                    len(accumulated.get("email_sequences", [])),
                    accumulated.get("hunt_round", 0))

        _broadcast(hunt_id, "completed", {
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "email_sequences_count": len(accumulated.get("email_sequences", [])),
            "hunt_round": accumulated.get("hunt_round", 0),
        })

    except HuntCancelledError as e:
        logger.warning("[Hunt %s] Cancelled: %s", hunt_id[:8], e)
        cost_summary = get_tracker(hunt_id).to_summary()
        remove_tracker(hunt_id)
        accumulated["cost_summary"] = cost_summary
        _hunts[hunt_id].update({
            "status": "cancelled",
            "error": str(e),
            "completed_at": now_iso(),
            "cost_summary": cost_summary,
            "result": accumulated,
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "hunt_round": accumulated.get("hunt_round", 0),
        })
        save_hunt(hunt_id, _hunts[hunt_id])
        _broadcast(hunt_id, "failed", {"error": str(e)})
    except Exception as e:
        logger.error("[Hunt %s] Failed: %s", hunt_id[:8], e, exc_info=True)
        cost_summary = get_tracker(hunt_id).to_summary()
        remove_tracker(hunt_id)
        accumulated["cost_summary"] = cost_summary
        _hunts[hunt_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": now_iso(),
            "cost_summary": cost_summary,
            "result": accumulated,
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "hunt_round": accumulated.get("hunt_round", 0),
        })
        save_hunt(hunt_id, _hunts[hunt_id])
        _broadcast(hunt_id, "failed", {"error": str(e)})
    finally:
        set_progress_callback(None)


# ── State compression for resume ────────────────────────────────────────

# Max search_results rows kept in resumed state (older ones are dropped;
# URL dedup is handled by seen_urls which is always preserved).
_MAX_SEARCH_RESULTS_ON_RESUME = 50


def _slim_state(prior_result: dict, request: ResumeRequest) -> dict:
    """Build a slimmed initial state from a completed hunt's result.

    What is preserved:
    - insight          — skip re-running the expensive ReAct insight loop
    - leads            — all previously found leads (accumulated)
    - used_keywords    — full history for dedup in KeywordGenAgent
    - keyword_search_stats — per-keyword effectiveness history for feedback
    - seen_urls        — full URL dedup set (compact: just strings)
    - matched_platforms

    What is compressed / reset:
    - search_results   — trimmed to last N rows (URL dedup handled by seen_urls)
    - hunt_round       — reset to 1 for the new session
    - prev_round_lead_count — reset to current lead count (baseline for new session)
    - round_feedback   — cleared (fresh start)
    - keywords         — cleared
    - messages         — cleared (no value carrying old reasoning traces)
    - email_sequences  — cleared (will be regenerated if requested)
    """
    leads = prior_result.get("leads", [])

    # seen_urls: prefer explicit field; fall back to extracting from search_results
    seen_urls: list[str] = prior_result.get("seen_urls") or [
        r.get("link", "") for r in prior_result.get("search_results", []) if r.get("link")
    ]

    # Trim search_results to last N — URL dedup is handled by seen_urls
    search_results = prior_result.get("search_results", [])
    trimmed_results = search_results[-_MAX_SEARCH_RESULTS_ON_RESUME:]

    # Rebuild round_feedback from historical keyword_search_stats so KeywordGenAgent
    # knows which keyword patterns worked/failed in the prior session's last round.
    keyword_search_stats = prior_result.get("keyword_search_stats", {})
    used_keywords = prior_result.get("used_keywords", [])
    if keyword_search_stats:
        kw_performance = _build_keyword_performance(keyword_search_stats, leads)
        best_kw = [kp["keyword"] for kp in kw_performance if kp["effectiveness"] == "high"]
        worst_kw = [kp["keyword"] for kp in kw_performance if kp["effectiveness"] == "low"]
        resume_feedback: dict | None = {
            "round": "prior_session_summary",
            "total_leads": len(leads),
            "target": request.target_lead_count,
            "new_leads_this_round": 0,
            "keyword_performance": kw_performance,
            "best_keywords": best_kw,
            "worst_keywords": worst_kw,
            "keywords_used": used_keywords,
            "top_sources": [],
            "industry_distribution": {},
            "region_distribution": {},
        }
    else:
        resume_feedback = None

    return {
        # ── Preserved from prior hunt ──────────────────────────────────
        "website_url": prior_result.get("website_url", ""),
        "product_keywords": prior_result.get("product_keywords", []),
        "target_regions": prior_result.get("target_regions", []),
        "uploaded_files": prior_result.get("uploaded_files", []),
        "email_template_examples": list(request.email_template_examples) or prior_result.get("email_template_examples", []),
        "email_template_notes": request.email_template_notes or prior_result.get("email_template_notes", ""),
        "template_seed": request.template_seed or prior_result.get("template_seed"),
        "insight": prior_result.get("insight"),          # skip re-running insight
        "used_keywords": used_keywords,
        "keyword_search_stats": keyword_search_stats,
        "matched_platforms": prior_result.get("matched_platforms", []),
        "leads": leads,
        "seen_urls": seen_urls,                           # full URL dedup set
        "search_results": trimmed_results,               # trimmed, not full history
        # ── New session controls ───────────────────────────────────────
        "target_lead_count": request.target_lead_count,
        "max_rounds": request.max_rounds,
        "min_new_leads_threshold": request.min_new_leads_threshold,
        "enable_email_craft": request.enable_email_craft,
        "keywords": [],
        "email_sequences": [],
        "hunt_round": 1,
        "prev_round_lead_count": len(leads),             # baseline = prior lead count
        "round_feedback": resume_feedback,               # historical perf for KeywordGenAgent
        "current_stage": "start",
        "hunt_id": prior_result.get("hunt_id", ""),     # preserve hunt_id for cost tracking
        "messages": [],
    }


async def _run_resume_hunt(hunt_id: str, request: ResumeRequest, prior_result: dict) -> None:
    """Resume a completed hunt from its prior state."""
    _hunts[hunt_id]["status"] = "running"
    logger.info(
        "[Hunt %s] Resuming — prior_leads=%d, new_target=%d, max_rounds=%d",
        hunt_id[:8],
        len(prior_result.get("leads", [])),
        request.target_lead_count,
        request.max_rounds,
    )

    initial_state = _slim_state(prior_result, request)

    def _on_lead_progress(data: dict) -> None:
        _broadcast(hunt_id, "lead_progress", data)
        # Incrementally persist each lead as it's found — survives kill -9
        if data.get("event") == "lead_found" and data.get("lead"):
            hunt = _hunts.get(hunt_id)
            if hunt is not None:
                result = hunt.setdefault("result", {})
                leads = result.setdefault("leads", [])
                leads.append(data["lead"])
                hunt["leads_count"] = _unique_leads_count(leads)
                save_hunt(hunt_id, hunt)

    set_progress_callback(_on_lead_progress)

    try:
        _raise_if_hunt_cancelled(hunt_id)
        graph = build_graph(
            parse_description_node=parse_description_node,
            insight_node=insight_node,
            keyword_gen_node=keyword_gen_node,
            search_node=search_node,
            lead_extract_node=lead_extract_node,
            evaluate_node=evaluate_progress,
            should_continue_fn=should_continue_hunting,
            email_craft_node=email_craft_node,
        )

        prev_stage = "start"
        prev_round = 1
        accumulated: dict[str, Any] = dict(initial_state)

        async for chunk in graph.astream(initial_state):
            _raise_if_hunt_cancelled(hunt_id)
            for node_name, node_output in chunk.items():
                if node_name == "__end__":
                    continue

                accumulated.update(node_output)

                stage = node_output.get("current_stage", prev_stage)
                hunt_round = accumulated.get("hunt_round", prev_round)
                leads_count = _unique_leads_count(accumulated.get("leads", []))
                email_count = len(accumulated.get("email_sequences", []))

                _hunts[hunt_id].update({
                    "current_stage": stage,
                    "hunt_round": hunt_round,
                    "leads_count": leads_count,
                    "email_sequences_count": email_count,
                })

                if stage != prev_stage:
                    logger.info(
                        "[Hunt %s] Stage: %s → %s (round %d, leads %d)",
                        hunt_id[:8], prev_stage, stage, hunt_round, leads_count,
                    )
                    _broadcast(hunt_id, "stage_change", {
                        "stage": stage,
                        "hunt_round": hunt_round,
                        "leads_count": leads_count,
                    })
                    _broadcast_stage_data(hunt_id, prev_stage, accumulated)

                    # Checkpoint: persist accumulated state so kill -9 doesn't lose data
                    _hunts[hunt_id]["result"] = dict(accumulated)
                    save_hunt(hunt_id, _hunts[hunt_id])

                    prev_stage = stage

                if hunt_round != prev_round:
                    _broadcast(hunt_id, "round_change", {"hunt_round": hunt_round})
                    prev_round = hunt_round

                _broadcast(hunt_id, "progress", {
                    "leads_count": leads_count,
                    "email_sequences_count": email_count,
                    "hunt_round": hunt_round,
                    "stage": stage,
                })
                _raise_if_hunt_cancelled(hunt_id)

        _hunts[hunt_id].update({
            "status": "completed",
            "result": accumulated,
            "current_stage": accumulated.get("current_stage", "done"),
            "hunt_round": accumulated.get("hunt_round", 0),
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "email_sequences_count": len(accumulated.get("email_sequences", [])),
            "completed_at": now_iso(),
        })
        save_hunt(hunt_id, _hunts[hunt_id])

        logger.info(
            "[Hunt %s] Resume completed — %d leads, %d rounds",
            hunt_id[:8],
            _unique_leads_count(accumulated.get("leads", [])),
            accumulated.get("hunt_round", 0),
        )
        _broadcast(hunt_id, "completed", {
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "email_sequences_count": len(accumulated.get("email_sequences", [])),
            "hunt_round": accumulated.get("hunt_round", 0),
        })

    except HuntCancelledError as e:
        logger.warning("[Hunt %s] Resume cancelled: %s", hunt_id[:8], e)
        cost_summary = get_tracker(hunt_id).to_summary()
        remove_tracker(hunt_id)
        accumulated["cost_summary"] = cost_summary
        _hunts[hunt_id].update({
            "status": "cancelled",
            "error": str(e),
            "completed_at": now_iso(),
            "cost_summary": cost_summary,
            "result": accumulated,
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "hunt_round": accumulated.get("hunt_round", 0),
        })
        save_hunt(hunt_id, _hunts[hunt_id])
        _broadcast(hunt_id, "failed", {"error": str(e)})
    except Exception as e:
        logger.error("[Hunt %s] Resume failed: %s", hunt_id[:8], e, exc_info=True)
        cost_summary = get_tracker(hunt_id).to_summary()
        remove_tracker(hunt_id)
        accumulated["cost_summary"] = cost_summary
        _hunts[hunt_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": now_iso(),
            "cost_summary": cost_summary,
            "result": accumulated,
            "leads_count": _unique_leads_count(accumulated.get("leads", [])),
            "hunt_round": accumulated.get("hunt_round", 0),
        })
        save_hunt(hunt_id, _hunts[hunt_id])
        _broadcast(hunt_id, "failed", {"error": str(e)})
    finally:
        set_progress_callback(None)


# ── Routes ────────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ai-hunter"}


@router.post("/upload", dependencies=[Depends(require_api_access)])
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload one or more files (txt, md, pdf, docx, xlsx, csv) for use as insight source.

    Returns a list of server-side file paths to pass as uploaded_file_ids in HuntRequest.
    """
    settings = get_settings()
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    max_file_bytes = settings.max_upload_size_mb * 1024 * 1024

    _ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".json"}
    results = []

    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not supported. Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
            )
        unique_name = f"{uuid.uuid4()}{ext}"
        dest = os.path.join(upload_dir, unique_name)
        written = 0
        try:
            with open(dest, "wb") as f:
                while True:
                    chunk = file.file.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_file_bytes:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File '{file.filename}' exceeds the {settings.max_upload_size_mb} MB limit.",
                        )
                    f.write(chunk)
        except Exception:
            if os.path.exists(dest):
                os.remove(dest)
            raise
        results.append({"original_name": file.filename, "file_id": str(Path(dest).resolve())})
        logger.info("[Upload] Saved %s → %s", file.filename, dest)

    return {"uploaded": results}


@router.post("/email-template-seeds/prepare", response_model=TemplateSeedResponse, dependencies=[Depends(require_api_access)])
async def prepare_email_template_seed(request: TemplateSeedRequest):
    return TemplateSeedResponse(template_seed=await _prepare_template_seed(request))


@router.post("/hunts", response_model=HuntResponse, dependencies=[Depends(require_api_access)])
async def create_hunt(request: HuntRequest, background_tasks: BackgroundTasks):
    """Start a new hunt pipeline in the background.

    Returns a hunt_id to track progress.
    """
    uploaded_file_ids = _validate_uploaded_file_ids(request.uploaded_file_ids)
    hunt_id = str(uuid.uuid4())
    _hunts[hunt_id] = {
        "status": "pending",
        "result": None,
        "current_stage": None,
        "hunt_round": 0,
        "leads_count": 0,
        "email_sequences_count": 0,
        "error": None,
        "created_at": now_iso(),
        "website_url": request.website_url,
        "product_keywords": request.product_keywords,
        "target_customer_profile": request.target_customer_profile,
        "target_regions": request.target_regions,
        "email_template_examples": request.email_template_examples,
        "email_template_notes": request.email_template_notes,
    }
    save_hunt(hunt_id, _hunts[hunt_id])

    request = request.model_copy(
        update={
            "uploaded_file_ids": uploaded_file_ids,
            "enable_email_craft": request.enable_email_craft,
        }
    )
    background_tasks.add_task(_run_hunt, hunt_id, request)

    return HuntResponse(hunt_id=hunt_id, status="pending")


@router.get("/hunts/{hunt_id}/status", response_model=HuntStatus, dependencies=[Depends(require_api_access)])
async def get_hunt_status(hunt_id: str):
    """Get the current status of a hunt."""
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = _hunts[hunt_id]
    result = hunt.get("result") or {}
    return HuntStatus(
        hunt_id=hunt_id,
        status=hunt["status"],
        current_stage=hunt.get("current_stage"),
        hunt_round=hunt.get("hunt_round", 0),
        leads_count=_unique_leads_count(result.get("leads", [])),
        email_sequences_count=hunt.get("email_sequences_count", 0),
        error=hunt.get("error"),
    )


@router.get("/hunts/{hunt_id}/result", response_model=HuntResult, dependencies=[Depends(require_api_access)])
async def get_hunt_result(hunt_id: str):
    """Get the full result of a hunt (partial data returned for running/pending hunts)."""
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = _hunts[hunt_id]
    result = hunt.get("result") or {}
    deduped_leads = _dedupe_leads(result.get("leads", []))
    return HuntResult(
        hunt_id=hunt_id,
        status=hunt["status"],
        insight=result.get("insight"),
        leads=deduped_leads,
        email_sequences=result.get("email_sequences", []),
        used_keywords=result.get("used_keywords", []),
        hunt_round=result.get("hunt_round", 0),
        round_feedback=result.get("round_feedback"),
        keyword_search_stats=result.get("keyword_search_stats", {}),
        search_result_count=len(result.get("search_results", [])),
    )

@router.post(
    "/hunts/{hunt_id}/email-sequences/{sequence_index}/decision",
    response_model=EmailSequenceDecisionResponse,
    dependencies=[Depends(require_api_access)],
)
async def decide_email_sequence(
    hunt_id: str,
    sequence_index: int,
    request: EmailSequenceDecisionRequest,
):
    """Persist a manual approval or rejection for a generated email sequence."""
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = _hunts[hunt_id]
    result = hunt.get("result") or {}
    sequences = result.get("email_sequences", [])
    if not isinstance(sequences, list):
        raise HTTPException(status_code=422, detail="Hunt has no email sequence data")
    if sequence_index < 0 or sequence_index >= len(sequences):
        raise HTTPException(status_code=404, detail="Email sequence not found")

    sequence = sequences[sequence_index]
    if not isinstance(sequence, dict):
        raise HTTPException(status_code=422, detail="Email sequence payload is invalid")

    manual_review = {
        "decision": request.decision,
        "notes": request.notes,
        "updated_at": now_iso(),
    }
    sequence["manual_review"] = manual_review
    sequence["auto_send_eligible"] = request.decision == "approved"

    hunt["result"] = result
    hunt["email_sequences_count"] = len(sequences)
    save_hunt(hunt_id, hunt)

    return EmailSequenceDecisionResponse(
        hunt_id=hunt_id,
        sequence_index=sequence_index,
        decision=request.decision,
        auto_send_eligible=bool(sequence["auto_send_eligible"]),
        manual_review=manual_review,
    )


@router.post(
    "/hunts/{hunt_id}/email-sequences/{sequence_index}/send",
    response_model=SendEmailDraftResponse,
    dependencies=[Depends(require_api_access)],
)
async def send_email_sequence_draft(
    hunt_id: str,
    sequence_index: int,
    request: SendEmailDraftRequest,
):
    """Send a specific draft from an approved email sequence via SMTP."""
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = _hunts[hunt_id]
    result = hunt.get("result") or {}
    sequences = result.get("email_sequences", [])
    if not isinstance(sequences, list):
        raise HTTPException(status_code=422, detail="Hunt has no email sequence data")
    if sequence_index < 0 or sequence_index >= len(sequences):
        raise HTTPException(status_code=404, detail="Email sequence not found")

    sequence = sequences[sequence_index]
    if not isinstance(sequence, dict):
        raise HTTPException(status_code=422, detail="Email sequence payload is invalid")
    if not _sequence_is_send_approved(sequence):
        raise HTTPException(status_code=409, detail="Email sequence must be approved before sending")

    recipient = _sequence_recipient(sequence)
    if not recipient:
        raise HTTPException(status_code=422, detail="No recipient email found on this lead")

    draft = None
    for item in sequence.get("emails", []):
        if isinstance(item, dict) and int(item.get("sequence_number", 0) or 0) == request.sequence_number:
            draft = item
            break
    if not draft:
        raise HTTPException(status_code=404, detail="Requested draft not found")

    settings = get_settings()
    try:
        ensure_smtp_ready(settings)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    try:
        send_result = await asyncio.to_thread(
            send_smtp_email,
            settings,
            to_address=recipient,
            subject=str(draft.get("subject", "") or ""),
            body_text=str(draft.get("body_text", "") or ""),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    draft["send_status"] = "sent"
    draft["sent_at"] = now_iso()
    draft["sent_to"] = recipient
    hunt["result"] = result
    save_hunt(hunt_id, hunt)

    return SendEmailDraftResponse(
        hunt_id=hunt_id,
        sequence_index=sequence_index,
        sequence_number=request.sequence_number,
        sent_to=recipient,
        subject=str(draft.get("subject", "") or ""),
        status=send_result["status"],
    )


@router.post(
    "/hunts/{hunt_id}/email-sequences/{sequence_index}/detect-replies",
    response_model=DetectReplyResponse,
    dependencies=[Depends(require_api_access)],
)
async def detect_email_sequence_replies(
    hunt_id: str,
    sequence_index: int,
):
    """Check IMAP inbox for replies from the lead's email address."""
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = _hunts[hunt_id]
    result = hunt.get("result") or {}
    sequences = result.get("email_sequences", [])
    if not isinstance(sequences, list) or sequence_index < 0 or sequence_index >= len(sequences):
        raise HTTPException(status_code=404, detail="Email sequence not found")

    sequence = sequences[sequence_index]
    if not isinstance(sequence, dict):
        raise HTTPException(status_code=422, detail="Email sequence payload is invalid")

    lead = sequence.get("lead") or {}
    recipient = _sequence_recipient(sequence)
    if not recipient:
        raise HTTPException(status_code=422, detail="No recipient email found on this lead")

    settings = get_settings()
    try:
        ensure_imap_ready(settings)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    try:
        replies = await asyncio.to_thread(search_recent_replies, settings, from_address=recipient)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sequence["reply_detection"] = {
        "checked_at": now_iso(),
        "reply_count": len(replies),
        "replies": replies,
    }
    if isinstance(lead, dict):
        lead["reply_status"] = "replied" if replies else "no_reply"
    hunt["result"] = result
    save_hunt(hunt_id, hunt)

    return DetectReplyResponse(
        hunt_id=hunt_id,
        sequence_index=sequence_index,
        reply_count=len(replies),
        replies=replies,
    )


@router.get("/hunts", dependencies=[Depends(require_api_access)])
async def list_hunts():
    """List all hunts with their status."""
    items = []
    for hid, h in _hunts.items():
        result = h.get("result") or {}
        items.append({
            "hunt_id": hid,
            "status": h["status"],
            "leads_count": _unique_leads_count(result.get("leads", [])),
            "created_at": h.get("created_at", ""),
            "website_url": h.get("website_url", ""),
            "product_keywords": h.get("product_keywords", []),
            "target_customer_profile": h.get("target_customer_profile", ""),
            "target_regions": h.get("target_regions", []),
            "hunt_round": h.get("hunt_round", 0),
            "email_sequences_count": h.get("email_sequences_count", 0),
        })
    # Sort by created_at descending (newest first)
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


@router.get("/hunts/{hunt_id}/cost", dependencies=[Depends(require_api_access)])
async def get_hunt_cost(hunt_id: str):
    """Get cost and token usage summary for a hunt.

    Returns live stats for running hunts (from in-memory tracker)
    and persisted stats for completed/failed hunts (from result).
    """
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = _hunts[hunt_id]
    status = hunt["status"]

    # For running hunts: read live from tracker
    if status in ("running", "pending"):
        try:
            summary = get_tracker(hunt_id).to_summary()
        except Exception:
            summary = {}
        return {"hunt_id": hunt_id, "status": status, "cost_summary": summary}

    # For completed/failed: read from persisted result
    cost_summary = hunt.get("cost_summary") or (hunt.get("result") or {}).get("cost_summary") or {}
    return {"hunt_id": hunt_id, "status": status, "cost_summary": cost_summary}


@router.post("/hunts/{hunt_id}/resume", response_model=HuntResponse, dependencies=[Depends(require_api_access)])
async def resume_hunt(hunt_id: str, request: ResumeRequest, background_tasks: BackgroundTasks):
    """Resume a completed hunt, continuing from where it left off.

    Preserves: insight, leads, used_keywords, keyword_search_stats, seen_urls.
    Resets:    hunt_round, round_feedback, keywords, email_sequences, messages.
    Compresses: search_results trimmed to last 50 rows (URL dedup via seen_urls).

    Allows raising target_lead_count and max_rounds to mine deeper.
    Both completed and failed hunts can be resumed (not running or pending).
    """
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = _hunts[hunt_id]
    if hunt["status"] == "running":
        raise HTTPException(status_code=409, detail="Hunt is already running")
    if hunt["status"] == "pending":
        raise HTTPException(status_code=409, detail="Hunt has not started yet")

    prior_result = hunt.get("result") or {}
    if not prior_result:
        raise HTTPException(status_code=422, detail="Hunt has no result state to resume from")

    # Inject original hunt metadata into prior_result so _slim_state can access it
    for field in ("website_url", "product_keywords", "target_customer_profile", "target_regions", "uploaded_files", "email_template_examples", "email_template_notes"):
        if field not in prior_result:
            prior_result[field] = hunt.get(field, [] if field != "website_url" else "")

    _hunts[hunt_id].update({
        "status": "pending",
        "error": None,
        "current_stage": None,
        "hunt_round": 0,
        "leads_count": _unique_leads_count(prior_result.get("leads", [])),
        "resumed_at": now_iso(),
    })
    save_hunt(hunt_id, _hunts[hunt_id])

    request = request.model_copy(
        update={"enable_email_craft": request.enable_email_craft}
    )
    background_tasks.add_task(_run_resume_hunt, hunt_id, request, prior_result)

    return HuntResponse(hunt_id=hunt_id, status="pending")
