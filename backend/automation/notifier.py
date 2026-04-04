"""Feishu notification helpers for headless automation."""

from __future__ import annotations

import json
from typing import Any
from urllib import error, request


def send_feishu_text(webhook_url: str, text: str) -> dict[str, Any]:
    payload = {
        "msg_type": "text",
        "content": {"text": text},
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return json.loads(body)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Feishu webhook failed: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Feishu webhook failed: {exc.reason}") from exc


def render_summary_text(metrics: dict[str, Any]) -> str:
    hunts = metrics.get("hunts", {})
    emails = metrics.get("emails", {})
    jobs = metrics.get("hunt_jobs", {})
    failures = metrics.get("recent_failures", []) or []
    lines = [
        f"AI Hunter 汇总 | 最近 {metrics.get('window_hours', 0)} 小时",
        f"挖掘任务: 完成 {jobs.get('completed', 0)} | 失败 {jobs.get('failed', 0)} | 排队 {jobs.get('queued', 0)} | 运行 {jobs.get('running', 0)}",
        f"Hunt: 新建 {hunts.get('created', 0)} | 完成 {hunts.get('completed', 0)} | 失败 {hunts.get('failed', 0)}",
        f"线索与邮件: 新增企业 {hunts.get('new_leads', 0)} | 生成邮件序列 {hunts.get('generated_email_sequences', 0)}",
        f"发送: 待发送 {emails.get('queued', 0)} | 已发送 {emails.get('sent', 0)} | 失败 {emails.get('failed', 0)} | 回复 {emails.get('replied', 0)}",
    ]
    if failures:
        sample = failures[0]
        lines.append(
            "最近失败示例: "
            f"{sample.get('lead_email', '')} | {sample.get('subject', '')} | {sample.get('failure_reason', '')}"
        )
    return "\n".join(lines)


def render_alert_text(status: dict[str, Any], metrics: dict[str, Any]) -> str:
    hunt_jobs = status.get("hunt_jobs", {})
    email_queue = status.get("email_queue", {})
    emails = metrics.get("emails", {})
    return "\n".join(
        [
            "AI Hunter 告警",
            f"待执行 hunt_jobs: {hunt_jobs.get('queued', 0)}",
            f"待发送邮件: {email_queue.get('pending', 0)}",
            f"最近窗口失败发送: {emails.get('failed', 0)}",
        ]
    )

