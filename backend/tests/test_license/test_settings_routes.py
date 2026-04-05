"""Tests for api/settings_routes.py settings behavior."""

import os
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app


@pytest.fixture
def app(monkeypatch):
    from config.settings import get_settings

    monkeypatch.setenv("SETTINGS_API_ENABLED", "true")
    get_settings.cache_clear()
    app = create_app()
    yield app
    get_settings.cache_clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestGetSettings:
    @pytest.mark.asyncio
    async def test_returns_settings_shape(self, client):
        with (
            patch("api.settings_routes.read_settings", return_value={"OPENAI_API_KEY": "sk-abcdefgh"}),
            patch("api.settings_routes.is_configured", return_value=True),
        ):
            resp = await client.get("/api/settings")

        assert resp.status_code == 200
        data = resp.json()
        assert "settings" in data
        assert "is_configured" in data
        assert "env_path" not in data
        assert data["is_configured"] is True

    @pytest.mark.asyncio
    async def test_masks_all_secret_values(self, client):
        with (
            patch(
                "api.settings_routes.read_settings",
                return_value={
                    "OPENAI_API_KEY": "sk-abcdefghijklmnop",
                    "SERPER_API_KEY": "serper-secret-1234",
                    "JINA_API_KEY": "jina-secret-5678",
                },
            ),
            patch("api.settings_routes.is_configured", return_value=True),
        ):
            resp = await client.get("/api/settings")

        data = resp.json()
        assert data["settings"]["OPENAI_API_KEY"] != "sk-abcdefghijklmnop"
        assert "****" in data["settings"]["SERPER_API_KEY"]
        assert "****" in data["settings"]["JINA_API_KEY"]


