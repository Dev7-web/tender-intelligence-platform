"""
Seed demo data for local development.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

# Allow `python scripts/seed_demo.py` to resolve the `app` package.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import settings
from app.database.mongodb import create_indexes


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def seed() -> None:
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]

    await create_indexes(db)

    users = db.get_collection("users")
    companies = db.get_collection("company_profiles")
    tenders = db.get_collection("tenders")
    actions = db.get_collection("tender_actions")

    demo_email = "demo@tenderagent.local"
    user = await users.find_one({"email": demo_email})
    if not user:
        now = utcnow()
        result = await users.insert_one(
            {
                "email": demo_email,
                "name": "Demo User",
                "auth_provider": "email",
                "provider_user_id": None,
                "is_verified": True,
                "company_id": None,
                "created_at": now,
                "updated_at": now,
                "last_login_at": now,
            }
        )
        user = await users.find_one({"_id": result.inserted_id})

    company_id = user.get("company_id") or str(uuid4())
    await users.update_one({"_id": user["_id"]}, {"$set": {"company_id": company_id}})

    def fake_embed(text: str, dim: int = 384):
        base = sum(ord(char) for char in text) % 97
        return [((base + idx) % 17) / 17 for idx in range(dim)]
    company_summary = (
        "Demo InfraTech provides infrastructure modernization, energy solutions, and public-sector delivery "
        "across India with ISO certification and automation capabilities."
    )
    company_embedding = fake_embed(company_summary)

    await companies.update_one(
        {"company_id": company_id},
        {
            "$set": {
                "company_id": company_id,
                "owner_user_id": str(user["_id"]),
                "name": "Demo InfraTech Pvt Ltd",
                "company_url": "https://example.com",
                "experience_years": 8,
                "interest_tags": ["Infrastructure", "Energy", "Supply of Goods", "Technology"],
                "website_scrape": {
                    "status": "success",
                    "pages": ["https://example.com/about"],
                    "extracted_text": "Demo InfraTech builds and maintains public infrastructure projects.",
                    "last_error": None,
                },
                "uploaded_files": [],
                "metadata": {
                    "company_name": "Demo InfraTech Pvt Ltd",
                    "industries": ["Infrastructure", "Energy"],
                    "capabilities": ["Road construction", "Solar deployment", "Public works management"],
                    "certifications": ["ISO 9001", "ISO 14001"],
                    "technologies": ["GIS", "IoT Monitoring", "AI & Automation"],
                    "domains": ["Infrastructure", "Energy", "Supply of Goods"],
                    "past_clients": ["Public Works Department", "Urban Local Bodies"],
                    "government_experience": True,
                    "years_in_business": 8,
                    "employee_count": "50-200",
                    "annual_turnover": "INR 80 Cr",
                    "locations": ["Mumbai", "Bengaluru", "Jaipur"],
                    "registrations": ["MSME", "GST"],
                    "summary": company_summary,
                },
                "summary_embedding": company_embedding,
                "status": {
                    "processing_status": "ready",
                    "files_processed": 0,
                    "total_files": 0,
                    "last_error": None,
                },
                "updated_at": utcnow(),
            },
            "$setOnInsert": {"created_at": utcnow()},
        },
        upsert=True,
    )

    demo_tenders = [
        {
            "bid_id": "GEM/2026/B/1000001",
            "title": "Solar Photovoltaic Modules/Panels - Crystalline silicon terrestrial",
            "department": "Forests And Environment Department Gujarat",
            "location": "Panch Mahals, Gujarat",
            "summary": "Procurement and installation of high-efficiency solar modules with maintenance support.",
            "domains": ["Energy", "Infrastructure", "Supply of Goods"],
            "tech": ["Solar PV", "Electrical Integration"],
            "certs": ["ISO 9001"],
            "value": "₹15.2 L",
            "days": 12,
        },
        {
            "bid_id": "GEM/2026/B/1000002",
            "title": "Road Construction Materials - Asphalt",
            "department": "Public Works Department Karnataka",
            "location": "Bengaluru, Karnataka",
            "summary": "Supply of asphalt materials and project support for urban road resurfacing.",
            "domains": ["Infrastructure", "Supply of Goods"],
            "tech": ["Road Materials", "Logistics"],
            "certs": ["ISO 14001"],
            "value": "₹30 L",
            "days": 20,
        },
        {
            "bid_id": "GEM/2026/B/1000003",
            "title": "Smart Classroom Digital Equipment",
            "department": "Department of Education Rajasthan",
            "location": "Jaipur, Rajasthan",
            "summary": "Supply and deployment of smart classroom devices and training support.",
            "domains": ["Technology", "Education", "Supply of Goods"],
            "tech": ["Interactive Panels", "Network Infrastructure"],
            "certs": ["ISO 9001"],
            "value": "₹50 L",
            "days": 15,
        },
    ]

    inserted_tender_ids = []
    for index, item in enumerate(demo_tenders):
        summary_embedding = fake_embed(item["summary"])
        end_date = utcnow() + timedelta(days=item["days"])
        payload = {
            "bid_id": item["bid_id"],
            "ra_no": None,
            "gem_url": f"https://bidplus.gem.gov.in/bidlists/{item['bid_id']}",
            "pdf_url": None,
            "pdf_local_path": None,
            "portal": "gem",
            "scraped_info": {
                "items": item["title"],
                "quantity": None,
                "department": item["department"],
                "department_address": item["location"],
                "start_date": utcnow() - timedelta(days=2 + index),
                "end_date": end_date,
                "bid_type": "Product Bid/RAs",
                "bid_value_range": item["value"],
            },
            "metadata": {
                "title": item["title"],
                "department": item["department"],
                "sector": "government",
                "domains": item["domains"],
                "required_certifications": item["certs"],
                "required_technologies": item["tech"],
                "required_experience_years": 3,
                "estimated_value": item["value"],
                "eligibility_criteria": {
                    "min_turnover": "INR 1 Cr",
                    "min_experience_years": 3,
                    "required_registrations": ["GST"],
                },
                "location": item["location"],
                "delivery_period": "90 days",
                "emd_amount": "INR 20,000",
                "summary": item["summary"],
            },
            "summary_embedding": summary_embedding,
            "status": {
                "scrape_status": "completed",
                "pdf_downloaded": False,
                "llm_processed": True,
                "embedding_generated": True,
                "last_error": None,
            },
            "scraped_at": utcnow() - timedelta(days=1),
            "processed_at": utcnow() - timedelta(hours=12),
            "updated_at": utcnow(),
            "is_active": True,
            "expired": False,
        }
        result = await tenders.update_one(
            {"bid_id": item["bid_id"]},
            {"$set": payload, "$setOnInsert": {"created_at": utcnow()}},
            upsert=True,
        )
        if result.upserted_id:
            inserted_tender_ids.append(str(result.upserted_id))
        else:
            existing = await tenders.find_one({"bid_id": item["bid_id"]}, {"_id": 1})
            inserted_tender_ids.append(str(existing["_id"]))

    if inserted_tender_ids:
        await actions.update_one(
            {"company_id": company_id, "tender_id": inserted_tender_ids[0]},
            {
                "$set": {
                    "company_id": company_id,
                    "user_id": str(user["_id"]),
                    "tender_id": inserted_tender_ids[0],
                    "action": "saved",
                    "updated_at": utcnow(),
                },
                "$setOnInsert": {"created_at": utcnow()},
            },
            upsert=True,
        )

    print("Demo seed complete")
    print(f"Demo email: {demo_email}")
    print(f"Dev OTP: {settings.DEV_OTP_CODE}")
    print(f"Company ID: {company_id}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
