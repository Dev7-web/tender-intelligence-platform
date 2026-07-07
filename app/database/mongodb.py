"""
MongoDB connection and index management.
"""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import OperationFailure

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_client()[settings.DB_NAME]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def _ensure_ttl_index(
    database: AsyncIOMotorDatabase, collection: str, field: str, expire_seconds: int
) -> None:
    """Ensure a single-field TTL index on ``field`` with the given expiry.

    Re-running ``create_index`` with a changed ``expireAfterSeconds`` raises an
    IndexOptionsConflict, so if the index already exists we update it in place
    via ``collMod``. This keeps the retention window configurable across
    restarts without crashing startup.
    """
    coll = database.get_collection(collection)
    try:
        await coll.create_index([(field, ASCENDING)], expireAfterSeconds=expire_seconds)
    except OperationFailure:
        await database.command(
            {
                "collMod": collection,
                "index": {"keyPattern": {field: 1}, "expireAfterSeconds": expire_seconds},
            }
        )


async def create_indexes(db: Optional[AsyncIOMotorDatabase] = None) -> None:
    """Create required indexes for collections."""
    database = db if db is not None else get_database()

    tender_coll = database.get_collection("tenders")
    await tender_coll.create_index([("bid_id", ASCENDING)], unique=True)
    await tender_coll.create_index([("status.scrape_status", ASCENDING)])
    await tender_coll.create_index([("status.llm_processed", ASCENDING)])
    await tender_coll.create_index([("scraped_info.end_date", ASCENDING)])
    await tender_coll.create_index([("metadata.domains", ASCENDING)])
    await tender_coll.create_index([("metadata.required_certifications", ASCENDING)])
    await tender_coll.create_index([("is_active", ASCENDING), ("expired", ASCENDING)])
    await tender_coll.create_index([("expired", ASCENDING)])
    await tender_coll.create_index([("scraped_at", DESCENDING)])
    await tender_coll.create_index([("created_at", DESCENDING)])

    company_coll = database.get_collection("company_profiles")
    await company_coll.create_index([("company_id", ASCENDING)], unique=True)
    await company_coll.create_index([("owner_user_id", ASCENDING)])
    await company_coll.create_index([("status.processing_status", ASCENDING)])
    await company_coll.create_index([("metadata.certifications", ASCENDING)])
    await company_coll.create_index([("metadata.technologies", ASCENDING)])
    await company_coll.create_index([("metadata.domains", ASCENDING)])
    await company_coll.create_index([("created_at", DESCENDING)])

    users_coll = database.get_collection("users")
    await users_coll.create_index([("email", ASCENDING)], unique=True)
    await users_coll.create_index([("company_id", ASCENDING)])

    sessions_coll = database.get_collection("auth_sessions")
    await sessions_coll.create_index([("user_id", ASCENDING)])
    await sessions_coll.create_index([("expires_at", ASCENDING)])

    otp_coll = database.get_collection("auth_otps")
    await otp_coll.create_index([("email", ASCENDING), ("created_at", DESCENDING)])
    await otp_coll.create_index([("expires_at", ASCENDING)])

    auth_rate_limits_coll = database.get_collection("auth_rate_limits")
    await auth_rate_limits_coll.create_index([("scope", ASCENDING), ("key", ASCENDING), ("ts", DESCENDING)])
    await _ensure_ttl_index(
        database,
        "auth_rate_limits",
        "ts",
        max(settings.AUTH_RATE_LIMIT_IP_WINDOW_SECONDS, settings.AUTH_RATE_LIMIT_EMAIL_WINDOW_SECONDS),
    )

    actions_coll = database.get_collection("tender_actions")
    await actions_coll.create_index([("company_id", ASCENDING), ("tender_id", ASCENDING)], unique=True)
    await actions_coll.create_index([("company_id", ASCENDING), ("action", ASCENDING)])
    await actions_coll.create_index([("updated_at", DESCENDING)])

    chats_coll = database.get_collection("tender_chats")
    await chats_coll.create_index([("company_id", ASCENDING), ("tender_id", ASCENDING)])
    await chats_coll.create_index([("updated_at", DESCENDING)])

    rate_limits_coll = database.get_collection("ai_chat_rate_limits")
    await rate_limits_coll.create_index([("user_id", ASCENDING), ("ts", DESCENDING)])
    await _ensure_ttl_index(
        database,
        "ai_chat_rate_limits",
        "ts",
        settings.AI_RATE_LIMIT_WINDOW_SECONDS,
    )

    share_logs = database.get_collection("share_logs")
    await share_logs.create_index([("company_id", ASCENDING), ("created_at", DESCENDING)])
    await share_logs.create_index([("tender_id", ASCENDING)])

    await database.get_collection("search_history").create_index(
        [("company_id", ASCENDING), ("searched_at", DESCENDING)]
    )
    # TTL index: auto-delete search_history rows older than the retention
    # window so the collection cannot grow without bound (issue #18).
    await _ensure_ttl_index(
        database,
        "search_history",
        "searched_at",
        settings.SEARCH_HISTORY_RETENTION_DAYS * 24 * 3600,
    )
    scrape_coll = database.get_collection("scrape_logs")
    await scrape_coll.create_index([("job_id", ASCENDING)], unique=True)
    await scrape_coll.create_index([("started_at", DESCENDING)])
    await scrape_coll.create_index([("status", ASCENDING)])
    await scrape_coll.create_index([("job_type", ASCENDING)])

    logger.info("mongodb.indexes.created")
