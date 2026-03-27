"""Shared API access control helpers."""

from __future__ import annotations

from fastapi import Header, HTTPException, Query, Request, status

from config.settings import get_settings

_LOCAL_HOSTS = {"", "127.0.0.1", "::1", "localhost", "testclient", "test"}


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return token.strip()


def require_api_access(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    api_key: str | None = Query(default=None),
) -> None:
    """Allow localhost access by default; require token for non-local requests when configured."""
    settings = get_settings()
    expected = settings.api_access_token.strip()
    client_host = (request.client.host if request.client else "").strip().lower()

    if not expected:
        if client_host in _LOCAL_HOSTS:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API access is restricted to localhost unless API_ACCESS_TOKEN is configured.",
        )

    provided = x_api_key or api_key or _extract_bearer_token(authorization)
    if provided == expected:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API access token.",
    )
