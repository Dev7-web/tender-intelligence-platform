"""
Authentication API routes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user, get_db, sync_user_from_claims
from app.config import settings
from app.services.auth_service import AuthService
from app.services.gateway_auth import gateway_login, gateway_refresh
from app.utils.jwt_auth import verify_auth_gateway_token

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Central auth gateway (login / refresh) ──────────────────────────────
# Mirrors main-dashboard: the frontend posts email/password here, the backend
# proxies to the auth gateway and returns id_token + refresh_token + user.
class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str


async def _tokens_to_response(tokens: Dict[str, Any], db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Verify the freshly-issued gateway token and sync the Mongo user profile."""
    claims = verify_auth_gateway_token(tokens["id_token"])
    user = await sync_user_from_claims(db, claims) if claims else None
    return {
        "id_token": tokens["id_token"],
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens.get("expires_in"),
        "user": user,
    }


@router.post("/login", response_model=Dict[str, Any])
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    tokens = gateway_login(payload.email.strip().lower(), payload.password)
    if not tokens or not tokens.get("id_token"):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return await _tokens_to_response(tokens, db)


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh(payload: RefreshRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    tokens = gateway_refresh(payload.refresh_token)
    if not tokens or not tokens.get("id_token"):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return await _tokens_to_response(tokens, db)


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)
    name: Optional[str] = None


class SigninRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=256)


class StartEmailRequest(BaseModel):
    email: str


class VerifyEmailRequest(BaseModel):
    email: str
    otp: str


@router.post("/signup", response_model=Dict[str, Any])
async def signup(payload: SignupRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.signup_with_password(
            email=payload.email,
            password=payload.password,
            name=payload.name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/signin", response_model=Dict[str, Any])
async def signin(payload: SigninRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.signin_with_password(
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/email/start", response_model=Dict[str, Any])
async def start_email_auth(payload: StartEmailRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.start_email_auth(payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/email/verify", response_model=Dict[str, Any])
async def verify_email_auth(payload: VerifyEmailRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.verify_email_auth(payload.email, payload.otp)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/oauth/google/start", response_model=Dict[str, Any])
async def oauth_google_start():
    has_credentials = bool(settings.GOOGLE_CLIENT_ID.strip()) and bool(settings.GOOGLE_CLIENT_SECRET.strip())
    if not has_credentials:
        return {
            "enabled": False,
            "message": "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and OAUTH_REDIRECT_URL.",
        }
    return {
        "enabled": False,
        "message": "Google OAuth callback flow is not implemented yet in this build.",
    }


@router.get("/oauth/google/callback", response_model=Dict[str, Any])
async def oauth_google_callback():
    return {
        "enabled": False,
        "message": "Google OAuth callback is a placeholder in this MVP build.",
    }


@router.get("/oauth/facebook/start", response_model=Dict[str, Any])
async def oauth_facebook_start():
    return {
        "enabled": False,
        "message": "Facebook OAuth is not configured in this MVP build.",
    }


@router.get("/oauth/facebook/callback", response_model=Dict[str, Any])
async def oauth_facebook_callback():
    return {
        "enabled": False,
        "message": "Facebook OAuth callback is a placeholder in this MVP build.",
    }


@router.get("/me", response_model=Dict[str, Any])
async def me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"user": current_user}


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    profession: Optional[str] = None
    location: Optional[str] = None
    about_me: Optional[str] = None


@router.patch("/profile", response_model=Dict[str, Any])
async def update_profile(
    payload: UpdateProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = AuthService(db)
    try:
        updates = {k: v for k, v in payload.model_dump().items() if v is not None}
        user = await service.update_profile(current_user["id"], updates)
        return {"user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


@router.post("/change-password", response_model=Dict[str, Any])
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = AuthService(db)
    try:
        return await service.change_password(
            current_user["id"], payload.current_password, payload.new_password
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class NotificationPreferencesRequest(BaseModel):
    tender_updates: Optional[bool] = None
    matching_tenders: Optional[bool] = None
    expiring_tenders: Optional[bool] = None


@router.patch("/notifications", response_model=Dict[str, Any])
async def update_notifications(
    payload: NotificationPreferencesRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = AuthService(db)
    prefs = {k: v for k, v in payload.model_dump().items() if v is not None}
    return await service.update_notifications(current_user["id"], prefs)


@router.delete("/account", response_model=Dict[str, Any])
async def delete_account(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    service = AuthService(db)
    try:
        return await service.delete_account(current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/logout", response_model=Dict[str, Any])
async def logout(_current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"logged_out": True}
