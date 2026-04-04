from automation.notifier import (
    render_alert_text,
    render_discovery_batch_text,
    render_hunt_completed_text,
    render_hunt_failed_text,
    render_hunt_started_text,
    render_send_batch_text,
    render_summary_text,
)


def test_render_summary_text_includes_key_counts():
    text = render_summary_text(
        {
            "window_hours": 2,
            "hunt_jobs": {"completed": 3, "failed": 1, "queued": 2, "running": 1, "retrying": 2},
            "hunts": {"created": 4, "completed": 3, "failed": 1, "new_leads": 120, "generated_email_sequences": 44},
            "emails": {"queued": 20, "sent": 18, "failed": 2, "replied": 1, "active_campaigns": 2, "active_sequences": 14, "replied_sequences": 1},
            "status_snapshot": {"hunts": {"running_details": [{"website_url": "https://www.gdushun.com/", "current_stage": "lead_extract", "leads_count": 4, "email_sequences_count": 0}]}},
            "recent_completed_hunts": [{"website_url": "https://www.gdushun.com/", "lead_count": 88, "email_sequence_count": 30}],
            "recent_failed_hunts": [{"website_url": "https://retry.example.com", "current_stage": "lead_extract", "error": "minimax 429", "retry_status": "queued_retry", "retry_attempts": 2}],
            "top_failure_reasons": [{"failure_reason": "smtp_timeout", "count": 2}],
            "recent_failures": [{"lead_email": "buyer@example.com", "subject": "Hello", "failure_reason": "smtp_timeout"}],
        }
    )
    assert "最近 2 小时" in text
    assert "Hunt 已创建 4" in text
    assert "新增企业 120" in text
    assert "已发送 18" in text
    assert "队列重试中 2" in text
    assert "当前运行中:" in text
    assert "最近失败Hunt:" in text
    assert "失败原因Top:" in text


def test_render_alert_text():
    text = render_alert_text(
        {"hunt_jobs": {"queued": 25}, "email_queue": {"pending": 30}},
        {"emails": {"failed": 12}},
    )
    assert "待执行 hunt_jobs: 25" in text
    assert "待发送邮件: 30" in text
    assert "最近窗口失败发送: 12" in text


def test_render_hunt_started_and_completed_text():
    started = render_hunt_started_text(
        {
            "website_url": "https://www.gdushun.com/",
            "target_regions": ["United States"],
            "target_lead_count": 100,
            "enable_email_craft": True,
            "description": "Find distributors",
        },
        hunt_id="hunt-123",
    )
    completed = render_hunt_completed_text(
        {
            "hunt_id": "hunt-123",
            "website_url": "https://www.gdushun.com/",
            "lead_count": 88,
            "email_sequence_count": 30,
            "campaign": {"campaign_id": "camp-1", "status": "active"},
        }
    )
    failed = render_hunt_failed_text(
        {"website_url": "https://www.gdushun.com/", "target_lead_count": 100, "description": "Find distributors"},
        error_message="timeout",
    )
    assert "任务开始" in started
    assert "官网: https://www.gdushun.com/" in started
    assert "任务结束" in completed
    assert "新增企业: 88" in completed
    assert "主要目标官网: https://www.gdushun.com/" in completed
    assert "任务失败" in failed


def test_render_discovery_and_send_batch_text():
    discovery = render_discovery_batch_text([
        {"company_name": "Acme", "website": "https://acme.com", "email_count": 2},
        {"company_name": "Beta", "website": "https://beta.com", "email_count": 1},
    ])
    sending = render_send_batch_text([
        {"company_name": "Acme", "lead_email": "buyer@acme.com", "subject": "Hello"},
        {"company_name": "Beta", "lead_email": "sales@beta.com", "subject": "Offer"},
    ])
    assert "新增企业" in discovery
    assert "Acme" in discovery
    assert "邮件已发送" in sending
    assert "buyer@acme.com" in sending
