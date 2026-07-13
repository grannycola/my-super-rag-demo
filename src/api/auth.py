"""Admin API key authentication."""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from src.config import get_config

admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin_key(key: str | None = Security(admin_key_header)) -> None:
    expected = get_config().admin_api_key
    if not expected:
        raise HTTPException(status_code=503, detail="Admin API key is not configured")
    if key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")
