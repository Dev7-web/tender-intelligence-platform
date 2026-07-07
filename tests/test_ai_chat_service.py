from datetime import datetime, timezone

import pytest
from bson import ObjectId

from app.config import settings
from app.services.ai_chat_service import AIChatService


class StubLLM:
    def generate_text(self, prompt: str) -> str:
        return "new assistant reply"


def _old_message(index: int):
    return {
        "role": "user" if index % 2 == 0 else "assistant",
        "content": f"old-{index}",
        "ts": datetime.now(timezone.utc),
    }


@pytest.mark.asyncio
async def test_rate_limit_persists_across_service_instances(fake_db, monkeypatch):
    monkeypatch.setattr(settings, "AI_RATE_LIMIT_PER_MIN", 2)
    monkeypatch.setattr(settings, "AI_RATE_LIMIT_WINDOW_SECONDS", 60)
    owner_user_id = "user-1"

    service = AIChatService(fake_db)
    await service._check_rate_limit(owner_user_id)
    await service._check_rate_limit(owner_user_id)

    restarted_service = AIChatService(fake_db)
    with pytest.raises(ValueError, match="AI chat rate limit exceeded"):
        await restarted_service._check_rate_limit(owner_user_id)

    stored_attempts = await fake_db.get_collection("ai_chat_rate_limits").count_documents({"user_id": owner_user_id})
    assert stored_attempts == settings.AI_RATE_LIMIT_PER_MIN


@pytest.mark.asyncio
async def test_chat_update_keeps_latest_100_messages(fake_db, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "http://localhost:11434")
    tender_id = ObjectId()
    chat_id = ObjectId()
    company_id = "company-1"
    owner_user_id = "user-1"
    now = datetime.now(timezone.utc)

    await fake_db.get_collection("tenders").insert_one(
        {
            "_id": tender_id,
            "metadata": {"title": "Network upgrade"},
            "scraped_info": {"end_date": now},
        }
    )
    await fake_db.get_collection("company_profiles").insert_one(
        {
            "company_id": company_id,
            "owner_user_id": owner_user_id,
            "name": "Example Co",
            "metadata": {},
        }
    )
    await fake_db.get_collection("tender_chats").insert_one(
        {
            "_id": chat_id,
            "company_id": company_id,
            "tender_id": str(tender_id),
            "messages": [_old_message(index) for index in range(settings.AI_CHAT_MAX_MESSAGES)],
            "created_at": now,
            "updated_at": now,
        }
    )

    service = AIChatService(fake_db)
    service.llm = StubLLM()

    result = await service.chat(
        tender_id=str(tender_id),
        company_id=company_id,
        owner_user_id=owner_user_id,
        message="new user question",
        chat_id=str(chat_id),
    )

    stored = await fake_db.get_collection("tender_chats").find_one({"_id": chat_id})
    messages = stored["messages"]

    assert result["chat_id"] == str(chat_id)
    assert len(messages) == settings.AI_CHAT_MAX_MESSAGES
    assert messages[0]["content"] == "old-2"
    assert messages[-2]["content"] == "new user question"
    assert messages[-1]["content"] == "new assistant reply"
