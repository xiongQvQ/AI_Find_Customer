"""License validator for AIHunter desktop app.

Talks to the license-server-v2 (Hono/Cloudflare Worker) at
https://license.b2binsights.io/api/v1.

Endpoints used:
  POST /api/v1/bind     – bind this machine to a license key (activation)
  POST /api/v1/validate – verify token or license_key+machine_id
  POST /api/v1/unbind   – unbind this machine (device transfer)
"""

from __future__ import annotations

import enum
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from license.fingerprint import get_machine_id
from license.token_store import clear_token, is_token_valid_offline, load_token, save_token

_NEAR_EXPIRY_DAYS = 2
_REQUEST_TIMEOUT = 10.0


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string to a timezone-aware datetime."""
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class LicenseStatus(str, enum.Enum):
    VALID = "valid"
    VALID_OFFLINE = "valid_offline"
    NOT_ACTIVATED = "not_activated"
    INVALID = "invalid"
    EXPIRED = "expired"
    DEVICE_LIMIT = "device_limit"
    SERVER_ERROR = "server_error"


class LicenseResult:
    def __init__(
        self,
        status: LicenseStatus,
        message: str = "",
        plan: str = "",
        customer_name: str = "",
        expires_at: datetime | None = None,
    ) -> None:
        self.status = status
        self.message = message
        self.plan = plan
        self.customer_name = customer_name
        self.expires_at = expires_at

    @property
    def is_allowed(self) -> bool:
        return self.status in (LicenseStatus.VALID, LicenseStatus.VALID_OFFLINE)


class LicenseValidator:
    def __init__(self, server_url: str) -> None:
        # Normalise: strip trailing slash
        self._base = server_url.rstrip("/")

    # ── public API ────────────────────────────────────────────────────────────

    async def check(self) -> LicenseResult:
        """Check current license status using stored token."""
        data = load_token()
        if data is None:
            return LicenseResult(LicenseStatus.NOT_ACTIVATED, "No license activated.")

        try:
            expires_at = _parse_dt(data["expires_at"])
        except Exception:
            clear_token()
            return LicenseResult(LicenseStatus.INVALID, "Stored token is corrupted.")

        now = datetime.now(timezone.utc)
        token_expired = expires_at <= now
        near_expiry = expires_at <= now + timedelta(days=_NEAR_EXPIRY_DAYS)

        if not token_expired and not near_expiry:
            # Token still fresh — no network call needed
            return LicenseResult(
                LicenseStatus.VALID,
                "License is valid.",
                plan=data.get("plan", ""),
                customer_name=data.get("customer_name", ""),
                expires_at=data.get("license_expires_at") and _parse_dt(data["license_expires_at"]),
            )

        # Token expired or near-expiry — try server refresh via /validate
        machine_id = get_machine_id()
        token = data.get("token", "")
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._base}/api/v1/validate",
                    json={"token": token},
                )
            if resp.status_code == 200:
                body = resp.json()
                # Server may return a refreshed token
                new_token = body.get("token") or token
                new_exp_raw = body.get("token_expires_at") or body.get("expires_at")
                if new_exp_raw:
                    new_exp = _parse_dt(new_exp_raw)
                    save_token(new_token, new_exp)
                return LicenseResult(
                    LicenseStatus.VALID,
                    "License is valid.",
                    plan=body.get("plan", data.get("plan", "")),
                    customer_name=body.get("customer_name", data.get("customer_name", "")),
                    expires_at=body.get("license_expires_at") and _parse_dt(body["license_expires_at"]),
                )
        except httpx.HTTPError:
            pass

        # Network failed
        if token_expired:
            return LicenseResult(LicenseStatus.EXPIRED, "License token has expired and could not be refreshed.")
        # Near-expiry but offline — still usable
        return LicenseResult(
            LicenseStatus.VALID_OFFLINE,
            "Offline mode — token will expire soon.",
            plan=data.get("plan", ""),
            customer_name=data.get("customer_name", ""),
        )

    async def activate(self, license_key: str, machine_label: str = "") -> LicenseResult:
        """Bind this machine to the given license key."""
        machine_id = get_machine_id()
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._base}/api/v1/bind",
                    json={
                        "license_key": license_key.strip().upper(),
                        "machine_id": machine_id,
                        "machine_label": machine_label or "",
                    },
                )
        except httpx.HTTPError as exc:
            return LicenseResult(LicenseStatus.SERVER_ERROR, f"Could not reach license server: {exc}")

        if resp.status_code in (200, 201):
            body = resp.json()
            token = body.get("token", "")
            exp_raw = body.get("token_expires_at") or body.get("expires_at")
            if token and exp_raw:
                exp = _parse_dt(exp_raw)
                save_token(token, exp)
                # Persist extra fields alongside the token for offline use
                import json as _json
                from license.token_store import _get_token_path, _derive_key, get_machine_id as _mid
                from cryptography.fernet import Fernet
                _machine_id = _mid()
                _key = _derive_key(_machine_id)
                _f = Fernet(_key)
                _payload = _json.dumps({
                    "token": token,
                    "expires_at": exp.isoformat(),
                    "machine_id": _machine_id,
                    "plan": body.get("plan", ""),
                    "customer_name": body.get("customer_name", ""),
                    "license_expires_at": body.get("license_expires_at"),
                }).encode()
                _get_token_path().write_bytes(_f.encrypt(_payload))

            lic_exp = body.get("license_expires_at") or body.get("expires_at")
            return LicenseResult(
                LicenseStatus.VALID,
                body.get("message", "License activated successfully."),
                plan=body.get("plan", ""),
                customer_name=body.get("customer_name", ""),
                expires_at=_parse_dt(lic_exp) if lic_exp else None,
            )

        body = {}
        try:
            body = resp.json()
        except Exception:
            pass

        status_field = body.get("status", "")
        detail = body.get("message") or body.get("detail") or body.get("error") or ""

        if resp.status_code == 404 or status_field == "not_found":
            return LicenseResult(LicenseStatus.INVALID, detail or "License key not found.")
        if status_field in ("already_bound", "device_limit") or "device limit" in detail.lower():
            return LicenseResult(LicenseStatus.DEVICE_LIMIT, detail or "License is already bound to another machine.")
        if status_field == "expired" or (detail and "expired" in detail.lower()):
            return LicenseResult(LicenseStatus.EXPIRED, detail or "License has expired.")
        if status_field in ("revoked", "suspended"):
            return LicenseResult(LicenseStatus.INVALID, detail or f"License is {status_field}.")
        return LicenseResult(LicenseStatus.INVALID, detail or f"Activation failed (HTTP {resp.status_code}).")

    async def deactivate(self) -> bool:
        """Unbind this machine from its license. Always clears local token."""
        data = load_token()
        if data is None:
            return False

        machine_id = get_machine_id()
        token = data.get("token", "")
        # We need the license_key to call /unbind.
        # It is embedded in the JWT payload (lic claim) but we avoid JWT parsing here.
        # Fall back to the stored license_key if present.
        license_key = data.get("license_key", "")

        try:
            if license_key:
                async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                    await client.post(
                        f"{self._base}/api/v1/unbind",
                        json={"license_key": license_key, "machine_id": machine_id},
                    )
        except httpx.HTTPError:
            pass  # Always clear local token regardless

        clear_token()
        return True
