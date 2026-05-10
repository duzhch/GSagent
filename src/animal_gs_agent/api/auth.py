"""Simple API token authentication for protected routes."""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


def _auth_disabled() -> bool:
    value = os.getenv("ANIMAL_GS_AGENT_API_AUTH_DISABLED", "").strip().lower()
    return value in {"1", "true", "yes"}


def _extract_token(*, x_api_key: str | None, authorization: str | None) -> str:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


def require_api_token(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    if _auth_disabled():
        return

    configured = os.getenv("ANIMAL_GS_AGENT_API_TOKEN", "").strip()
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="api auth token is not configured",
        )

    provided = _extract_token(x_api_key=x_api_key, authorization=authorization)
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing api authentication token",
        )
    if not hmac.compare_digest(provided, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api authentication token",
        )
