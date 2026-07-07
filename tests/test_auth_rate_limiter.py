from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes.auth import SigninRequest, signin
from app.config import settings
from app.services.auth_rate_limiter import AuthRateLimiter


class DummyRequest:
    def __init__(self, host: str = "203.0.113.10", headers=None):
        self.client = SimpleNamespace(host=host)
        self.headers = headers or {}


@pytest.fixture(autouse=True)
def configure_auth_rate_limits(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_IP_REQUESTS", 10)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_IP_WINDOW_SECONDS", 60)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_EMAIL_REQUESTS", 2)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_EMAIL_WINDOW_SECONDS", 900)


@pytest.mark.asyncio
async def test_auth_rate_limit_persists_across_service_instances(fake_db):
    request = DummyRequest()
    email = "User@Example.com"

    limiter = AuthRateLimiter(fake_db)
    await limiter.enforce_auth_limit(request=request, action="password", email=email)
    await limiter.enforce_auth_limit(request=request, action="password", email=email)

    restarted_limiter = AuthRateLimiter(fake_db)
    with pytest.raises(HTTPException) as exc:
        await restarted_limiter.enforce_auth_limit(request=request, action="password", email=email)

    assert exc.value.status_code == 429
    assert exc.value.headers["Retry-After"] == str(settings.AUTH_RATE_LIMIT_EMAIL_WINDOW_SECONDS)
    stored_attempts = await fake_db.get_collection("auth_rate_limits").count_documents(
        {"scope": "auth:password:email", "key": "user@example.com"}
    )
    assert stored_attempts == settings.AUTH_RATE_LIMIT_EMAIL_REQUESTS


@pytest.mark.asyncio
async def test_signin_route_rate_limits_repeated_email_attempts(fake_db):
    request = DummyRequest()
    payload = SigninRequest(email="User@Example.com", password="wrong-password")

    for _ in range(settings.AUTH_RATE_LIMIT_EMAIL_REQUESTS):
        with pytest.raises(HTTPException) as exc:
            await signin(request, payload, fake_db)
        assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        await signin(request, payload, fake_db)

    assert exc.value.status_code == 429
    assert exc.value.detail == "Too many authentication attempts. Please retry later."
