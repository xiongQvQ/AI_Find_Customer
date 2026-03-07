"""Live integration tests against https://license.b2binsights.io

These tests make real HTTP calls to the production license server.
Run them explicitly:

    pytest tests/test_license/test_integration_live.py -v -s

They are excluded from the normal test suite via the `live` mark.
"""

from __future__ import annotations

import asyncio
import pytest

from license.fingerprint import get_machine_id
from license.validator import LicenseResult, LicenseStatus, LicenseValidator
from license.token_store import clear_token, load_token

SERVER_URL = "https://aihunter-license-worker.xiongbojian007.workers.dev"
REAL_LICENSE_KEY = "AIHNT-3T5HZ-ZYGRP-MTLLQ-E3375"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.mark.live
class TestLiveActivation:
    def setup_method(self):
        """Clear any stored token before each test."""
        clear_token()

    def teardown_method(self):
        """Leave token in place after bind so subsequent tests can use it."""
        pass

    def test_machine_id_is_valid(self):
        mid = get_machine_id()
        assert isinstance(mid, str)
        assert len(mid) == 32
        assert all(c in "0123456789abcdef" for c in mid)
        print(f"\n  machine_id = {mid}")

    def test_bind_real_license(self):
        """POST /api/v1/bind — bind this machine to the real license key."""
        v = LicenseValidator(SERVER_URL)
        result = _run(v.activate(REAL_LICENSE_KEY, machine_label="integration-test"))
        print(f"\n  status       = {result.status}")
        print(f"  plan         = {result.plan}")
        print(f"  customer     = {result.customer_name}")
        print(f"  is_allowed   = {result.is_allowed}")
        print(f"  message      = {result.message}")

        # Either valid (first bind) or already_bound to this same machine (re-run)
        assert result.status in (LicenseStatus.VALID, LicenseStatus.DEVICE_LIMIT), (
            f"Unexpected status: {result.status} — {result.message}"
        )

    def test_bind_then_token_stored(self):
        """After successful bind, token must be saved locally."""
        v = LicenseValidator(SERVER_URL)
        result = _run(v.activate(REAL_LICENSE_KEY, machine_label="integration-test"))

        if result.status == LicenseStatus.VALID:
            data = load_token()
            assert data is not None, "Token should be stored after activation"
            assert data.get("token"), "Token string should be non-empty"
            print(f"\n  token stored, expires_at = {data.get('expires_at')}")
        else:
            # Already bound to this machine — still ok
            print(f"\n  status={result.status}, skipping token check")

    def test_check_after_bind(self):
        """check() uses stored token — must return VALID after bind."""
        v = LicenseValidator(SERVER_URL)
        # First activate
        act_result = _run(v.activate(REAL_LICENSE_KEY, machine_label="integration-test"))
        if not act_result.is_allowed:
            pytest.skip(f"Activation not allowed: {act_result.status} — {act_result.message}")

        # Now check
        check_result = _run(v.check())
        print(f"\n  check status = {check_result.status}")
        assert check_result.is_allowed, f"check() returned {check_result.status}: {check_result.message}"

    def test_validate_with_token(self):
        """POST /api/v1/validate with token — server-side online check."""
        v = LicenseValidator(SERVER_URL)
        act = _run(v.activate(REAL_LICENSE_KEY, machine_label="integration-test"))
        if not act.is_allowed:
            pytest.skip(f"Activation not allowed: {act.status}")

        data = load_token()
        assert data is not None
        token = data["token"]

        import httpx, asyncio
        async def _validate():
            async with httpx.AsyncClient(timeout=10) as client:
                return await client.post(
                    f"{SERVER_URL}/api/v1/validate",
                    json={"token": token},
                )
        resp = asyncio.get_event_loop().run_until_complete(_validate())
        print(f"\n  validate status_code = {resp.status_code}")
        print(f"  validate body        = {resp.json()}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "valid"

    def test_validate_with_key_and_machine(self):
        """POST /api/v1/validate with license_key + machine_id (legacy path B)."""
        import httpx, asyncio
        machine_id = get_machine_id()
        async def _validate():
            async with httpx.AsyncClient(timeout=10) as client:
                return await client.post(
                    f"{SERVER_URL}/api/v1/validate",
                    json={"license_key": REAL_LICENSE_KEY, "machine_id": machine_id},
                )
        resp = asyncio.get_event_loop().run_until_complete(_validate())
        print(f"\n  validate(key+machine) status_code = {resp.status_code}")
        print(f"  body = {resp.json()}")
        # Valid if bound to this machine, machine_mismatch if bound to another
        assert resp.status_code in (200, 403)
        body = resp.json()
        assert body.get("status") in ("valid", "machine_mismatch", "not_activated")

    def test_invalid_key_returns_invalid(self):
        """A bad key format should return INVALID."""
        v = LicenseValidator(SERVER_URL)
        result = _run(v.activate("AIHNT-XXXXX-XXXXX-XXXXX-XXXXX"))
        print(f"\n  bad key status = {result.status}: {result.message}")
        assert result.status == LicenseStatus.INVALID

    def test_deactivate_then_reactivate(self):
        """Unbind then re-bind on same machine — full lifecycle."""
        v = LicenseValidator(SERVER_URL)
        # Bind
        act = _run(v.activate(REAL_LICENSE_KEY, machine_label="lifecycle-test"))
        if not act.is_allowed:
            pytest.skip(f"Cannot bind: {act.status}")

        # Deactivate
        ok = _run(v.deactivate())
        assert ok is True
        assert load_token() is None, "Token should be cleared after deactivate"
        print("\n  deactivated OK")

        # Re-bind
        react = _run(v.activate(REAL_LICENSE_KEY, machine_label="lifecycle-retest"))
        print(f"  re-bind status = {react.status}: {react.message}")
        assert react.is_allowed, f"Re-activation failed: {react.status} — {react.message}"
