"""
Application Configuration
"""

from __future__ import annotations

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Tender Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "TendorMatching"

    # API Keys
    GEMINI_API_KEY: str = ""

    # File Storage
    TENDER_PDF_DIR: str = "data/pdfs/tenders"
    PROFILE_UPLOAD_DIR: str = "data/pdfs/profiles"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    MAX_ONBOARDING_TOTAL_SIZE: int = 209715200  # 200MB

    # Scraping
    SCRAPE_MAX_PAGES: int = 10
    SCRAPE_MAX_BIDS: int = 200
    SCRAPE_MIN_DELAY: int = 2
    SCRAPE_MAX_DELAY: int = 5
    SCRAPER_HEADLESS: bool = True

    # LLM
    LLM_PROVIDER: str = "ollama"
    LLM_BASE_URL: str = "http://124.123.18.150:11434"
    LLM_MODEL: str = "gpt-oss:latest"
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_INPUT_MAX_CHARS: int = 12000
    LLM_GEMINI_MAX_CHARS: int = 500000  # Gemini supports large context
    LLM_CHUNK_SIZE: int = 30000  # Chunk size for very large docs
    LLM_CHUNK_OVERLAP: int = 1000  # Overlap between chunks
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Embedding
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000"
    )
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # Scheduler
    ENABLE_SCHEDULER: bool = False
    SCRAPE_INTERVAL_HOURS: int = 6
    PROCESS_INTERVAL_MINUTES: int = 30
    PROCESS_BATCH_LIMIT: int = 50

    # Auth
    JWT_SECRET: str = "change-me"
    JWT_EXPIRES_MIN: int = 60
    JWT_REFRESH_EXPIRES_DAYS: int = 30
    OTP_EXPIRES_MIN: int = 10
    DEV_OTP_CODE: str = "123456"
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""

    # Email
    EMAIL_PROVIDER: str = "smtp"
    EMAIL_FROM: str = "Tender Agent <no-reply@example.com>"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SENDGRID_API_KEY: str = ""

    # OAuth (optional placeholders for MVP)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FACEBOOK_CLIENT_ID: str = ""
    FACEBOOK_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URL: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    # Company website scrape
    WEBSITE_SCRAPE_MAX_PAGES: int = 10
    WEBSITE_SCRAPE_TIMEOUT_SECONDS: int = 12
    WEBSITE_SCRAPE_MAX_CHARS: int = 200000

    # AI chat
    AI_RATE_LIMIT_PER_MIN: int = 20

    # Admin panel
    ADMIN_API_KEY: str = "tender-admin-secret"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

# Create directories for local storage
os.makedirs(settings.TENDER_PDF_DIR, exist_ok=True)
os.makedirs(settings.PROFILE_UPLOAD_DIR, exist_ok=True)
