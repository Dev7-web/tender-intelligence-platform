"""
Tender-grounded AI chat service.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.processors.llm_extractor import LLMExtractor
from app.utils.logger import get_logger

logger = get_logger(__name__)


SUGGESTIONS = [
    "What is the timeline for the tender submission and evaluation process?",
    "What is the budget range allocated for this tender?",
    "What criteria will be used to evaluate the tender proposals?",
    "Are there any specific requirements or regulations to adhere to?",
    "Who are the main points of contact for questions during the tender process?",
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AIChatService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.tenders = db.get_collection("tenders")
        self.companies = db.get_collection("company_profiles")
        self.chats = db.get_collection("tender_chats")
        self.rate_limits = db.get_collection("ai_chat_rate_limits")
        self.llm = LLMExtractor()

    def get_suggestions(self) -> List[str]:
        return SUGGESTIONS

    async def chat(
        self,
        tender_id: str,
        company_id: str,
        owner_user_id: str,
        message: str,
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not message.strip():
            raise ValueError("Message is required")

        await self._check_rate_limit(owner_user_id)

        tender = await self.tenders.find_one({"_id": ObjectId(tender_id)})
        if not tender:
            raise ValueError("Tender not found")

        company = await self.companies.find_one({"company_id": company_id, "owner_user_id": owner_user_id})
        if not company:
            raise ValueError("Company profile not found")

        chat_doc = None
        if chat_id:
            try:
                chat_doc = await self.chats.find_one(
                    {
                        "_id": ObjectId(chat_id),
                        "company_id": company_id,
                        "tender_id": tender_id,
                    }
                )
            except Exception:
                chat_doc = None

        history = (chat_doc or {}).get("messages", [])[-8:]
        prompt = self._build_prompt(tender=tender, company=company, history=history, user_message=message)

        try:
            reply = self.llm.generate_text(prompt)
        except Exception as exc:
            logger.info("ai_chat.generation_failed", error=str(exc))
            reply = (
                "I could not complete a full analysis right now. Please check the official tender document "
                "for exact eligibility, deadlines, and compliance clauses."
            )

        user_msg = {"role": "user", "content": message, "ts": utcnow()}
        ai_msg = {"role": "assistant", "content": reply.strip(), "ts": utcnow()}

        if chat_doc:
            await self.chats.update_one(
                {"_id": chat_doc["_id"]},
                {
                    "$push": {
                        "messages": {
                            "$each": [user_msg, ai_msg],
                            "$slice": -settings.AI_CHAT_MAX_MESSAGES,
                        }
                    },
                    "$set": {"updated_at": utcnow()},
                },
            )
            final_chat_id = str(chat_doc["_id"])
        else:
            insert = {
                "company_id": company_id,
                "tender_id": tender_id,
                "messages": [user_msg, ai_msg],
                "created_at": utcnow(),
                "updated_at": utcnow(),
            }
            result = await self.chats.insert_one(insert)
            final_chat_id = str(result.inserted_id)

        return {
            "chat_id": final_chat_id,
            "reply": reply.strip(),
        }

    def _build_prompt(
        self,
        tender: Dict[str, Any],
        company: Dict[str, Any],
        history: List[Dict[str, Any]],
        user_message: str,
    ) -> str:
        tender_meta = tender.get("metadata") or {}
        scraped_info = tender.get("scraped_info") or {}
        company_meta = company.get("metadata") or {}

        history_text = "\n".join([f"{item.get('role')}: {item.get('content')}" for item in history if item.get("content")])

        return f"""
You are an AI tender analyst.
Use ONLY the context below. If information is missing, explicitly say it is missing and suggest checking the official tender documents.
Keep the answer concise and practical.

Tender Context:
- Title: {tender_meta.get('title') or scraped_info.get('items') or 'N/A'}
- Department: {tender_meta.get('department') or scraped_info.get('department') or 'N/A'}
- Location: {tender_meta.get('location') or 'N/A'}
- Estimated Value: {tender_meta.get('estimated_value') or scraped_info.get('bid_value_range') or 'N/A'}
- Close Date: {scraped_info.get('end_date')}
- Summary: {tender_meta.get('summary') or 'N/A'}
- Eligibility: {tender_meta.get('eligibility_criteria')}
- Certifications: {tender_meta.get('required_certifications')}
- Technologies: {tender_meta.get('required_technologies')}

Company Context:
- Name: {company.get('name')}
- Capabilities: {company_meta.get('capabilities')}
- Domains: {company_meta.get('domains')}
- Certifications: {company_meta.get('certifications')}

Recent Chat:
{history_text}

User question: {user_message}
""".strip()

    async def _check_rate_limit(self, owner_user_id: str) -> None:
        now = utcnow()
        window_start = now - timedelta(seconds=settings.AI_RATE_LIMIT_WINDOW_SECONDS)
        result = await self.rate_limits.insert_one({"user_id": owner_user_id, "ts": now})
        count = await self.rate_limits.count_documents({"user_id": owner_user_id, "ts": {"$gte": window_start}})

        if count > settings.AI_RATE_LIMIT_PER_MIN:
            await self.rate_limits.delete_one({"_id": result.inserted_id})
            raise ValueError("AI chat rate limit exceeded. Please retry in one minute.")
