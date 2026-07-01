"""
Central auth gateway JWT verification utilities.

Ported from `main-dashboard/backend/utils/jwt_auth.py` so that Tender Matching AI
uses the same company-wide auth gateway (JWKS / RS256) instead of Firebase.

The only change vs. the main-dashboard original is the settings import path
(`app.config` instead of `core.config`).
"""
import logging
import time
from typing import Any, Dict, Optional

import requests
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

_JWKS_CACHE: dict[str, Any] = {"keys": [], "expires_at": 0.0}
_JWKS_CACHE_TTL_SECONDS = 300


def _resolve_jwks_url() -> str:
    if settings.AUTH_JWKS_URL:
        return settings.AUTH_JWKS_URL
    base = settings.AUTH_GATEWAY_BASE_URL.rstrip("/")
    prefix = settings.AUTH_GATEWAY_PREFIX.strip("/")
    return f"{base}/{prefix}/.well-known/jwks.json"


def _resolve_issuer() -> str:
    """
    Kept for backwards compatibility.
    Current verification intentionally does not enforce issuer,
    because different gateway deployments may use different `iss` values.
    """
    base = settings.AUTH_GATEWAY_BASE_URL.rstrip("/")
    prefix = settings.AUTH_GATEWAY_PREFIX.strip("/")
    return f"{base}/{prefix}"


def _fetch_jwks() -> list[dict[str, Any]]:
    now = time.time()
    if _JWKS_CACHE["keys"] and _JWKS_CACHE["expires_at"] > now:
        return _JWKS_CACHE["keys"]

    response = requests.get(_resolve_jwks_url(), timeout=10)
    response.raise_for_status()
    payload = response.json()
    # Auth gateway wraps payload as:
    # { "status_code": 200, "data": { "keys": [...] } }
    # Some deployments may return plain JWKS as { "keys": [...] }.
    keys = payload.get("keys") or payload.get("data", {}).get("keys") or []
    _JWKS_CACHE["keys"] = keys
    _JWKS_CACHE["expires_at"] = now + _JWKS_CACHE_TTL_SECONDS
    return keys


def verify_auth_gateway_token(token: str) -> Optional[Dict[str, Any]]:
    if not token or not isinstance(token, str) or not token.strip():
        return None

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        keys = _fetch_jwks()
        signing_key = next((key for key in keys if key.get("kid") == kid), None)
        if not signing_key:
            return None

        decoded = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )

        return decoded
    except (JWTError, requests.RequestException, ValueError) as exc:
        logger.error("Auth gateway token verification failed: %s", exc)
        return None
