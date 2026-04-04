from automation.notifier import render_alert_text, render_summary_text


def test_render_summary_text_includes_key_counts():
    text = render_summary_text(
        {
            "window_hours": 2,
            "hunt_jobs": {"completed": 3, "failed": 1, "queued": 2, "running": 1},
            "hunts": {"created": 4, "completed": 3, "failed": 1, "new_leads": 120, "generated_email_sequences": 44},
            "emails": {"queued": 20, "sent": 18, "failed": 2, "replied": 1},
            "recent_failures": [{"lead_email": "buyer@example.com", "subject": "Hello", "failure_reason": "smtp_timeout"}],
        }
    )
    assert "最近 2 小时" in text
    assert "新增企业 120" in text
    assert "已发送 18" in text


def test_render_alert_text():
    text = render_alert_text(
        {"hunt_jobs": {"queued": 25}, "email_queue": {"pending": 30}},
        {"emails": {"failed": 12}},
    )
    assert "待执行 hunt_jobs: 25" in text
    assert "待发送邮件: 30" in text
    assert "最近窗口失败发送: 12" in text

