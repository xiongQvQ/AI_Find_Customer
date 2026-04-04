"""Lightweight ReAct loop runner for tool-calling agents.

Uses litellm's native function-calling (tool_choice) so the reasoning model
decides which tool to invoke at each step.  No LangGraph dependency — this is
a simple async loop that can be embedded inside any LangGraph node.

Flow:
    1. Send system + user messages with tool definitions to the reasoning LLM.
    2. If the LLM returns tool_calls → execute them, append results, loop.
    3. If the LLM returns plain text (no tool_calls) → that's the final answer.
    4. Stop after max_iterations to prevent runaway loops.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Awaitable

import litellm

from config.settings import Settings, get_settings
from tools.llm_errors import format_llm_error
from tools.llm_client import _inject_api_keys, normalize_model_name
from tools.llm_rate_limiter import get_llm_rate_limiter

logger = logging.getLogger(__name__)

# Max number of "nudge" retries when the model returns non-JSON text
_MAX_JSON_NUDGES = 2

# Max messages allowed before trimming to prevent token overflow
_MAX_MESSAGES_BEFORE_TRIM = 30


async def _acompletion_with_rpm_limit(
    settings: Settings,
    *,
    scope: str = "reasoning",
    **kwargs: Any,
) -> Any:
    rpm = settings.reasoning_requests_per_minute or settings.llm_requests_per_minute
    await get_llm_rate_limiter(scope, rpm).acquire()
    return await litellm.acompletion(**kwargs)


def _clean_markdown_fences(text: str) -> str:
    """Strip markdown code fences from text."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n", 1)
        t = lines[1] if len(lines) > 1 else ""
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
        t = t.strip()
    return t


def _try_parse_json(text: str) -> dict | list | None:
    """Attempt to parse text as JSON after stripping markdown fences.

    Strategies:
    1. Direct parse after cleaning markdown fences
    2. Regex extraction of outermost {...}
    3. Regex extraction of outermost [...]

    Returns:
        Parsed dict/list, or None if all strategies fail.
    """
    if not text or not text.strip():
        return None

    cleaned = _clean_markdown_fences(text)

    # Strategy 1: direct parse
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: extract outermost JSON object {...}
    m = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    # Strategy 3: extract outermost JSON array [...]
    m = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return None


def _has_required_fields(parsed: dict | list | None, required_fields: list[str]) -> bool:
    """Check if parsed JSON dict contains all required fields."""
    if not required_fields or not isinstance(parsed, dict):
        return True  # No requirements or not a dict — accept as-is
    return all(field in parsed for field in required_fields)


def _trim_messages(messages: list[dict[str, Any]], keep_last: int = 10) -> list[dict[str, Any]]:
    """Trim messages to prevent token overflow.

    Keeps: system message (first) + initial user message (second) + last N messages.
    """
    if len(messages) <= keep_last + 2:
        return messages
    return messages[:2] + messages[-(keep_last):]


