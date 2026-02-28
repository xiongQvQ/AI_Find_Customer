"""Tests for license/token_store.py"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from license.token_store import (
    _derive_key,
    clear_token,
    is_token_valid_offline,
    load_token,
    save_token,
)

FAKE_MACHINE_ID = "deadbeefdeadbeef12345678deadbeef"
FAKE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.test.token"


@pytest.fixture(autouse=True)
def isolated_token_path(tmp_path):
    """Redirect token storage to a temp dir so tests don't touch real disk."""
    token_file = tmp_path / ".aihunter_license"
    with (
        patch("license.token_store._get_token_path", return_value=token_file),
        patch("license.token_store.get_machine_id", return_value=FAKE_MACHINE_ID),
        patch("license.fingerprint.get_machine_id", return_value=FAKE_MACHINE_ID),
    ):
        yield token_file


class TestDeriveKey:
    def test_returns_fernet_compatible_bytes(self):
        key = _derive_key(FAKE_MACHINE_ID)
        assert isinstance(key, bytes)
        assert len(key) == 44  # base64url-encoded 32 bytes

    def test_deterministic(self):
        assert _derive_key(FAKE_MACHINE_ID) == _derive_key(FAKE_MACHINE_ID)

    def test_different_machine_ids_give_different_keys(self):
        k1 = _derive_key("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        k2 = _derive_key("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
        assert k1 != k2


class TestSaveAndLoadToken:
    def test_round_trip(self):
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        save_token(FAKE_TOKEN, expires)
        data = load_token()
        assert data is not None
        assert data["token"] == FAKE_TOKEN
        assert data["machine_id"] == FAKE_MACHINE_ID

    def test_load_returns_none_when_no_file(self, isolated_token_path):
        assert not isolated_token_path.exists()
        assert load_token() is None

    def test_load_returns_none_on_tampered_file(self, isolated_token_path):
        isolated_token_path.write_bytes(b"not-encrypted-data")
        assert load_token() is None

    def test_load_returns_none_on_machine_id_mismatch(self, isolated_token_path):
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        save_token(FAKE_TOKEN, expires)
        # Simulate loading on a different machine
        with patch("license.token_store.get_machine_id", return_value="different" + "0" * 24):
            result = load_token()
        assert result is None

    def test_expires_at_preserved(self):
        expires = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        save_token(FAKE_TOKEN, expires)
        data = load_token()
        assert data is not None
        assert "2026-06-15" in data["expires_at"]


class TestClearToken:
    def test_clear_removes_file(self, isolated_token_path):
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        save_token(FAKE_TOKEN, expires)
        assert isolated_token_path.exists()
        clear_token()
        assert not isolated_token_path.exists()

    def test_clear_on_missing_file_is_noop(self, isolated_token_path):
        assert not isolated_token_path.exists()
        clear_token()  # should not raise


class TestIsTokenValidOffline:
    def test_valid_token_returns_true(self):
        expires = datetime.now(timezone.utc) + timedelta(days=3)
        save_token(FAKE_TOKEN, expires)
        assert is_token_valid_offline() is True

    def test_expired_token_returns_false(self):
        expires = datetime.now(timezone.utc) - timedelta(seconds=1)
        save_token(FAKE_TOKEN, expires)
        assert is_token_valid_offline() is False

    def test_no_token_returns_false(self):
        assert is_token_valid_offline() is False
