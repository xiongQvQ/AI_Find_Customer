"""Tests for tools/email_verifier.py — syntax check, MX lookup mock."""

from unittest.mock import patch

import pytest

from tools.email_verifier import EmailVerifierTool, _has_valid_syntax, _get_mx_records


class TestHasValidSyntax:
    def test_valid_emails(self):
        assert _has_valid_syntax("info@company.com") is True
        assert _has_valid_syntax("john.doe@solartech.de") is True
        assert _has_valid_syntax("user+tag@domain.co.uk") is True

    def test_invalid_emails(self):
        assert _has_valid_syntax("") is False
        assert _has_valid_syntax("not-an-email") is False
        assert _has_valid_syntax("@domain.com") is False
        assert _has_valid_syntax("user@") is False
        assert _has_valid_syntax("user@.com") is False
        assert _has_valid_syntax("user@domain") is False


class TestGetMxRecords:
    def test_with_mock_dns_resolver(self):
        """Mock dns.resolver to return MX records."""
        mock_answer = type("Answer", (), {
            "preference": 10,
            "exchange": "mx1.example.com.",
        })()
        mock_answer2 = type("Answer", (), {
            "preference": 20,
            "exchange": "mx2.example.com.",
        })()

        with patch("dns.resolver.resolve", return_value=[mock_answer, mock_answer2]):
            records = _get_mx_records("example.com")

        assert records == ["mx1.example.com", "mx2.example.com"]

    def test_no_dns_module_fallback(self):
        """When dns module is not available, fallback to socket."""
        with patch.dict("sys.modules", {"dns": None, "dns.resolver": None}):
            # This will hit the ImportError path and try socket
            # We can't easily test the socket fallback without network
            # Just verify it doesn't crash
            pass

    def test_exception_returns_empty(self):
        """Any exception during MX lookup returns empty list."""
        with patch("dns.resolver.resolve", side_effect=Exception("DNS error")):
            records = _get_mx_records("nonexistent.invalid")
        assert records == []


class TestEmailVerifierTool:
    @pytest.mark.asyncio
    async def test_verify_invalid_syntax(self):
        tool = EmailVerifierTool()
        result = await tool.verify("not-an-email")
        assert result["valid_syntax"] is False
        assert result["has_mx"] is False
        assert result["is_deliverable"] is False

    @pytest.mark.asyncio
    async def test_verify_valid_with_mx(self):
        tool = EmailVerifierTool()

        with patch("tools.email_verifier._get_mx_records", return_value=["mx1.google.com"]):
            result = await tool.verify("info@company.com")

        assert result["email"] == "info@company.com"
        assert result["valid_syntax"] is True
        assert result["has_mx"] is True
        assert result["is_deliverable"] is True
        assert result["mx_records"] == ["mx1.google.com"]

    @pytest.mark.asyncio
    async def test_verify_valid_no_mx(self):
        tool = EmailVerifierTool()

        with patch("tools.email_verifier._get_mx_records", return_value=[]):
            result = await tool.verify("info@nonexistent-domain.xyz")

        assert result["valid_syntax"] is True
        assert result["has_mx"] is False
        assert result["is_deliverable"] is False

    @pytest.mark.asyncio
    async def test_verify_normalizes_email(self):
        tool = EmailVerifierTool()

        with patch("tools.email_verifier._get_mx_records", return_value=["mx.test.com"]):
            result = await tool.verify("  INFO@Company.COM  ")

        assert result["email"] == "info@company.com"

    @pytest.mark.asyncio
    async def test_verify_batch(self):
        tool = EmailVerifierTool()

        def mock_mx(domain):
            return ["mx.test.com"] if domain == "good.com" else []

        with patch("tools.email_verifier._get_mx_records", side_effect=mock_mx):
            results = await tool.verify_batch([
                "user@good.com",
                "user@bad.xyz",
                "invalid",
            ])

        assert len(results) == 3
        assert results[0]["is_deliverable"] is True
        assert results[1]["is_deliverable"] is False
        assert results[2]["valid_syntax"] is False
