import pytest

from app.database.repositories.tender_action_repo import TenderActionRepository


@pytest.mark.asyncio
async def test_tender_action_upsert_logic(fake_db):
    repo = TenderActionRepository(fake_db)

    await repo.set_action(company_id="c1", user_id="u1", tender_id="t1", action="saved")
    await repo.set_action(company_id="c1", user_id="u1", tender_id="t1", action="applied")

    action_map = await repo.get_action_map("c1", ["t1"])
    assert action_map["t1"] == "applied"

    count_applied = await repo.count_by_company_action("c1", "applied")
    assert count_applied == 1

    await repo.set_action(company_id="c1", user_id="u1", tender_id="t1", action=None)
    action_map_after_delete = await repo.get_action_map("c1", ["t1"])
    assert "t1" not in action_map_after_delete
