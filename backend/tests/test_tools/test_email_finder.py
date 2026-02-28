"""Tests for tools/email_finder.py — regex extraction, Hunter.io mock, filtering."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from config.settings import Settings
from tools.email_finder import EmailFinderTool, extract_emails_from_text, _is_valid_email

_FAKE_REQUEST = httpx.Request("GET", "https://fake")


class TestExtractEmailsFromText:
    def test_basic_extraction(self):
        text = "Contact us at info@solartech.de or sales@solartech.de"
        emails = extract_emails_from_text(text)
        assert "info@solartech.de" in emails
        assert "sales@solartech.de" in emails

    def test_deduplication(self):
        text = "info@x.com and INFO@X.COM and info@x.com"
        emails = extract_emails_from_text(text)
        assert len(emails) == 1

    def test_filters_blacklisted_domains(self):
        text = "user@example.com and real@company.com"
        emails = extract_emails_from_text(text)
        assert "user@example.com" not in emails
        assert "real@company.com" in emails

    def test_filters_blacklisted_prefixes(self):
        text = "noreply@company.com and sales@company.com"
        emails = extract_emails_from_text(text)
        assert "noreply@company.com" not in emails
        assert "sales@company.com" in emails

    def test_filters_image_domains(self):
        text = "icon@image.png and real@company.com"
        emails = extract_emails_from_text(text)
        assert "icon@image.png" not in emails
        assert "real@company.com" in emails

    def test_empty_text(self):
        assert extract_emails_from_text("") == []

    def test_no_emails_in_text(self):
        assert extract_emails_from_text("No emails here, just text.") == []

    def test_mixed_content(self):
        text = """
        Welcome to SolarTech GmbH.
        For inquiries: info@solartech.de
        Technical support: support@solartech.de
        Image: logo@solartech.png
        Do not reply: noreply@solartech.de
        """
        emails = extract_emails_from_text(text)
        assert "info@solartech.de" in emails
        assert "support@solartech.de" in emails
        assert "noreply@solartech.de" not in emails


class TestIsValidEmail:
    def test_valid(self):
        assert _is_valid_email("info@company.com") is True

    def test_blacklisted_domain(self):
        assert _is_valid_email("user@example.com") is False

    def test_blacklisted_prefix(self):
        assert _is_valid_email("noreply@company.com") is False

    def test_image_domain(self):
        assert _is_valid_email("icon@img.jpg") is False


class TestEmailFinderToolFindInText:
    def test_find_in_text(self):
        tool = EmailFinderTool()
        emails = tool.find_in_text("Contact sales@acme.com for details")
        assert emails == ["sales@acme.com"]


class TestEmailFinderToolHunterIO:
    @pytest.mark.asyncio
    async def test_find_by_domain_with_api_key(self):
        settings = Settings(hunter_api_key="hunter-test-key")
        tool = EmailFinderTool(settings=settings)

        hunter_response = {
            "data": {
                "emails": [
                    {
                        "value": "john@solartech.de",
                        "first_name": "John",
                        "last_name": "Doe",
                        "position": "CEO",
                        "confidence": 95,
                    },
                    {
                        "value": "info@solartech.de",
                        "first_name": "",
                        "last_name": "",
                        "position": "",
                        "confidence": 80,
                    },
                ]
            }
        }
        mock_resp = httpx.Response(200, json=hunter_response, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.find_by_domain("solartech.de")

        assert len(results) == 2
        assert results[0]["email"] == "john@solartech.de"
        assert results[0]["confidence"] == 95
        assert results[0]["position"] == "CEO"
        await tool.close()

    @pytest.mark.asyncio
    async def test_find_by_domain_no_api_key(self):
        settings = Settings(hunter_api_key="")
        tool = EmailFinderTool(settings=settings)
        results = await tool.find_by_domain("solartech.de")
        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_find_by_domain_empty_results(self):
        settings = Settings(hunter_api_key="key")
        tool = EmailFinderTool(settings=settings)

        mock_resp = httpx.Response(200, json={"data": {"emails": []}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            results = await tool.find_by_domain("unknown-domain.xyz")

        assert results == []
        await tool.close()

    @pytest.mark.asyncio
    async def test_find_by_domain_sends_correct_params(self):
        settings = Settings(hunter_api_key="my-key")
        tool = EmailFinderTool(settings=settings)

        captured_params = {}

        async def mock_get(url, **kwargs):
            captured_params.update(kwargs.get("params", {}))
            return httpx.Response(200, json={"data": {"emails": []}}, request=_FAKE_REQUEST)

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            await tool.find_by_domain("test.com")

        assert captured_params["domain"] == "test.com"
        assert captured_params["api_key"] == "my-key"
        await tool.close()
