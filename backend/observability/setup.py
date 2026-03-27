"""Langfuse observability setup via litellm's built-in callback.

When LANGFUSE_ENABLED=true, this module configures litellm to automatically
report every LLM call (tokens, cost, latency, model, messages) to Langfuse.

litellm natively supports Langfuse — it reads these env vars automatically:
  - LANGFUSE_PUBLIC_KEY
  - LANGFUSE_SECRET_KEY
  - LANGFUSE_HOST

Usage:
    Call ``setup_observability()`` once at app startup (e.g. in api/app.py).
"""

from __future__ import annotations

import logging
import os

import litellm

from config.settings import get_settings

logger = logging.getLogger(__name__)


def setup_observability() -> None:
    """Enable Langfuse tracing if configured."""
    settings = get_settings()

    if not settings.langfuse_enabled:
        logger.info("[Observability] Langfuse disabled (LANGFUSE_ENABLED=false)")
        return

    # litellm reads Langfuse keys from env vars directly
    if settings.langfuse_public_key:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    if settings.langfuse_secret_key:
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    if settings.langfuse_host:
        os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)

    # Validate keys are present
    if not os.environ.get("LANGFUSE_PUBLIC_KEY") or not os.environ.get("LANGFUSE_SECRET_KEY"):
        logger.warning(
            "[Observability] LANGFUSE_ENABLED=true but LANGFUSE_PUBLIC_KEY or "
            "LANGFUSE_SECRET_KEY is missing. Skipping Langfuse setup."
        )
        return

    # Register Langfuse as a litellm callback — this automatically tracks:
    #   - Token usage (prompt_tokens, completion_tokens, total_tokens)
    #   - Cost (calculated by litellm based on model pricing)
    #   - Latency
    #   - Model name
    #   - Messages (input/output)
    #   - Errors
    if "langfuse" not in litellm.success_callback:
        litellm.success_callback.append("langfuse")
    if "langfuse" not in litellm.failure_callback:
        litellm.failure_callback.append("langfuse")

    logger.info(
        "[Observability] Langfuse enabled — host=%s, traces will appear in dashboard",
        settings.langfuse_host,
    )