def _strip_tool_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove tool-call related messages from history.

    Used as a fallback for the final LLM call on models that require
    tool_schemas to be present whenever the history has tool_call messages
    (e.g. Anthropic-compatible APIs like MiniMax), but don't support
    tool_choice='none'.

    Strips: assistant messages with tool_calls, role='tool' messages.
    Keeps: system, user, and plain assistant text messages.
    """
    cleaned = []
    for m in messages:
        role = m.get("role", "")
        if role == "tool":
            continue
        if role == "assistant" and m.get("tool_calls"):
            # Keep only the text content if any, drop tool_calls
            content = m.get("content") or ""
            if content:
                cleaned.append({"role": "assistant", "content": content})
            continue
        cleaned.append(m)
    return cleaned


class ToolDef:
    """Definition of a tool the ReAct agent can call."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        fn: Callable[..., Awaitable[str]],
    ) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self.fn = fn

    def to_openai_schema(self) -> dict:
        """Convert to OpenAI function-calling tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def _record_react_cost(
    response: Any,
    hunt_id: str,
    agent: str,
    model: str,
    hunt_round: int,
) -> None:
    """Extract usage+cost from a litellm response and record to CostTracker."""
    if not hunt_id:
        return
    try:
        from observability.cost_tracker import get_tracker
        usage = getattr(response, "usage", None)
        if usage:
            cost = getattr(response, "_hidden_params", {}).get("response_cost") or 0.0
            get_tracker(hunt_id).record_llm_call(
                agent=agent,
                model=model,
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                cost_usd=float(cost),
                hunt_round=hunt_round,
            )
    except Exception:
        pass  # Never let tracking break the main flow


async def react_loop(
    *,
    system: str,
    user_prompt: str,
    tools: list[ToolDef],
    settings: Settings | None = None,
    max_iterations: int | None = None,
    required_json_fields: list[str] | None = None,
    hunt_id: str = "",
    agent: str = "react",
    hunt_round: int = 0,
) -> str:
    """Run a ReAct loop with the reasoning model.

    Args:
        system: System prompt describing the agent's role and goal.
        user_prompt: Initial user message with context.
        tools: List of ToolDef objects the agent can call.
        settings: Optional settings override.
        max_iterations: Max tool-call rounds (default from settings).
        required_json_fields: Optional list of field names that the final JSON
            must contain. If provided and the JSON is missing fields, the model
            is nudged to include them.
        hunt_id: Hunt ID for cost tracking (empty = no tracking).
        agent: Agent label for cost breakdown (e.g. "insight", "lead_extract").
        hunt_round: Current hunt round for per-round cost breakdown.

    Returns:
        The final text response from the agent (should be JSON).
    """
    _settings = settings or get_settings()
    max_iter = max_iterations or _settings.react_max_iterations
    model = normalize_model_name(_settings.reasoning_model)
    temperature = _settings.reasoning_temperature
    max_tokens = _settings.reasoning_max_tokens

    # Inject API keys
    _inject_api_keys(_settings)

    # Build tool schemas and lookup
    tool_schemas = [t.to_openai_schema() for t in tools]
    tool_map = {t.name: t for t in tools}

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]

    for iteration in range(1, max_iter + 1):
        logger.debug("[ReAct] Iteration %d/%d — calling %s", iteration, max_iter, model)

        # On the last allowed iteration, don't offer tools — force a text answer
        is_last = iteration == max_iter
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tool_schemas:
            kwargs["tools"] = tool_schemas
            if is_last:
                kwargs["tool_choice"] = "none"

        # Inject budget warning when nearing the limit
        if iteration == max_iter - 1:
            messages.append({
                "role": "user",
                "content": (
                    "⚠️ You have 1 tool-call round left. After this, you MUST output "
                    "your final JSON answer. Wrap up now."
                ),
            })

        try:
            response = await _acompletion_with_rpm_limit(_settings, **kwargs)
            _record_react_cost(response, hunt_id, agent, model, hunt_round)
        except Exception as e:
            # Fallback for last iteration: some Anthropic-compatible APIs (e.g. MiniMax)
            # reject tool_choice="none" or tools= when history has tool_call messages.
            # Retry with tool messages stripped and no tools= param.
            if is_last and tool_schemas:
                logger.warning(
                    "[ReAct] Last-iteration call failed (%s), retrying with stripped tool history", e
                )
                try:
                    fallback_kwargs = {
                        "model": model,
                        "messages": _strip_tool_messages(messages),
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    response = await _acompletion_with_rpm_limit(_settings, **fallback_kwargs)
                    _record_react_cost(response, hunt_id, agent, model, hunt_round)
                except Exception as e2:
                    formatted = format_llm_error(e2)
                    logger.error("[ReAct] Fallback call also failed at iteration %d: %s", iteration, formatted)
                    return json.dumps({"error": f"ReAct LLM call failed: {formatted}"})
            else:
                formatted = format_llm_error(e)
                logger.error("[ReAct] LLM call failed at iteration %d: %s", iteration, formatted)
                return json.dumps({"error": f"ReAct LLM call failed: {formatted}"})

        choice = response.choices[0]
        msg = choice.message

        # If no tool calls → check if it's a valid JSON final answer
        if not msg.tool_calls:
            content = msg.content or ""
            parsed = _try_parse_json(content)

            if parsed is not None and _has_required_fields(parsed, required_json_fields or []):
                logger.debug("[ReAct] Final answer at iteration %d", iteration)
                return json.dumps(parsed) if not isinstance(content, str) else content

            # Determine nudge reason
            if parsed is not None and not _has_required_fields(parsed, required_json_fields or []):
                missing = [f for f in (required_json_fields or []) if f not in parsed]
                nudge_reason = (
                    f"Your JSON is missing required fields: {missing}. "
                    f"Output a complete JSON object that includes ALL of these fields: "
                    f"{required_json_fields}. Output ONLY the JSON object."
                )
            else:
                nudge_reason = (
                    "Your response is not valid JSON. You MUST output ONLY a raw JSON "
                    "object (starting with '{') with the lead information. "
                    "Do NOT include any explanation or tool call syntax. "
                    "Output ONLY the JSON object."
                )

            # Model returned prose/thinking instead of JSON — nudge it
            logger.debug("[ReAct] Non-JSON or incomplete at iteration %d, nudging", iteration)
            messages.append(msg.model_dump())
            messages.append({"role": "user", "content": nudge_reason})

            # Trim messages if they've grown too large
            messages = _trim_messages(messages)

            # Nudge calls never pass tools= so strip tool-call messages from history
            # to avoid Anthropic-compatible API errors (e.g. MiniMax)
            nudge_messages = _strip_tool_messages(messages)

            # Use a dedicated nudge sub-loop to avoid consuming main iterations
            for nudge in range(_MAX_JSON_NUDGES):
                try:
                    nudge_resp = await _acompletion_with_rpm_limit(
                        _settings,
                        model=model,
                        messages=nudge_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    _record_react_cost(nudge_resp, hunt_id, agent, model, hunt_round)
                    nudge_content = nudge_resp.choices[0].message.content or ""
                    nudge_parsed = _try_parse_json(nudge_content)
                    if nudge_parsed is not None and _has_required_fields(
                        nudge_parsed, required_json_fields or []
                    ):
                        logger.debug("[ReAct] Got valid JSON after nudge %d", nudge + 1)
                        return nudge_content
                    # Still not valid — append and try once more
                    nudge_messages.append(nudge_resp.choices[0].message.model_dump())
                    nudge_messages.append({
                        "role": "user",
                        "content": "That is still not valid JSON. Output ONLY a raw JSON object starting with '{'. Nothing else.",
                    })
                    nudge_messages = _trim_messages(nudge_messages)
                except Exception as e:
                    logger.warning("[ReAct] Nudge call failed: %s", format_llm_error(e))
                    break
            # All nudges failed — return whatever we have
            logger.warning("[ReAct] Could not get JSON after %d nudges, returning raw", _MAX_JSON_NUDGES)
            return content

        # Append assistant message with tool calls
        messages.append(msg.model_dump())

        # Execute each tool call
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args_raw = tool_call.function.arguments

            try:
                fn_args = json.loads(fn_args_raw) if fn_args_raw else {}
            except json.JSONDecodeError:
                fn_args = {}

            tool_def = tool_map.get(fn_name)
            if not tool_def:
                result = json.dumps({"error": f"Unknown tool: {fn_name}"})
            else:
                try:
                    logger.debug("[ReAct] Calling tool %s(%s)", fn_name, fn_args)
                    result = await tool_def.fn(**fn_args)
                except Exception as e:
                    logger.warning("[ReAct] Tool %s failed: %s", fn_name, e)
                    result = json.dumps({"error": f"Tool {fn_name} failed: {e}"})

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    # Exhausted iterations — ask for final answer without tools
    logger.warning("[ReAct] Max iterations (%d) reached, requesting final answer", max_iter)
    messages.append({
        "role": "user",
        "content": "STOP calling tools. Output your final JSON answer NOW based on everything gathered so far. Output ONLY a raw JSON object starting with '{'. Nothing else.",
    })

    # Trim and strip tool messages — final answer calls never pass tools=
    final_messages = _strip_tool_messages(_trim_messages(messages))

    for attempt in range(_MAX_JSON_NUDGES + 1):
        try:
            response = await _acompletion_with_rpm_limit(
                _settings,
                model=model,
                messages=final_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            _record_react_cost(response, hunt_id, agent, model, hunt_round)
            content = response.choices[0].message.content or ""
            parsed = _try_parse_json(content)
            if parsed is not None and _has_required_fields(
                parsed, required_json_fields or []
            ):
                return content
            if attempt < _MAX_JSON_NUDGES:
                final_messages.append(response.choices[0].message.model_dump())
                final_messages.append({
                    "role": "user",
                    "content": "That is not valid JSON. Output ONLY a raw JSON object starting with '{'. Nothing else.",
                })
                final_messages = _trim_messages(final_messages)
        except Exception as e:
            formatted = format_llm_error(e)
            logger.error("[ReAct] Final answer call failed: %s", formatted)
            return json.dumps({"error": f"ReAct final answer failed: {formatted}"})

    logger.warning("[ReAct] Could not get JSON final answer after retries")
    return content
