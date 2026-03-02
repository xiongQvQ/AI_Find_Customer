"""
Unified LLM client using litellm.

Configuration (in .env):
    LLM_MODEL=openai/gpt-4o-mini          # OpenAI
    LLM_MODEL=anthropic/claude-3-haiku-20240307
    LLM_MODEL=gemini/gemini-1.5-flash
    LLM_MODEL=deepseek/deepseek-chat       # DeepSeek (国内)
    LLM_MODEL=zhipuai/glm-4-flash         # Zhipu GLM (国内)
    LLM_MODEL=minimax/abab6.5s-chat       # MiniMax (国内)
    LLM_MODEL=volcengine/doubao-1-5-pro-256k-250115  # 火山豆包 (国内)
    LLM_MODEL=openrouter/google/gemma-3-27b-it:free
    LLM_MODEL=xai/grok-3-mini-beta

Required env var: LLM_MODEL (leave empty to disable LLM features)
Provider API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY,
                   DEEPSEEK_API_KEY, ZHIPUAI_API_KEY, MINIMAX_API_KEY,
                   OPENROUTER_API_KEY, XAI_API_KEY, VOLCENGINE_API_KEY
"""

from __future__ import annotations

import json
import logging
import os
import re

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Volcano Engine / 火山引擎 special handling ────────────────────────────
# litellm routes volcengine models via the OpenAI-compatible base URL.
# We set OPENAI_API_BASE / OPENAI_API_KEY so litellm's openai provider picks
# it up when the model string starts with "volcengine/".
_VOLCENGINE_BASE = os.getenv(
    "VOLCENGINE_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"
)
_VOLCENGINE_KEY = os.getenv("VOLCENGINE_API_KEY", "")

# ── Public API ────────────────────────────────────────────────────────────


def get_llm_model() -> str:
    """Return the configured LLM_MODEL string, or empty string if not set."""
    return os.getenv("LLM_MODEL", "").strip()


def is_llm_available() -> bool:
    """Return True if LLM_MODEL is configured and a matching API key exists."""
    model = get_llm_model()
    if not model:
        return False
    return _has_api_key(model)


def call_llm(
    system: str,
    user: str,
    temperature: float = 0.6,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Call the configured LLM via litellm and return the response text.

    Args:
        system: System prompt string.
        user: User message string.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in the response.
        json_mode: If True, request JSON output (supported on OpenAI-compatible APIs).

    Returns:
        Response text string.

    Raises:
        ValueError: If LLM_MODEL is not configured.
        RuntimeError: If the LLM call fails.
    """
    model = get_llm_model()
    if not model:
        raise ValueError(
            "LLM_MODEL is not configured. "
            "Set LLM_MODEL in your .env file, e.g. LLM_MODEL=openai/gpt-4o-mini"
        )

    try:
        import litellm  # lazy import so the module loads even without litellm installed
    except ImportError as exc:
        raise RuntimeError(
            "litellm is not installed. Run: pip install litellm"
        ) from exc

    # Suppress verbose litellm logging unless DEBUG is set
    if not os.getenv("DEBUG"):
        litellm.suppress_debug_info = True
        logging.getLogger("litellm").setLevel(logging.WARNING)
        logging.getLogger("LiteLLM").setLevel(logging.WARNING)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    kwargs: dict = {
        "model": _resolve_model(model),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Volcano Engine: pass api_base + api_key through litellm extra_headers / api_base
    if model.startswith("volcengine/"):
        kwargs["api_base"] = _VOLCENGINE_BASE
        kwargs["api_key"] = _VOLCENGINE_KEY

    # OpenRouter requires HTTP-Referer header
    if model.startswith("openrouter/"):
        kwargs["headers"] = {
            "HTTP-Referer": "https://github.com/xiongQvQ/AI_Find_Customer",
            "X-Title": "AI-Find-Customer",
        }

    # JSON mode (OpenAI-compatible only — gracefully ignored otherwise)
    if json_mode:
        try:
            kwargs["response_format"] = {"type": "json_object"}
        except Exception:
            pass

    try:
        response = litellm.completion(**kwargs)
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.error("LLM call failed (model=%s): %s", model, exc)
        raise RuntimeError(f"LLM call failed: {exc}") from exc


def parse_json_response(raw: str) -> dict | list | None:
    """
    Robustly parse JSON from LLM output.
    Handles markdown code fences and partial JSON.
    Returns parsed object, or None on failure.
    """
    if not raw:
        return None

    text = raw.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first line (```json or ```) and last line if it's ```
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract the first JSON object or array
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


# ── Internal helpers ──────────────────────────────────────────────────────


def _resolve_model(model: str) -> str:
    """
    Map provider-specific model names to litellm model strings.
    Mostly a pass-through; handles volcengine stripping for litellm routing.
    """
    # Volcano Engine: litellm routes it as openai with a custom base_url.
    # We keep "volcengine/<name>" and pass api_base separately in call_llm.
    return model


def _has_api_key(model: str) -> bool:
    """Check that the API key for the model's provider is set."""
    m = model.lower()

    if m.startswith("openai/"):
        return bool(os.getenv("OPENAI_API_KEY"))
    if m.startswith("anthropic/"):
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    if m.startswith("gemini/") or m.startswith("google/"):
        return bool(os.getenv("GOOGLE_API_KEY"))
    if m.startswith("deepseek/"):
        return bool(os.getenv("DEEPSEEK_API_KEY"))
    if m.startswith("zhipuai/"):
        return bool(os.getenv("ZHIPUAI_API_KEY"))
    if m.startswith("minimax/"):
        return bool(os.getenv("MINIMAX_API_KEY"))
    if m.startswith("volcengine/"):
        return bool(os.getenv("VOLCENGINE_API_KEY"))
    if m.startswith("openrouter/"):
        return bool(os.getenv("OPENROUTER_API_KEY"))
    if m.startswith("xai/"):
        return bool(os.getenv("XAI_API_KEY"))

    # Unknown prefix — optimistically return True so the call can proceed
    return True
