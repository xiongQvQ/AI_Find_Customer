"""LLM tool — unified multi-provider interface via litellm.

Supports: OpenAI, Anthropic, OpenRouter, Groq, GLM (智谱), Kimi (Moonshot),
MiniMax, and 100+ other providers through litellm.
"""

from __future__ import annotations

import os
from typing import Any

import litellm

from config.settings import Settings, get_settings


# Suppress litellm's verbose logging by default
litellm.suppress_debug_info = True


def _inject_api_keys(settings: Settings) -> None:
    """Push provider API keys from Settings into env vars for litellm."""
    _key_map = {
        "OPENAI_API_KEY": settings.openai_api_key,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
        "GROQ_API_KEY": settings.groq_api_key,
        "ZAI_API_KEY": settings.zai_api_key,
        "MOONSHOT_API_KEY": settings.moonshot_api_key,
        "MINIMAX_API_KEY": settings.minimax_api_key,
        "MINIMAX_API_BASE": settings.minimax_api_base,
        "ZHIPUAI_API_KEY": settings.zai_api_key,
    }
    for env_var, value in _key_map.items():
        if value and not os.environ.get(env_var):
            os.environ[env_var] = value

    # Native workaround: If using anthropic/ prefix for MiniMax, inject ANTHROPIC_API_BASE
    if settings.llm_model.startswith("anthropic/") and "minimax" in settings.llm_model.lower():
        os.environ["ANTHROPIC_API_BASE"] = settings.minimax_api_base
    if settings.reasoning_model.startswith("anthropic/") and "minimax" in settings.reasoning_model.lower():
        os.environ["ANTHROPIC_API_BASE"] = settings.minimax_api_base


class LLMTool:
    """Unified LLM client powered by litellm.

    All calls go through a single interface so agents don't care about the
    provider.  Just set ``llm_model`` in Settings (or ``LLM_MODEL`` in .env)
    using litellm model naming, e.g.:
      - ``gpt-4o``
      - ``anthropic/claude-3-5-sonnet-20241022``
      - ``openrouter/google/gemini-pro``
      - ``groq/llama-3.3-70b-versatile``
      - ``zai/glm-4.7``
      - ``moonshot/moonshot-v1-128k``
      - ``minimax/MiniMax-Text-01``

    Args:
        model_type: ``"default"`` uses ``llm_model`` (fast, cheap — data extraction).
                    ``"reasoning"`` uses ``reasoning_model`` (strong reasoning — ReAct decisions).
        settings: Optional Settings override.
        hunt_id: Optional hunt ID for cost tracking.
        agent: Agent name label for cost tracking (e.g. "keyword_gen", "email_craft").
        hunt_round: Current hunt round for per-round cost breakdown.
    """

    def __init__(
        self,
        model_type: str = "default",
        settings: Settings | None = None,
        hunt_id: str = "",
        agent: str = "unknown",
        hunt_round: int = 0,
    ) -> None:
        self._settings = settings or get_settings()
        self._model_type = model_type
        self._hunt_id = hunt_id
        self._agent = agent
        self._hunt_round = hunt_round
        _inject_api_keys(self._settings)

    @property
    def model(self) -> str:
        if self._model_type == "reasoning":
            return self._settings.reasoning_model
        return self._settings.llm_model

    @property
    def _default_temperature(self) -> float:
        if self._model_type == "reasoning":
            return self._settings.reasoning_temperature
        return self._settings.llm_temperature

    @property
    def _default_max_tokens(self) -> int:
        if self._model_type == "reasoning":
            return self._settings.reasoning_max_tokens
        return self._settings.llm_max_tokens

    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> str:
        """Generate a completion from the LLM.

        Args:
            prompt: User message / main prompt.
            system: Optional system message.
            temperature: Override default temperature.
            max_tokens: Override default max_tokens.
            response_format: Optional JSON mode config.

        Returns:
            The generated text content.
        """
        temp = temperature if temperature is not None else self._default_temperature
        tokens = max_tokens or self._default_max_tokens

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await litellm.acompletion(**kwargs)

        # Record cost to tracker if hunt_id is set
        if self._hunt_id:
            try:
                from observability.cost_tracker import get_tracker
                usage = getattr(response, "usage", None)
                if usage:
                    cost = getattr(response, "_hidden_params", {}).get("response_cost") or 0.0
                    get_tracker(self._hunt_id).record_llm_call(
                        agent=self._agent,
                        model=self.model,
                        prompt_tokens=getattr(usage, "prompt_tokens", 0),
                        completion_tokens=getattr(usage, "completion_tokens", 0),
                        cost_usd=float(cost),
                        hunt_round=self._hunt_round,
                    )
            except Exception:
                pass  # Never let tracking break the main flow

        return response.choices[0].message.content

    async def close(self) -> None:
        """No-op — litellm manages its own connections."""
        pass
