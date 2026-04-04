"""Helpers for normalizing provider-specific LLM errors into actionable messages."""

from __future__ import annotations


def format_llm_error(exc: Exception) -> str:
    """Return a concise, user-actionable error string for upstream LLM failures."""
    raw = str(exc).strip() or exc.__class__.__name__
    lowered = raw.lower()

    if "insufficient_balance_error" in lowered or "insufficient balance" in lowered:
        return (
            "MiniMax API 调用失败：账户余额不足。"
            "请充值或切换到其他可用模型/API Key 后重试。"
            f" 原始错误: {raw}"
        )

    if '"http_code":"429"' in lowered or "http_code': 429" in lowered:
        return f"LLM API 调用失败：上游返回 429，请检查配额、限流或账户状态。原始错误: {raw}"

    return raw
