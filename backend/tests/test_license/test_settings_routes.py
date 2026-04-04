"""Tests for api/settings_routes.py — license and settings API endpoints."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from license.validator import LicenseResult, LicenseStatus


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── GET /api/settings ─────────────────────────────────────────────────────────

class TestGetSettings:
    @pytest.mark.asyncio
    async def test_returns_settings_shape(self, client):
        with (
            patch("api.settings_routes.read_settings", return_value={"OPENAI_API_KEY": "sk-abcdefgh"}),
            patch("api.settings_routes.is_configured", return_value=True),
            patch("api.settings_routes.get_env_path", return_value=MagicMock(__str__=lambda s: "/tmp/.env")),
        ):
            resp = await client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "settings" in data
        assert "is_configured" in data
        assert data["is_configured"] is True

    @pytest.mark.asyncio
    async def test_masks_api_keys(self, client):
        with (
            patch("api.settings_routes.read_settings",
                  return_value={"OPENAI_API_KEY": "sk-abcdefghijklmnop"}),
            patch("api.settings_routes.is_configured", return_value=True),
            patch("api.settings_routes.get_env_path", return_value=MagicMock(__str__=lambda s: "/tmp/.env")),
        ):
            resp = await client.get("/api/settings")
        data = resp.json()
        masked = data["settings"].get("OPENAI_API_KEY", "")
        assert "****" in masked
        assert masked != "sk-abcdefghijklmnop"

    @pytest.mark.asyncio
    async def test_empty_settings(self, client):
        with (
            patch("api.settings_routes.read_settings", return_value={}),
            patch("api.settings_routes.is_configured", return_value=False),
            patch("api.settings_routes.get_env_path", return_value=MagicMock(__str__=lambda s: "/tmp/.env")),
        ):
            resp = await client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_configured"] is False


# ── POST /api/settings ────────────────────────────────────────────────────────

class TestSaveSettings:
    @pytest.mark.asyncio
    async def test_saves_api_key(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post("/api/settings", json={"openai_api_key": "sk-newkey"})
        assert resp.status_code == 204
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0][0]
        assert "OPENAI_API_KEY" in call_args
        assert call_args["OPENAI_API_KEY"] == "sk-newkey"

    @pytest.mark.asyncio
    async def test_skips_empty_fields(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post("/api/settings", json={
                "openai_api_key": "",
                "serper_api_key": "serp-valid",
            })
        assert resp.status_code == 204
        call_args = mock_update.call_args[0][0]
        assert "OPENAI_API_KEY" not in call_args
        assert "SERPER_API_KEY" in call_args

    @pytest.mark.asyncio
    async def test_skips_masked_values(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post("/api/settings", json={
                "openai_api_key": "sk-a****bcde",  # masked
            })
        assert resp.status_code == 204
        # update_settings should not be called for masked values
        if mock_update.called:
            call_args = mock_update.call_args[0][0]
            assert "OPENAI_API_KEY" not in call_args

    @pytest.mark.asyncio
    async def test_updates_os_environ(self, client):
        original = os.environ.get("SERPER_API_KEY", "")
        with (
            patch("api.settings_routes.update_settings"),
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post("/api/settings", json={"serper_api_key": "serp-env-test"})
        assert resp.status_code == 204
        # Restore
        if original:
            os.environ["SERPER_API_KEY"] = original
        elif "SERPER_API_KEY" in os.environ:
            del os.environ["SERPER_API_KEY"]

    @pytest.mark.asyncio
    async def test_saves_smtp_fields(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post("/api/settings", json={
                "email_from_address": "sales@example.com",
                "email_smtp_host": "smtp.example.com",
                "email_smtp_port": "587",
                "email_smtp_username": "sales@example.com",
                "email_smtp_password": "secret",
                "email_use_tls": "true",
            })
        assert resp.status_code == 204
        call_args = mock_update.call_args[0][0]
        assert call_args["EMAIL_FROM_ADDRESS"] == "sales@example.com"
        assert call_args["EMAIL_SMTP_HOST"] == "smtp.example.com"
        assert call_args["EMAIL_SMTP_PORT"] == "587"
        assert call_args["EMAIL_SMTP_USERNAME"] == "sales@example.com"
        assert call_args["EMAIL_SMTP_PASSWORD"] == "secret"
        assert call_args["EMAIL_USE_TLS"] == "true"


class TestEmailSettings:
    @pytest.mark.asyncio
    async def test_smtp_test_success(self, client):
        with (
            patch("api.settings_routes.get_settings") as mock_gs,
            patch("api.settings_routes.test_smtp_connection", return_value={
                "host": "smtp.example.com",
                "username": "sales@example.com",
            }),
        ):
            mock_gs.cache_clear = MagicMock()
            mock_gs.return_value = MagicMock()
            resp = await client.post("/api/settings/email/test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["host"] == "smtp.example.com"

    @pytest.mark.asyncio
    async def test_smtp_test_failure(self, client):
        with (
            patch("api.settings_routes.get_settings") as mock_gs,
            patch("api.settings_routes.test_smtp_connection", side_effect=ValueError("Missing SMTP settings")),
        ):
            mock_gs.cache_clear = MagicMock()
            mock_gs.return_value = MagicMock()
            resp = await client.post("/api/settings/email/test")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_imap_test_success(self, client):
        with (
            patch("api.settings_routes.get_settings") as mock_gs,
            patch("api.settings_routes.test_imap_connection", return_value={
                "host": "imap.example.com",
                "username": "sales@example.com",
            }),
        ):
            mock_gs.cache_clear = MagicMock()
            mock_gs.return_value = MagicMock()
            resp = await client.post("/api/settings/email/imap-test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["host"] == "imap.example.com"


# ── GET /api/settings/license/status ─────────────────────────────────────────

class TestLicenseStatus:
    @pytest.mark.asyncio
    async def test_valid_license(self, client):
        result = LicenseResult(
            LicenseStatus.VALID, "License valid.", plan="personal",
            customer_name="Alice", expires_at=None,
        )
        with patch("api.settings_routes._get_validator") as mock_v:
            validator = AsyncMock()
            validator.check = AsyncMock(return_value=result)
            mock_v.return_value = validator
            resp = await client.get("/api/settings/license/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "valid"
        assert data["plan"] == "personal"
        assert data["customer_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_not_activated(self, client):
        result = LicenseResult(LicenseStatus.NOT_ACTIVATED, "No license activated.")
        with patch("api.settings_routes._get_validator") as mock_v:
            validator = AsyncMock()
            validator.check = AsyncMock(return_value=result)
            mock_v.return_value = validator
            resp = await client.get("/api/settings/license/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_activated"


# ── POST /api/settings/license/activate ──────────────────────────────────────

class TestLicenseActivate:
    @pytest.mark.asyncio
    async def test_successful_activation(self, client):
        result = LicenseResult(
            LicenseStatus.VALID, "License activated successfully.",
            plan="personal", customer_name="Bob",
        )
        with patch("api.settings_routes._get_validator") as mock_v:
            validator = AsyncMock()
            validator.activate = AsyncMock(return_value=result)
            mock_v.return_value = validator
            resp = await client.post("/api/settings/license/activate", json={
                "license_key": "AIHNT-12345-12345-12345-12345",
                "machine_label": "MacBook Pro",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "valid"

    @pytest.mark.asyncio
    async def test_empty_key_returns_400(self, client):
        resp = await client.post("/api/settings/license/activate", json={
            "license_key": "",
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_device_limit_returns_403(self, client):
        result = LicenseResult(LicenseStatus.DEVICE_LIMIT, "Device limit reached.")
        with patch("api.settings_routes._get_validator") as mock_v:
            validator = AsyncMock()
            validator.activate = AsyncMock(return_value=result)
            mock_v.return_value = validator
            resp = await client.post("/api/settings/license/activate", json={
                "license_key": "AIHNT-12345-12345-12345-12345",
            })
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_key_returns_403(self, client):
        result = LicenseResult(LicenseStatus.INVALID, "Invalid license key.")
        with patch("api.settings_routes._get_validator") as mock_v:
            validator = AsyncMock()
            validator.activate = AsyncMock(return_value=result)
            mock_v.return_value = validator
            resp = await client.post("/api/settings/license/activate", json={
                "license_key": "AIHNT-WRONG-WRONG-WRONG-WRONG",
            })
        assert resp.status_code == 403


# ── POST /api/settings/license/deactivate ────────────────────────────────────

class TestLicenseDeactivate:
    @pytest.mark.asyncio
    async def test_deactivate_success(self, client):
        with patch("api.settings_routes._get_validator") as mock_v:
            validator = AsyncMock()
            validator.deactivate = AsyncMock(return_value=True)
            mock_v.return_value = validator
            resp = await client.post("/api/settings/license/deactivate")
        assert resp.status_code == 204


# ── _mask helper ──────────────────────────────────────────────────────────────

class TestMaskHelper:
    def test_masks_long_value(self):
        from api.settings_routes import _mask
        result = _mask("sk-abcdefghijklmnop")
        assert "****" in result
        assert result.startswith("sk-a")
        assert result.endswith("mnop")

    def test_short_value_not_masked(self):
        from api.settings_routes import _mask
        assert _mask("short") == "short"

    def test_empty_not_masked(self):
        from api.settings_routes import _mask
        assert _mask("") == ""

    def test_is_masked_detection(self):
        from api.settings_routes import _is_masked
        assert _is_masked("sk-a****bcde") is True
        assert _is_masked("sk-fullkeyhere") is False
