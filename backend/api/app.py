"""FastAPI application — main entry point for the AI Hunter API."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import socket
from argparse import Namespace
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.automation_routes import router as automation_router
from api.hunt_store import load_all_hunts
from api.email_routes import router as email_router
from api.routes import router, start_background_workers, stop_background_workers, request_hunt_cancel
from api.settings_routes import router as settings_router
from api.sse import sse_router
from automation.job_queue import HuntJobQueue
from automation.metrics import collect_automation_metrics, collect_automation_status
from automation.notifier import (
    render_alert_text,
    render_discovery_batch_text,
    render_send_batch_text,
    render_summary_text,
    send_feishu_text,
)
from automation.runtime import update_worker_state
from config.settings import get_settings
from emailing.readiness import ensure_imap_tested, ensure_smtp_tested
from emailing.reply_detector import run_reply_detection_once
from emailing.scheduler import run_scheduler_once
from emailing.store import EmailStore
from scripts.headless_worker import JobCancelledError, run_hunt_payload

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

# Suppress noisy LiteLLM logs (they spam "completion() model=..." on every call)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("LiteLLM Proxy").setLevel(logging.WARNING)
logging.getLogger("LiteLLM Router").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

import litellm  # noqa: E402
litellm.suppress_debug_info = True
litellm.set_verbose = False


logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _automation_worker_id() -> str:
    return f"{socket.gethostname()}:embedded-consumer"


def _extract_hunt_id_from_error(message: str) -> str:
    match = re.search(r"hunt\s+([^\s:]+)\s+failed:", str(message or ""))
    return str(match.group(1)) if match else ""


def _embedded_consumer_enabled(settings) -> bool:
    # TestClient/pytest should not mutate the operator's real queue DB.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    return bool(getattr(settings, "automation_embedded_consumer_enabled", True))


async def _run_automation_consumer_once() -> bool:
    settings = get_settings()
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    update_worker_state(
        "consumer",
        enabled=_embedded_consumer_enabled(settings),
        running=True,
        worker_id=_automation_worker_id(),
        last_poll_at=_now_iso(),
    )
    job = queue.claim_next(worker_id=_automation_worker_id(), now_iso=_now_iso())
    if not job:
        return False

    job_id = str(job["id"])
    update_worker_state(
        "consumer",
        active_job_id=job_id,
        last_claimed_job_id=job_id,
        last_activity_at=_now_iso(),
        last_error="",
    )
    logger.info("[AutomationConsumer] claimed job=%s", job_id[:8])
    queue.update_progress(
        job_id,
        updated_at=_now_iso(),
        progress_stage="claimed",
        progress_message="Embedded consumer claimed this queue job",
    )

    host = settings.api_host.strip() or "127.0.0.1"
    if host == "0.0.0.0":
        host = "127.0.0.1"
    consumer_args = Namespace(
        api_base_url=f"http://{host}:{settings.api_port}",
        api_token=settings.api_access_token,
        auto_start_campaign=bool(settings.automation_consumer_auto_start_campaign),
        campaign_name_prefix="Auto Campaign",
        status_poll_seconds=int(settings.automation_consumer_status_poll_seconds),
        request_timeout_seconds=int(settings.automation_consumer_request_timeout_seconds),
    )
    consumer_args.progress_callback = lambda stage, message, **extra: queue.update_progress(
        job_id,
        updated_at=_now_iso(),
        progress_stage=str(stage or ""),
        progress_message=str(message or ""),
        hunt_id=str(extra.get("hunt_id", "") or ""),
        template_seed_status=extra.get("template_seed_status"),
        template_seed_source=extra.get("template_seed_source"),
    )
    consumer_args.cancel_check = lambda: queue.is_cancellation_requested(job_id)

    try:
        result = await asyncio.to_thread(run_hunt_payload, consumer_args, job.get("payload") or {})
        queue.mark_completed(job_id, hunt_id=str(result["hunt_id"]), finished_at=_now_iso())
        update_worker_state(
            "consumer",
            active_job_id="",
            last_completed_job_id=job_id,
            last_activity_at=_now_iso(),
            last_error="",
        )
        logger.info("[AutomationConsumer] completed job=%s hunt=%s", job_id[:8], str(result['hunt_id'])[:8])
    except JobCancelledError as exc:
        latest_job = queue.get(job_id) or {}
        hunt_id = str(latest_job.get("last_hunt_id", "") or job.get("last_hunt_id", "") or "")
        if hunt_id:
            request_hunt_cancel(hunt_id, reason=str(exc))
        update_worker_state(
            "consumer",
            active_job_id="",
            last_activity_at=_now_iso(),
            last_error=str(exc),
        )
        logger.warning("[AutomationConsumer] job=%s cancelled: %s", job_id[:8], exc)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        available_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=max(1, int(settings.automation_consumer_retry_delay_seconds)))
        ).isoformat()
        queue.requeue(
            job_id,
            available_at=available_at,
            error_message=str(exc),
            updated_at=_now_iso(),
            hunt_id=_extract_hunt_id_from_error(str(exc)),
        )
        update_worker_state(
            "consumer",
            active_job_id="",
            last_activity_at=_now_iso(),
            last_error=str(exc),
        )
        logger.exception("[AutomationConsumer] job=%s failed and was requeued: %s", job_id[:8], exc)
    return True


async def _automation_consumer_loop() -> None:
    while True:
        try:
            settings = get_settings()
            if not _embedded_consumer_enabled(settings):
                update_worker_state(
                    "consumer",
                    enabled=False,
                    running=False,
                    active_job_id="",
                    last_poll_at=_now_iso(),
                )
                await asyncio.sleep(5)
                continue
            update_worker_state("consumer", enabled=True, running=True, worker_id=_automation_worker_id())
            did_work = await _run_automation_consumer_once()
            if did_work:
                continue
        except asyncio.CancelledError:
            raise
        except Exception:
            update_worker_state("consumer", last_error="polling iteration failed", last_activity_at=_now_iso())
            logger.exception("[AutomationConsumer] polling iteration failed")
        await asyncio.sleep(max(1, int(get_settings().automation_consumer_poll_seconds)))


async def _email_scheduler_loop() -> None:
    """Poll pending email jobs and dispatch due messages."""
    while True:
        try:
            settings = get_settings()
            if not bool(settings.email_auto_send_enabled):
                await asyncio.sleep(60)
                continue
            ensure_smtp_tested(settings)
            store = EmailStore(settings.email_db_path)
            store.init_db()
            result = await run_scheduler_once(store)
            if result["sent"] or result["failed"]:
                logger.info("[EmailScheduler] sent=%s failed=%s skipped=%s", result["sent"], result["failed"], result["skipped"])
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[EmailScheduler] polling iteration failed")
        await asyncio.sleep(60)


async def _email_reply_loop() -> None:
    """Poll inbox for replies and stop follow-up sequences."""
    while True:
        try:
            settings = get_settings()
            if not bool(settings.email_reply_detection_enabled):
                await asyncio.sleep(max(30, int(settings.email_reply_check_interval_seconds)))
                continue
            ensure_imap_tested(settings)
            store = EmailStore(settings.email_db_path)
            store.init_db()
            account = store.get_account("default")
            if account:
                result = await run_reply_detection_once(store, account)
                if result["matched"]:
                    logger.info("[EmailReply] checked=%s matched=%s skipped=%s", result["checked"], result["matched"], result["skipped"])
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[EmailReply] polling iteration failed")
        await asyncio.sleep(max(30, int(settings.email_reply_check_interval_seconds)))


async def _automation_notify_loop() -> None:
    last_summary_at = 0.0
    last_alert_at = 0.0
    discovery_buffer: list[dict[str, str | int]] = []
    send_buffer: list[dict[str, str]] = []
    seen_hunt_ids: set[str] = set()
    seen_sent_message_ids: set[str] = set()
    primed = False
    last_discovery_flush_at = 0.0
    last_send_flush_at = 0.0
    loop = asyncio.get_running_loop()
    while True:
        try:
            settings = get_settings()
            webhook_url = str(settings.automation_feishu_webhook_url or "").strip()
            if not webhook_url:
                await asyncio.sleep(60)
                continue

            now_monotonic = loop.time()
            if bool(getattr(settings, "automation_event_notifications_enabled", True)):
                batch_flush_interval = max(60, int(getattr(settings, "automation_event_flush_interval_seconds", 600) or 600))
                discovery_batch_size = max(1, int(getattr(settings, "automation_discovery_batch_size", 5) or 5))
                send_batch_size = max(1, int(getattr(settings, "automation_send_batch_size", 10) or 10))

                hunts = load_all_hunts()
                store = EmailStore(settings.email_db_path)
                store.init_db()
                if not primed:
                    seen_hunt_ids.update(
                        hunt_id for hunt_id, hunt in hunts.items()
                        if str(hunt.get("status", "") or "") == "completed"
                    )
                    seen_sent_message_ids.update(
                        str(item.get("id", "") or "")
                        for item in store.list_sent_messages_since(since_iso="1970-01-01T00:00:00+00:00", limit=5000)
                        if str(item.get("id", "") or "")
                    )
                    primed = True
                    last_discovery_flush_at = now_monotonic
                    last_send_flush_at = now_monotonic

                for hunt_id, hunt in hunts.items():
                    if hunt_id in seen_hunt_ids:
                        continue
                    if str(hunt.get("status", "") or "") != "completed":
                        continue
                    seen_hunt_ids.add(hunt_id)
                    result = hunt.get("result") or {}
                    for lead in result.get("leads", []) or []:
                        if not isinstance(lead, dict):
                            continue
                        emails = lead.get("emails", []) or []
                        discovery_buffer.append({
                            "company_name": str(lead.get("company_name", "") or ""),
                            "website": str(lead.get("website", "") or ""),
                            "email_count": len(emails) if isinstance(emails, list) else 0,
                        })

                for item in store.list_sent_messages_since(since_iso="1970-01-01T00:00:00+00:00", limit=500):
                    message_id = str(item.get("id", "") or "")
                    if not message_id or message_id in seen_sent_message_ids:
                        continue
                    seen_sent_message_ids.add(message_id)
                    send_buffer.append({
                        "company_name": str(item.get("lead_name", "") or ""),
                        "lead_email": str(item.get("lead_email", "") or ""),
                        "subject": str(item.get("subject", "") or ""),
                    })

                if discovery_buffer and (
                    len(discovery_buffer) >= discovery_batch_size
                    or now_monotonic - last_discovery_flush_at >= batch_flush_interval
                ):
                    text = render_discovery_batch_text(discovery_buffer[:])
                    await asyncio.to_thread(send_feishu_text, webhook_url, text)
                    discovery_buffer.clear()
                    last_discovery_flush_at = now_monotonic
                    logger.info("[AutomationNotify] discovery batch sent")

                if send_buffer and (
                    len(send_buffer) >= send_batch_size
                    or now_monotonic - last_send_flush_at >= batch_flush_interval
                ):
                    text = render_send_batch_text(send_buffer[:])
                    await asyncio.to_thread(send_feishu_text, webhook_url, text)
                    send_buffer.clear()
                    last_send_flush_at = now_monotonic
                    logger.info("[AutomationNotify] send batch sent")

            if bool(settings.automation_summary_enabled):
                interval = max(300, int(settings.automation_summary_interval_seconds or 7200))
                if now_monotonic - last_summary_at >= interval:
                    status = collect_automation_status()
                    metrics = collect_automation_metrics(hours=max(1, interval // 3600))
                    metrics["status_snapshot"] = status
                    text = render_summary_text(metrics)
                    await asyncio.to_thread(send_feishu_text, webhook_url, text)
                    last_summary_at = now_monotonic
                    logger.info("[AutomationNotify] summary sent")

            if bool(settings.automation_alerts_enabled):
                alert_interval = max(300, int(settings.automation_alert_interval_seconds or 1800))
                if now_monotonic - last_alert_at >= alert_interval:
                    status = collect_automation_status()
                    metrics = collect_automation_metrics(hours=2)
                    should_alert = (
                        status["hunt_jobs"]["queued"] >= int(settings.automation_alert_backlog_threshold or 20)
                        or status["email_queue"]["pending"] >= int(settings.automation_alert_backlog_threshold or 20)
                        or metrics["emails"]["failed"] >= int(settings.automation_alert_failed_messages_threshold or 10)
                    )
                    if should_alert:
                        text = render_alert_text(status, metrics)
                        await asyncio.to_thread(send_feishu_text, webhook_url, text)
                        logger.warning("[AutomationNotify] alert sent")
                    last_alert_at = now_monotonic
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[AutomationNotify] loop failed")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    settings = get_settings()
    app.state.settings = settings
    app.state.email_scheduler_task = None
    app.state.email_reply_task = None
    app.state.automation_notify_task = None
    app.state.automation_consumer_task = None
    queue = HuntJobQueue(settings.automation_queue_db_path)
    queue.init_db()
    recovered_jobs = queue.recover_interrupted_running_jobs(updated_at=_now_iso())
    if recovered_jobs:
        logger.warning("[AutomationConsumer] recovered %s interrupted running job(s) after startup", recovered_jobs)

    # Enable Langfuse tracing if configured
    from observability.setup import setup_observability
    setup_observability()

    app.state.email_scheduler_task = asyncio.create_task(_email_scheduler_loop())
    logger.info("[EmailScheduler] background loop started")
    app.state.email_reply_task = asyncio.create_task(_email_reply_loop())
    logger.info("[EmailReply] background loop started")
    app.state.automation_notify_task = asyncio.create_task(_automation_notify_loop())
    logger.info("[AutomationNotify] background loop started")
    app.state.automation_consumer_task = asyncio.create_task(_automation_consumer_loop())
    logger.info("[AutomationConsumer] background loop started")
    update_worker_state("consumer", enabled=_embedded_consumer_enabled(settings), running=True, worker_id=_automation_worker_id())

    start_background_workers()

    try:
        yield
    finally:
        task = getattr(app.state, "email_scheduler_task", None)
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            logger.info("[EmailScheduler] background loop stopped")
        reply_task = getattr(app.state, "email_reply_task", None)
        if reply_task:
            reply_task.cancel()
            with suppress(asyncio.CancelledError):
                await reply_task
            logger.info("[EmailReply] background loop stopped")
        notify_task = getattr(app.state, "automation_notify_task", None)
        if notify_task:
            notify_task.cancel()
            with suppress(asyncio.CancelledError):
                await notify_task
            logger.info("[AutomationNotify] background loop stopped")
        consumer_task = getattr(app.state, "automation_consumer_task", None)
        if consumer_task:
            consumer_task.cancel()
            with suppress(asyncio.CancelledError):
                await consumer_task
            logger.info("[AutomationConsumer] background loop stopped")
        update_worker_state("consumer", running=False, active_job_id="")

    await stop_background_workers()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Hunter API",
        description="Multi-agent B2B lead hunting pipeline",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")
    app.include_router(automation_router)
    app.include_router(email_router)
    app.include_router(sse_router, prefix="/api/v1")
    if settings.settings_api_enabled:
        app.include_router(settings_router)

    return app


app = create_app()
