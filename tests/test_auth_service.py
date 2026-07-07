from datetime import datetime, timezone

import pytest

from app.config import settings
from app.services.auth_service import AuthService, create_access_token, decode_access_token, verify_password_hash


TEST_JWT_SECRET = "test-jwt-secret-value-that-is-at-least-32-chars"


@pytest.fixture(autouse=True)
def configure_jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", TEST_JWT_SECRET)


def test_create_access_token_rejects_weak_jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "change-me")

    with pytest.raises(ValueError, match="JWT_SECRET must be set"):
        create_access_token("user-id")


@pytest.mark.asyncio
async def test_signup_with_password_creates_user(fake_db):
    service = AuthService(fake_db)

    result = await service.signup_with_password("User@Example.com", "StrongPass1")

    assert result["user"]["email"] == "user@example.com"
    assert "password_hash" not in result["user"]

    payload = decode_access_token(result["token"])
    assert payload is not None
    assert payload["sub"] == result["user"]["id"]

    stored = await fake_db.get_collection("users").find_one({"email": "user@example.com"})
    assert stored is not None
    assert verify_password_hash("StrongPass1", stored["password_hash"])


@pytest.mark.asyncio
async def test_signin_with_password_rejects_wrong_password(fake_db):
    service = AuthService(fake_db)
    await service.signup_with_password("user@example.com", "StrongPass1")

    with pytest.raises(ValueError, match="Invalid email or password"):
        await service.signin_with_password("user@example.com", "wrong-password")


@pytest.mark.asyncio
async def test_signup_upgrades_legacy_otp_user_to_password(fake_db):
    service = AuthService(fake_db)
    users = fake_db.get_collection("users")
    now = datetime.now(timezone.utc)

    await users.insert_one(
        {
            "email": "legacy@example.com",
            "name": "legacy",
            "auth_provider": "email_otp",
            "provider_user_id": None,
            "is_verified": True,
            "company_id": None,
            "created_at": now,
            "updated_at": now,
            "last_login_at": now,
        }
    )

    result = await service.signup_with_password("legacy@example.com", "Upgrade123")

    assert result["user"]["email"] == "legacy@example.com"
    stored = await users.find_one({"email": "legacy@example.com"})
    assert stored is not None
    assert stored["auth_provider"] == "email_password"
    assert verify_password_hash("Upgrade123", stored["password_hash"])


@pytest.mark.asyncio
async def test_signup_rejects_google_linked_email(fake_db):
    service = AuthService(fake_db)
    users = fake_db.get_collection("users")
    now = datetime.now(timezone.utc)

    await users.insert_one(
        {
            "email": "google-user@example.com",
            "name": "google-user",
            "auth_provider": "google",
            "provider_user_id": "google-sub-123",
            "is_verified": True,
            "company_id": None,
            "created_at": now,
            "updated_at": now,
            "last_login_at": now,
        }
    )

    with pytest.raises(ValueError, match="Google"):
        await service.signup_with_password("google-user@example.com", "StrongPass1")
