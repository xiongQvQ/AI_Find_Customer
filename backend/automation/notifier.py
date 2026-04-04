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
    running_details = (metrics.get("status_snapshot", {}) or {}).get("hunts", {}).get("running_details", []) or []
    recent_completed = metrics.get("recent_completed_hunts", []) or []
    failure_reasons = metrics.get("top_failure_reasons", []) or []
    lines = [
        f"AI Hunter 汇总 | 最近 {metrics.get('window_hours', 0)} 小时",
        f"任务队列: 完成 {jobs.get('completed', 0)} | 失败 {jobs.get('failed', 0)} | 排队 {jobs.get('queued', 0)} | 运行 {jobs.get('running', 0)}",
        f"Hunt结果: 新建 {hunts.get('created', 0)} | 完成 {hunts.get('completed', 0)} | 失败 {hunts.get('failed', 0)} | 新增企业 {hunts.get('new_leads', 0)}",
        f"邮件产出: 生成序列 {hunts.get('generated_email_sequences', 0)} | 活跃Campaign {emails.get('active_campaigns', 0)} | 活跃序列 {emails.get('active_sequences', 0)} | 已回复序列 {emails.get('replied_sequences', 0)}",
        f"发送表现: 待发送 {emails.get('queued', 0)} | 已发送 {emails.get('sent', 0)} | 失败 {emails.get('failed', 0)} | 回复 {emails.get('replied', 0)}",
    ]
    if running_details:
        lines.append("当前运行中:")
        for item in running_details[:3]:
            lines.append(
                f"- {item.get('website_url', '-') or '-'} | 阶段 {item.get('current_stage', '-') or '-'} | 企业 {item.get('leads_count', 0)} | 邮件 {item.get('email_sequences_count', 0)}"
            )
    if recent_completed:
        lines.append("最近完成:")
        for item in recent_completed[:3]:
            lines.append(
                f"- {item.get('website_url', '-') or '-'} | 企业 {item.get('lead_count', 0)} | 邮件序列 {item.get('email_sequence_count', 0)}"
            )
    if failure_reasons:
        lines.append(
            "失败原因Top: " + " | ".join(
                f"{item.get('failure_reason') or 'unknown'} x{item.get('count', 0)}"
                for item in failure_reasons[:3]
            )
        )
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


def render_hunt_started_text(payload: dict[str, Any], *, hunt_id: str) -> str:
    website = str(payload.get("website_url", "") or "")
    description = str(payload.get("description", "") or "")
    regions = ", ".join(payload.get("target_regions", []) or [])
    return "\n".join(
        [
            "AI Hunter 任务开始",
            f"Hunt ID: {hunt_id}",
            f"官网: {website or '-'}",
            f"地区: {regions or '-'}",
            f"目标线索数: {payload.get('target_lead_count', 0)}",
            f"邮件生成: {bool(payload.get('enable_email_craft', False))}",
            f"描述: {description[:300] or '-'}",
        ]
    )


def render_hunt_completed_text(result: dict[str, Any]) -> str:
    campaign = result.get("campaign") or {}
    return "\n".join(
        [
            "AI Hunter 任务结束",
            f"Hunt ID: {result.get('hunt_id', '')}",
            f"新增企业: {result.get('lead_count', 0)}",
            f"生成邮件序列: {result.get('email_sequence_count', 0)}",
            f"主要目标官网: {result.get('website_url', '-')}",
            f"Campaign: {campaign.get('campaign_id', '-')}",
            f"Campaign 状态: {campaign.get('status', '-')}",
        ]
    )


def render_hunt_failed_text(payload: dict[str, Any], *, error_message: str) -> str:
    website = str(payload.get("website_url", "") or "")
    description = str(payload.get("description", "") or "")
    return "\n".join(
        [
            "AI Hunter 任务失败",
            f"官网: {website or '-'}",
            f"目标线索数: {payload.get('target_lead_count', 0)}",
            f"描述: {description[:200] or '-'}",
            f"错误: {error_message[:500]}",
        ]
    )
