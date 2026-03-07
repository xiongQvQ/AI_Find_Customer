"""Encrypted token storage using Fernet (AES-128-CBC + HMAC).

The encryption key is derived from the machine ID via PBKDF2 so that
the token file is bound to this machine and cannot be copied verbatim.
"""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from license.fingerprint import get_machine_id

_PBKDF2_SALT = b"aihunter_token_v2"
_PBKDF2_ITERATIONS = 100_000


def _get_token_path() -> Path:
    """Return the path where the encrypted token is stored."""
    import platform
    if getattr(sys, "frozen", False):
        system = platform.system()
        if system == "Darwin":
            base = Path.home() / "Library" / "Application Support" / "AIHunter"
        elif system == "Windows":
            import os
            base = Path(os.environ.get("APPDATA", str(Path.home()))) / "AIHunter"
        else:
            base = Path.home() / ".config" / "AIHunter"
    else:
        base = Path.home() / ".aihunter"
    base.mkdir(parents=True, exist_ok=True)
    return base / ".aihunter_license"


def _derive_key(machine_id: str) -> bytes:
    """Derive a Fernet-compatible 32-byte key from machine_id via PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_PBKDF2_SALT,
        iterations=_PBKDF2_ITERATIONS,
    )
    raw = kdf.derive(machine_id.encode())
    return base64.urlsafe_b64encode(raw)


def save_token(token: str, expires_at: datetime) -> None:
    """Encrypt and persist the token + metadata to disk."""
    machine_id = get_machine_id()
    key = _derive_key(machine_id)
    f = Fernet(key)
    payload = json.dumps({
        "token": token,
        "expires_at": expires_at.isoformat(),
        "machine_id": machine_id,
    }).encode()
    encrypted = f.encrypt(payload)
    _get_token_path().write_bytes(encrypted)


def load_token() -> dict | None:
    """Decrypt and return token data dict, or None if missing/invalid/mismatched."""
    path = _get_token_path()
    if not path.exists():
        return None
    machine_id = get_machine_id()
    key = _derive_key(machine_id)
    f = Fernet(key)
    try:
        raw = f.decrypt(path.read_bytes())
        data = json.loads(raw.decode())
    except (InvalidToken, Exception):
        return None
    if data.get("machine_id") != machine_id:
        return None
    return data


def clear_token() -> None:
    """Remove the token file if it exists."""
    path = _get_token_path()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def is_token_valid_offline() -> bool:
    """Return True if a locally stored token exists and has not expired."""
    data = load_token()
    if not data:
        return False
    try:
        raw_exp = data.get("expires_at", "")
        if raw_exp.endswith("Z"):
            raw_exp = raw_exp[:-1] + "+00:00"
        exp = datetime.fromisoformat(raw_exp)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp > datetime.now(timezone.utc)
    except Exception:
        return False
