"""FastAPI application — main entry point for the AI Hunter API."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.automation_routes import router as automation_router
from api.email_routes import router as email_router
from api.routes import router, start_background_workers, stop_background_workers
from api.settings_routes import router as settings_router
from api.sse import sse_router
from automation.metrics import collect_automation_metrics, collect_automation_status
from automation.notifier import render_alert_text, render_summary_text, send_feishu_text
from config.settings import get_settings
from emailing.readiness import ensure_imap_tested, ensure_smtp_tested
from emailing.reply_detector import run_reply_detection_once
from emailing.scheduler import run_scheduler_once
from emailing.store import EmailStore

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
    loop = asyncio.get_running_loop()
    while True:
        try:
            settings = get_settings()
            webhook_url = str(settings.automation_feishu_webhook_url or "").strip()
            if not webhook_url:
                await asyncio.sleep(60)
                continue

            now_monotonic = loop.time()
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

    # Enable Langfuse tracing if configured
    from observability.setup import setup_observability
    setup_observability()

    app.state.email_scheduler_task = asyncio.create_task(_email_scheduler_loop())
    logger.info("[EmailScheduler] background loop started")
    app.state.email_reply_task = asyncio.create_task(_email_reply_loop())
    logger.info("[EmailReply] background loop started")
    app.state.automation_notify_task = asyncio.create_task(_automation_notify_loop())
    logger.info("[AutomationNotify] background loop started")

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
