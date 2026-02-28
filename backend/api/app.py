"""FastAPI application — main entry point for the AI Hunter API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.settings_routes import router as settings_router
from api.sse import sse_router
from config.settings import get_settings

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    settings = get_settings()
    app.state.settings = settings

    # Enable Langfuse tracing if configured
    from observability.setup import setup_observability
    setup_observability()

    yield


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
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")
    app.include_router(sse_router, prefix="/api/v1")
    app.include_router(settings_router)

    return app


app = create_app()
