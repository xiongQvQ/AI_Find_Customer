"""Cryptographic helpers: JWT tokens, license key generation."""

import secrets
import string
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

_KEY_CHARS = string.ascii_uppercase + string.digits
_KEY_CHARS = _KEY_CHARS.replace("O", "").replace("0", "").replace("I", "").replace("1", "")


def generate_license_key(prefix: str = "AIHNT") -> str:
    """Generate a license key like AIHNT-XXXXX-XXXXX-XXXXX-XXXXX."""
    groups = [
        "".join(secrets.choice(_KEY_CHARS) for _ in range(5))
        for _ in range(4)
    ]
    return f"{prefix}-" + "-".join(groups)


def create_device_token(
    license_key: str,
    machine_id: str,
    plan: str,
    ttl_days: int | None = None,
) -> tuple[str, datetime]:
    """Create a signed JWT token for a device. Returns (token, expires_at)."""
    ttl = ttl_days or settings.token_ttl_days
    expires_at = datetime.now(timezone.utc) + timedelta(days=ttl)
    payload = {
        "sub": machine_id,
        "lic": license_key,
        "plan": plan,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def verify_device_token(token: str) -> dict | None:
    """Verify and decode a device token. Returns payload or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def generate_admin_token() -> str:
    """Generate a secure random admin API key."""
    return secrets.token_urlsafe(32)
