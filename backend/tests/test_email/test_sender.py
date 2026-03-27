from unittest.mock import MagicMock, patch

import pytest

from emailing.email_sender import send_email


@pytest.mark.asyncio
async def test_send_email_missing_recipient():
    result = await send_email({}, to_email="", subject="Hi", body_text="Hello")
    assert result["ok"] is False
    assert result["error_type"] == "invalid_recipient"


@pytest.mark.asyncio
async def test_send_email_smtp_success():
    account = {
        "provider_type": "smtp",
        "from_name": "B2Binsights",
        "from_email": "sales@example.com",
        "reply_to": "sales@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "sales@example.com",
        "smtp_secret_encrypted": "secret",
        "use_tls": 1,
    }
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    smtp.__exit__.return_value = False
    with patch("emailing.email_sender.smtplib.SMTP", return_value=smtp):
        result = await send_email(account, to_email="buyer@example.com", subject="Hi", body_text="Hello")
    assert result["ok"] is True
    assert result["provider"] == "smtp"
    assert result["provider_message_id"].startswith("<")