class TestSaveSettings:
    @pytest.mark.asyncio
    async def test_saves_search_keys(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post(
                "/api/settings",
                json={
                    "serper_api_key": "serper-live-key",
                    "jina_api_key": "jina-live-key",
                },
            )

        assert resp.status_code == 204
        updates = mock_update.call_args[0][0]
        assert updates["SERPER_API_KEY"] == "serper-live-key"
        assert updates["JINA_API_KEY"] == "jina-live-key"

    @pytest.mark.asyncio
    async def test_skips_masked_values_and_allows_explicit_clears(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post(
                "/api/settings",
                json={
                    "openai_api_key": "sk-a****bcde",
                    "serper_api_key": "",
                    "tavily_api_key": "tvly-valid",
                },
            )

        assert resp.status_code == 204
        updates = mock_update.call_args[0][0]
        assert "OPENAI_API_KEY" not in updates
        assert updates["SERPER_API_KEY"] == ""
        assert updates["TAVILY_API_KEY"] == "tvly-valid"

    @pytest.mark.asyncio
    async def test_updates_os_environ(self, client):
        original_serper = os.environ.get("SERPER_API_KEY")
        original_jina = os.environ.get("JINA_API_KEY")
        try:
            with (
                patch("api.settings_routes.update_settings"),
                patch("api.settings_routes.get_settings") as mock_gs,
            ):
                mock_gs.cache_clear = MagicMock()
                resp = await client.post(
                    "/api/settings",
                    json={
                        "serper_api_key": "serper-env-test",
                        "jina_api_key": "jina-env-test",
                    },
                )

            assert resp.status_code == 204
            assert os.environ["SERPER_API_KEY"] == "serper-env-test"
            assert os.environ["JINA_API_KEY"] == "jina-env-test"
        finally:
            if original_serper is None:
                os.environ.pop("SERPER_API_KEY", None)
            else:
                os.environ["SERPER_API_KEY"] = original_serper
            if original_jina is None:
                os.environ.pop("JINA_API_KEY", None)
            else:
                os.environ["JINA_API_KEY"] = original_jina

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
        assert call_args["EMAIL_SMTP_LAST_TEST_AT"] == ""

    @pytest.mark.asyncio
    async def test_changing_imap_fields_clears_imap_test_timestamp(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post("/api/settings", json={
                "email_imap_host": "imap.example.com",
                "email_imap_port": "993",
            })
        assert resp.status_code == 204
        call_args = mock_update.call_args[0][0]
        assert call_args["EMAIL_IMAP_LAST_TEST_AT"] == ""

    @pytest.mark.asyncio
    async def test_allows_clearing_smtp_fields(self, client):
        with (
            patch("api.settings_routes.update_settings") as mock_update,
            patch("api.settings_routes.get_settings") as mock_gs,
        ):
            mock_gs.cache_clear = MagicMock()
            resp = await client.post("/api/settings", json={
                "email_smtp_password": "",
                "email_from_address": "",
            })
        assert resp.status_code == 204
        call_args = mock_update.call_args[0][0]
        assert call_args["EMAIL_SMTP_PASSWORD"] == ""
        assert call_args["EMAIL_FROM_ADDRESS"] == ""


class TestEmailSettings:
    @pytest.mark.asyncio
    async def test_smtp_test_success(self, client):
        with (
            patch("api.settings_routes.get_settings") as mock_gs,
            patch("api.settings_routes.test_smtp_connection", return_value={
                "host": "smtp.example.com",
                "username": "sales@example.com",
            }),
            patch("api.settings_routes.update_settings") as mock_update,
        ):
            mock_gs.cache_clear = MagicMock()
            mock_gs.return_value = MagicMock()
            resp = await client.post("/api/settings/email/test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["host"] == "smtp.example.com"
        assert "EMAIL_SMTP_LAST_TEST_AT" in mock_update.call_args[0][0]

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
            patch("api.settings_routes.update_settings") as mock_update,
        ):
            mock_gs.cache_clear = MagicMock()
            mock_gs.return_value = MagicMock()
            resp = await client.post("/api/settings/email/imap-test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["host"] == "imap.example.com"
        assert "EMAIL_IMAP_LAST_TEST_AT" in mock_update.call_args[0][0]

    @pytest.mark.asyncio
    async def test_feishu_test_success(self, client):
        with (
            patch("api.settings_routes.get_settings") as mock_gs,
            patch("api.settings_routes.send_feishu_text", return_value={"StatusCode": 0}) as mock_send,
        ):
            mock_gs.cache_clear = MagicMock()
            mock_gs.return_value = MagicMock(automation_feishu_webhook_url="https://open.feishu.test/hook/abc")
            resp = await client.post("/api/settings/automation/feishu-test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["webhook_url"] == "https://open.feishu.test/hook/abc"
        assert mock_send.called

    @pytest.mark.asyncio
    async def test_feishu_test_requires_webhook(self, client):
        with patch("api.settings_routes.get_settings") as mock_gs:
            mock_gs.cache_clear = MagicMock()
            mock_gs.return_value = MagicMock(automation_feishu_webhook_url="")
            resp = await client.post("/api/settings/automation/feishu-test")
        assert resp.status_code == 400


class TestLicenseCompatibility:
    @pytest.mark.asyncio
    async def test_license_status_returns_compatibility_response(self, client):
        resp = await client.get("/api/settings/license/status")

        assert resp.status_code == 200
        assert resp.json() == {
            "status": "valid",
            "message": "License verification has been removed; all features are available.",
            "plan": "lifetime",
            "customer_name": "Local User",
            "expires_at": None,
        }

    @pytest.mark.asyncio
    async def test_license_activate_is_now_a_noop(self, client):
        resp = await client.post(
            "/api/settings/license/activate",
            json={"license_key": "", "machine_label": "dev-machine"},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "valid"

    @pytest.mark.asyncio
    async def test_license_deactivate_is_now_a_noop(self, client):
        resp = await client.post("/api/settings/license/deactivate")

        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_license_save_token_is_now_a_noop(self, client):
        resp = await client.post(
            "/api/settings/license/save-token",
            json={"token": "fake-token", "expires_at": "2099-12-31T00:00:00Z"},
        )

        assert resp.status_code == 204


class TestMaskHelpers:
    def test_masks_long_value(self):
        from api.settings_routes import _mask

        result = _mask("sk-abcdefghijklmnop")
        assert "****" in result
        assert result.startswith("sk-a")
        assert result.endswith("mnop")

    def test_short_value_not_masked(self):
        from api.settings_routes import _mask

        assert _mask("short") == "short"

    def test_is_masked_detection(self):
        from api.settings_routes import _is_masked

        assert _is_masked("sk-a****bcde") is True
        assert _is_masked("sk-fullkeyhere") is False
