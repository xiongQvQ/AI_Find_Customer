"""FastAPI application — main entry point for the AI Hunter API."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.email_routes import router as email_router
from api.routes import router, start_background_workers, stop_background_workers
from api.settings_routes import router as settings_router
from api.sse import sse_router
from config.settings import get_settings
from emailing.reply_detector import run_reply_detection_once
from emailing.scheduler import run_scheduler_once
from emailing.store import EmailStore


EMAIL_FEATURES_ENABLED = False

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


async def _email_scheduler_loop(settings) -> None:
    """Poll pending email jobs and dispatch due messages."""
    while True:
        try:
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


async def _email_reply_loop(settings) -> None:
    """Poll inbox for replies and stop follow-up sequences."""
    while True:
        try:
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    settings = get_settings()
    app.state.settings = settings
    app.state.email_scheduler_task = None
    app.state.email_reply_task = None

    # Enable Langfuse tracing if configured
    from observability.setup import setup_observability
    setup_observability()

    if EMAIL_FEATURES_ENABLED and settings.email_sequence_enabled and settings.email_auto_send_enabled:
        app.state.email_scheduler_task = asyncio.create_task(_email_scheduler_loop(settings))
        logger.info("[EmailScheduler] background loop started")
    if EMAIL_FEATURES_ENABLED and settings.email_reply_detection_enabled:
        app.state.email_reply_task = asyncio.create_task(_email_reply_loop(settings))
        logger.info("[EmailReply] background loop started")

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
    app.include_router(email_router)
    app.include_router(sse_router, prefix="/api/v1")
    if settings.settings_api_enabled:
        app.include_router(settings_router)

    return app


app = create_app()
