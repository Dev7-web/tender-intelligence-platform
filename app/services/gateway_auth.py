"""
Central auth gateway client for Tender Matching AI.

Proxies email/password login and refresh-token exchange to the company auth
gateway (``auth.nervesparks.com``). Ported from
``main-dashboard/backend/service/auth_service.py`` (the gateway-facing parts).

Token verification lives in ``app.utils.jwt_auth``; the Mongo user profile
upsert lives in ``app.api.dependencies.sync_user_from_claims``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def _gateway_url(path: str) -> str:
    base = settings.AUTH_GATEWAY_BASE_URL.rstrip("/")
    prefix = settings.AUTH_GATEWAY_PREFIX.strip("/")
    clean_path = path.lstrip("/")
    return f"{base}/{prefix}/{clean_path}"


def _extract_tokens(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The gateway wraps its payload as {"data": {...}} on some deployments."""
    tokens = data.get("data") or data
    token = tokens.get("access_token") or tokens.get("id_token")
    if not token:
        return None
    return {
        "id_token": token,
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens.get("expires_in"),
    }


def gateway_login(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Login via the auth gateway. Returns tokens dict or None on failure."""
    try:
        response = requests.post(
            _gateway_url("/login"),
            json={"email": email, "password": password},
            timeout=20,
        )
        response.raise_for_status()
        return _extract_tokens(response.json() or {})
    except requests.exceptions.RequestException as exc:
        logger.error("Auth gateway login error: %s", exc, exc_info=True)
        return None
    except Exception as exc:  # noqa: BLE001 - defensive, mirror main-dashboard
        logger.error("Login error: %s", exc, exc_info=True)
        return None


def gateway_refresh(refresh_token: str) -> Optional[Dict[str, Any]]:
    """Exchange a refresh token for a fresh access token via the auth gateway."""
    try:
        response = requests.post(
            _gateway_url("/refresh"),
            json={"refresh_token": refresh_token},
            timeout=20,
        )
        response.raise_for_status()
        return _extract_tokens(response.json() or {})
    except requests.exceptions.RequestException as exc:
        logger.error("Auth gateway refresh error: %s", exc, exc_info=True)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("Refresh token error: %s", exc, exc_info=True)
        return None
