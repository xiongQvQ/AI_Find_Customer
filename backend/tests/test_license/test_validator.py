"""Tests for license/validator.py — LicenseValidator with mocked HTTP and token store."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from license.validator import LicenseResult, LicenseStatus, LicenseValidator, _parse_dt

FAKE_MACHINE_ID = "deadbeefdeadbeef12345678deadbeef"
FAKE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.test.sig"
SERVER_URL = "https://license.aihunter.app"


# ── _parse_dt ─────────────────────────────────────────────────────────────────

class TestParseDt:
    def test_iso_with_offset(self):
        dt = _parse_dt("2026-01-15T12:00:00+00:00")
        assert dt.tzinfo is not None
        assert dt.year == 2026

    def test_z_suffix(self):
        dt = _parse_dt("2026-01-15T12:00:00Z")
        assert dt.tzinfo is not None
        assert dt.year == 2026

    def test_naive_gets_utc(self):
        dt = _parse_dt("2026-01-15T12:00:00")
        assert dt.tzinfo == timezone.utc

    def test_strips_whitespace(self):
        dt = _parse_dt("  2026-01-15T12:00:00Z  ")
        assert dt.year == 2026


# ── Helpers ───────────────────────────────────────────────────────────────────

def _future(days: int = 7) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


def _past(days: int = 1) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _make_token_data(expires_at: datetime) -> dict:
    return {"token": FAKE_TOKEN, "expires_at": expires_at.isoformat(), "machine_id": FAKE_MACHINE_ID}


@pytest.fixture(autouse=True)
def mock_machine_id():
    with patch("license.validator.get_machine_id", return_value=FAKE_MACHINE_ID):
        yield


# ── LicenseValidator.check ────────────────────────────────────────────────────

class TestCheck:
    def test_no_token_returns_not_activated(self):
        with patch("license.validator.load_token", return_value=None):
            v = LicenseValidator(SERVER_URL)
            result = _run(v.check())
        assert result.status == LicenseStatus.NOT_ACTIVATED

    def test_valid_token_no_refresh_needed(self):
        data = _make_token_data(_future(10))
        with patch("license.validator.load_token", return_value=data):
            v = LicenseValidator(SERVER_URL)
            result = _run(v.check())
        assert result.status == LicenseStatus.VALID

    def test_expired_token_tries_refresh(self):
        data = _make_token_data(_past(1))
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "token": "new-token",
            "expires_at": _future(7).isoformat(),
        }
        with (
            patch("license.validator.load_token", return_value=data),
            patch("license.validator.save_token"),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client
            v = LicenseValidator(SERVER_URL)
            result = _run(v.check())
        assert result.status == LicenseStatus.VALID

    def test_expired_token_no_network_returns_expired(self):
        import httpx
        data = _make_token_data(_past(1))
        with (
            patch("license.validator.load_token", return_value=data),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("no network"))
            mock_client_cls.return_value = mock_client
            v = LicenseValidator(SERVER_URL)
            result = _run(v.check())
        assert result.status == LicenseStatus.EXPIRED

    def test_near_expiry_refresh_fails_offline_mode(self):
        import httpx
        data = _make_token_data(_future(1))  # < 2 days = near expiry
        with (
            patch("license.validator.load_token", return_value=data),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("no network"))
            mock_client_cls.return_value = mock_client
            v = LicenseValidator(SERVER_URL)
            result = _run(v.check())
        assert result.status == LicenseStatus.VALID_OFFLINE

    def test_corrupted_token_data_returns_invalid(self):
        bad_data = {"token": FAKE_TOKEN, "expires_at": "not-a-date", "machine_id": FAKE_MACHINE_ID}
        with (
            patch("license.validator.load_token", return_value=bad_data),
            patch("license.validator.clear_token"),
        ):
            v = LicenseValidator(SERVER_URL)
            result = _run(v.check())
        assert result.status == LicenseStatus.INVALID


# ── LicenseValidator.activate ────────────────────────────────────────────────

class TestActivate:
    def _make_activate_resp(self, status_code: int, body: dict) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = body
        return resp

    def _patched_client(self, resp):
        from unittest.mock import AsyncMock, patch
        import httpx
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=resp)
        return mock_client

    def test_successful_activation(self):
        resp = self._make_activate_resp(200, {
            "token": "new-token",
            "expires_at": _future(7).isoformat(),
            "plan": "personal",
            "customer_name": "Test User",
        })
        with (
            patch("license.validator.save_token"),
            patch("httpx.AsyncClient") as mock_cls,
        ):
            mock_cls.return_value = self._patched_client(resp)
            v = LicenseValidator(SERVER_URL)
            result = _run(v.activate("AIHNT-12345-12345-12345-12345"))
        assert result.status == LicenseStatus.VALID
        assert result.plan == "personal"
        assert result.customer_name == "Test User"

    def test_invalid_key_404(self):
        resp = self._make_activate_resp(404, {"detail": "License key not found"})
        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value = self._patched_client(resp)
            v = LicenseValidator(SERVER_URL)
            result = _run(v.activate("AIHNT-WRONG-KEY"))
        assert result.status == LicenseStatus.INVALID

    def test_device_limit_403(self):
        resp = self._make_activate_resp(403, {"detail": "Device limit reached (1 device(s) allowed)."})
        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value = self._patched_client(resp)
            v = LicenseValidator(SERVER_URL)
            result = _run(v.activate("AIHNT-12345-12345-12345-12345"))
        assert result.status == LicenseStatus.DEVICE_LIMIT

    def test_disabled_license_403(self):
        resp = self._make_activate_resp(403, {"detail": "License key is disabled"})
        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value = self._patched_client(resp)
            v = LicenseValidator(SERVER_URL)
            result = _run(v.activate("AIHNT-12345-12345-12345-12345"))
        assert result.status == LicenseStatus.INVALID  # not EXPIRED

    def test_expired_license_403(self):
        resp = self._make_activate_resp(403, {"detail": "License key has expired"})
        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value = self._patched_client(resp)
            v = LicenseValidator(SERVER_URL)
            result = _run(v.activate("AIHNT-12345-12345-12345-12345"))
        assert result.status == LicenseStatus.EXPIRED

    def test_network_error_returns_server_error(self):
        import httpx
        with patch("httpx.AsyncClient") as mock_cls:
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=False)
            client.post = AsyncMock(side_effect=httpx.ConnectError("offline"))
            mock_cls.return_value = client
            v = LicenseValidator(SERVER_URL)
            result = _run(v.activate("AIHNT-12345-12345-12345-12345"))
        assert result.status == LicenseStatus.SERVER_ERROR

    def test_z_suffix_expires_at_parsed(self):
        resp = self._make_activate_resp(200, {
            "token": "tok",
            "expires_at": "2026-12-31T00:00:00Z",  # Z-suffix
            "plan": "pro",
            "customer_name": "Alice",
        })
        with (
            patch("license.validator.save_token"),
            patch("httpx.AsyncClient") as mock_cls,
        ):
            mock_cls.return_value = self._patched_client(resp)
            v = LicenseValidator(SERVER_URL)
            result = _run(v.activate("AIHNT-12345-12345-12345-12345"))
        assert result.status == LicenseStatus.VALID
        assert result.expires_at is not None
        assert result.expires_at.tzinfo is not None


# ── LicenseValidator.deactivate ──────────────────────────────────────────────

class TestDeactivate:
    def test_deactivate_success(self):
        data = _make_token_data(_future(7))
        resp = MagicMock()
        resp.status_code = 204
        with (
            patch("license.validator.load_token", return_value=data),
            patch("license.validator.clear_token") as mock_clear,
            patch("httpx.AsyncClient") as mock_cls,
        ):
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=False)
            client.post = AsyncMock(return_value=resp)
            mock_cls.return_value = client
            v = LicenseValidator(SERVER_URL)
            ok = _run(v.deactivate())
        assert ok is True
        mock_clear.assert_called_once()

    def test_deactivate_no_token(self):
        with patch("license.validator.load_token", return_value=None):
            v = LicenseValidator(SERVER_URL)
            ok = _run(v.deactivate())
        assert ok is False

    def test_deactivate_clears_token_even_on_network_error(self):
        import httpx
        data = _make_token_data(_future(7))
        with (
            patch("license.validator.load_token", return_value=data),
            patch("license.validator.clear_token") as mock_clear,
            patch("httpx.AsyncClient") as mock_cls,
        ):
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=False)
            client.post = AsyncMock(side_effect=httpx.ConnectError("offline"))
            mock_cls.return_value = client
            v = LicenseValidator(SERVER_URL)
            _run(v.deactivate())
        mock_clear.assert_called_once()


# ── LicenseResult ────────────────────────────────────────────────────────────

class TestLicenseResult:
    def test_is_allowed_valid(self):
        r = LicenseResult(LicenseStatus.VALID)
        assert r.is_allowed is True

    def test_is_allowed_valid_offline(self):
        r = LicenseResult(LicenseStatus.VALID_OFFLINE)
        assert r.is_allowed is True

    def test_is_allowed_false_for_others(self):
        for s in [LicenseStatus.INVALID, LicenseStatus.NOT_ACTIVATED,
                  LicenseStatus.EXPIRED, LicenseStatus.DEVICE_LIMIT, LicenseStatus.SERVER_ERROR]:
            r = LicenseResult(s)
            assert r.is_allowed is False, f"Expected is_allowed=False for {s}"


# ── Async runner helper ───────────────────────────────────────────────────────

def _run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)
