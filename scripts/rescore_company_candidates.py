"""Re-score company tender candidates with the strict relevance gate."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

from bson import ObjectId

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.mongodb import get_database
from app.database.repositories.company_tender_candidate_repo import CompanyTenderCandidateRepository
from app.services.match_service import MatchService
from app.services.tender_relevance import assess_tender_relevance


async def _find_tender(db, tender_id: Any, bid_id: str | None) -> Dict[str, Any] | None:
    if tender_id:
        try:
            tender = await db.get_collection("tenders").find_one({"_id": ObjectId(str(tender_id))})
            if tender:
                return tender
        except Exception:
            pass
        tender = await db.get_collection("tenders").find_one({"_id": tender_id})
        if tender:
            return tender
        tender = await db.get_collection("tenders").find_one({"_id": str(tender_id)})
        if tender:
            return tender
    if bid_id:
        return await db.get_collection("tenders").find_one({"bid_id": bid_id})
    return None


async def run(*, company_id: str | None, apply: bool) -> None:
    db = get_database()
    companies = db.get_collection("company_profiles")
    candidates = db.get_collection("company_tender_candidates")
    repo = CompanyTenderCandidateRepository(db)
    match_service = MatchService(db)

    company_filter = {"company_id": company_id} if company_id else {}
    totals = {"checked": 0, "accepted": 0, "rejected": 0, "missing_tender": 0}

    async for profile in companies.find(company_filter):
        cid = profile.get("company_id")
        async for candidate in candidates.find({"company_id": cid}):
            totals["checked"] += 1
            tender = await _find_tender(db, candidate.get("tender_id"), candidate.get("bid_id"))
            if not tender:
                totals["missing_tender"] += 1
                totals["rejected"] += 1
                if apply:
                    await candidates.update_one(
                        {"_id": candidate["_id"]},
                        {
                            "$set": {
                                "qualified": False,
                                "relevance_status": "rejected",
                                "relevance_score": 0.0,
                                "relevance_reasons": ["Tender document missing"],
                                "matched_core_terms": [],
                            }
                        },
                    )
                continue

            relevance = assess_tender_relevance(profile=profile, tender=tender, search_keyword=candidate.get("search_keyword"))
            if relevance["accepted"]:
                totals["accepted"] += 1
                if apply:
                    score_data = match_service.score_tender_for_profile(profile=profile, tender=tender)
                    await repo.upsert_candidate(
                        company_id=cid,
                        tender_id=str(tender.get("_id")),
                        bid_id=tender.get("bid_id") or candidate.get("bid_id"),
                        search_keyword=candidate.get("search_keyword"),
                        raw_score=score_data["raw_score"],
                        match_score=score_data["match_score"],
                        match_reasons=score_data["match_reasons"],
                        qualified=score_data["qualified"],
                        relevance_status=score_data["relevance_status"],
                        relevance_score=score_data["relevance_score"],
                        relevance_reasons=score_data["relevance_reasons"],
                        matched_core_terms=score_data["matched_core_terms"],
                    )
            else:
                totals["rejected"] += 1
                if apply:
                    await repo.upsert_rejected(
                        company_id=cid,
                        tender_id=str(tender.get("_id")),
                        bid_id=tender.get("bid_id") or candidate.get("bid_id"),
                        search_keyword=candidate.get("search_keyword"),
                        relevance_score=relevance["relevance_score"],
                        relevance_reasons=relevance["relevance_reasons"],
                        matched_core_terms=relevance["matched_core_terms"],
                    )

    mode = "applied" if apply else "dry-run"
    print(f"{mode}: {totals}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    asyncio.run(run(company_id=args.company_id, apply=args.apply))
