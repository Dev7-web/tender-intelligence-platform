"""
Company profile onboarding and processing service.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiofiles
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from tenacity import RetryError

from app.config import settings
from app.database.repositories.company_repo import CompanyRepository
from app.processors.document_extractor import DocumentExtractor, is_extractable_file
from app.processors.embedder import TextEmbedder
from app.processors.llm_extractor import LLMExtractor
from app.services.auth_service import AuthService
from app.services.company_website_scraper import CompanyWebsiteScraper
from app.services.socket_manager import manager
from app.utils.helpers import ensure_dir, safe_filename, sha256_file
from app.utils.logger import get_logger

logger = get_logger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CompanyService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.repo = CompanyRepository(db)
        self.document_extractor = DocumentExtractor()
        self.embedder = TextEmbedder()
        self.website_scraper = CompanyWebsiteScraper()
        self.auth_service = AuthService(db)
        self._llm: Optional[LLMExtractor] = None

    def _get_llm(self) -> LLMExtractor:
        if self._llm is None:
            self._llm = LLMExtractor()
        return self._llm

    async def create_company(self, owner_user_id: str, name: str, company_url: str, experience_years: int) -> Dict[str, Any]:
        if not name.strip():
            raise ValueError("Company name is required")
        if not company_url.strip():
            raise ValueError("Company URL is required")
        parsed_url = urlparse(company_url.strip() if "://" in company_url else f"https://{company_url.strip()}")
        if not parsed_url.netloc:
            raise ValueError("Company URL is invalid")
        if experience_years < 0 or experience_years > 100:
            raise ValueError("Experience must be between 0 and 100")

        company_id = str(uuid.uuid4())
        normalized_url = company_url.strip() if "://" in company_url else f"https://{company_url.strip()}"

        profile = {
            "company_id": company_id,
            "owner_user_id": owner_user_id,
            "name": name.strip(),
            "company_url": normalized_url,
            "experience_years": int(experience_years),
            "interest_tags": [],
            "website_scrape": {
                "status": "pending",
                "pages": [],
                "extracted_text": "",
                "last_error": None,
            },
            "uploaded_files": [],
            "metadata": {},
            "summary_embedding": [],
            "status": {
                "processing_status": "pending",
                "files_processed": 0,
                "total_files": 0,
                "last_error": None,
            },
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        await self.repo.create(profile)
        await self.auth_service.set_user_company(owner_user_id, company_id)
        return self._serialize(profile)

    async def scrape_website(self, company_id: str, owner_user_id: str) -> Dict[str, Any]:
        profile = await self._get_owned_profile(company_id, owner_user_id)
        if not profile:
            raise ValueError("Company profile not found")

        company_url = profile.get("company_url")
        result = await self.website_scraper.scrape(company_url)

        await self.repo.update(
            company_id,
            {
                "website_scrape": result,
                "updated_at": utcnow(),
            },
        )
        return result

    async def upload_documents(
        self,
        company_id: str,
        owner_user_id: str,
        files: List[UploadFile],
    ) -> Dict[str, Any]:
        profile = await self._get_owned_profile(company_id, owner_user_id)
        if not profile:
            raise ValueError("Company profile not found")
        if not files:
            raise ValueError("No files provided")

        company_dir = os.path.join(settings.PROFILE_UPLOAD_DIR, company_id)
        ensure_dir(company_dir)

        existing_files = profile.get("uploaded_files", [])
        existing_by_hash = {item.get("file_hash"): item for item in existing_files}
        existing_hashes = {item.get("file_hash") for item in existing_files}
        current_total_size = sum(int(item.get("size_bytes") or 0) for item in existing_files)

        uploaded_items: List[Dict[str, Any]] = []
        for index, file in enumerate(files, start=1):
            if not file.filename:
                continue

            ext = os.path.splitext(file.filename.lower())[1]
            safe_name = safe_filename(file.filename, default=f"file_{index}{ext or ''}")
            local_path = os.path.join(company_dir, safe_name)

            file_size = 0
            async with aiofiles.open(local_path, "wb") as handle:
                while True:
                    chunk = await file.read(8192)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    if file_size > settings.MAX_UPLOAD_SIZE:
                        raise ValueError(f"File {file.filename} exceeds max upload size")
                    if current_total_size + file_size > settings.MAX_ONBOARDING_TOTAL_SIZE:
                        raise ValueError("Total upload size exceeds allowed onboarding limit")
                    await handle.write(chunk)

            file_hash = sha256_file(local_path)
            if file_hash in existing_hashes:
                existing_item = existing_by_hash.get(file_hash) or {}
                os.remove(local_path)
                uploaded_items.append(
                    {
                        "file_hash": file_hash,
                        "original_name": existing_item.get("original_name") or file.filename,
                        "status": "already_exists",
                        "size_bytes": existing_item.get("size_bytes"),
                        "extract_status": existing_item.get("extract_status"),
                        "extract_error": existing_item.get("extract_error"),
                        "extracted_text_len": existing_item.get("extracted_text_len", 0),
                    }
                )
                continue

            extracted_text = None
            extract_error = None
            extract_status = "stored_only"
            if is_extractable_file(file.filename):
                extracted_text = self.document_extractor.extract_text(local_path)
                if extracted_text:
                    extract_status = "extracted"
                elif self.document_extractor.needs_ocr(local_path):
                    extract_status = "needs_ocr"
                    extract_error = "No selectable text found. OCR is required."
                else:
                    extract_status = "failed"
                    extract_error = "No extractable text found."

            item = {
                "file_hash": file_hash,
                "original_name": file.filename,
                "local_path": local_path,
                "mime_type": file.content_type,
                "size_bytes": file_size,
                "uploaded_at": utcnow(),
                "extract_status": extract_status,
                "extract_error": extract_error,
                "extracted_text_len": len(extracted_text or ""),
                "extracted_text": extracted_text,
            }
            existing_files.append(item)
            existing_by_hash[file_hash] = item
            existing_hashes.add(file_hash)
            current_total_size += file_size

            uploaded_items.append(
                {
                    "file_hash": file_hash,
                    "original_name": file.filename,
                    "status": extract_status,
                    "size_bytes": file_size,
                    "extract_status": extract_status,
                    "extract_error": extract_error,
                    "extracted_text_len": len(extracted_text or ""),
                }
            )

            await self._broadcast_progress(
                job="PROCESS_COMPANY",
                job_id=company_id,
                status="progress",
                current=len(uploaded_items),
                total=len(files),
                message=f"Uploaded {file.filename}",
            )

        files_processed = len([item for item in existing_files if item.get("extract_status") == "extracted"])
        status = profile.get("status") or {}
        status.update(
            {
                "files_processed": files_processed,
                "total_files": len(existing_files),
            }
        )

        await self.repo.update(
            company_id,
            {
                "uploaded_files": existing_files,
                "status": status,
                "updated_at": utcnow(),
            },
        )

        # Auto-trigger profile rebuild only when newly uploaded files added usable text.
        usable_files_added = any(
            item.get("status") == "extracted" for item in uploaded_items
        )
        reprocessing = False
        if usable_files_added:
            reprocessing = True
            asyncio.create_task(
                self._process_company_profile(
                    company_id=company_id,
                    owner_user_id=owner_user_id,
                    job_id=str(uuid.uuid4()),
                )
            )

        return {
            "company_id": company_id,
            "files": uploaded_items,
            "total_files": len(existing_files),
            "uploaded": len(uploaded_items),
            "reprocessing": reprocessing,
        }

    async def remove_document(self, company_id: str, owner_user_id: str, file_hash: str) -> bool:
        profile = await self._get_owned_profile(company_id, owner_user_id)
        if not profile:
            raise ValueError("Company profile not found")

        files = profile.get("uploaded_files", [])
        target = next((item for item in files if item.get("file_hash") == file_hash), None)
        if not target:
            return False

        path = target.get("local_path")
        if path and os.path.exists(path):
            os.remove(path)

        updated = [item for item in files if item.get("file_hash") != file_hash]
        status = profile.get("status") or {}
        status["total_files"] = len(updated)
        status["files_processed"] = len([item for item in updated if item.get("extract_status") == "extracted"])

        await self.repo.update(
            company_id,
            {
                "uploaded_files": updated,
                "status": status,
                "updated_at": utcnow(),
            },
        )
        return True

    async def set_interests(self, company_id: str, owner_user_id: str, interest_tags: List[str]) -> Dict[str, Any]:
        profile = await self._get_owned_profile(company_id, owner_user_id)
        if not profile:
            raise ValueError("Company profile not found")

        cleaned = [tag.strip() for tag in interest_tags if tag and tag.strip()]
        await self.repo.update(
            company_id,
            {
                "interest_tags": cleaned,
                "updated_at": utcnow(),
            },
        )
        profile["interest_tags"] = cleaned
        return self._serialize(profile)

    async def update_company(self, company_id: str, owner_user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        profile = await self._get_owned_profile(company_id, owner_user_id)
        if not profile:
            raise ValueError("Company profile not found")

        allowed_fields = {
            "name", "company_url", "experience_years", "turnover",
            "description", "interest_tags", "interested_states", "tender_topics",
        }
        patch: Dict[str, Any] = {}
        for key, value in updates.items():
            if key not in allowed_fields:
                continue
            if key == "name" and isinstance(value, str):
                if not value.strip():
                    raise ValueError("Company name cannot be empty")
                patch[key] = value.strip()
            elif key == "company_url" and isinstance(value, str):
                if not value.strip():
                    raise ValueError("Company URL cannot be empty")
                normalized = value.strip() if "://" in value else f"https://{value.strip()}"
                parsed = urlparse(normalized)
                if not parsed.netloc:
                    raise ValueError("Company URL is invalid")
                patch[key] = normalized
            elif key in ("interest_tags", "interested_states", "tender_topics") and isinstance(value, list):
                patch[key] = [tag.strip() for tag in value if isinstance(tag, str) and tag.strip()]
            else:
                patch[key] = value

        if not patch:
            return self._serialize(profile)

        # Detect if URL changed
        old_url = (profile.get("company_url") or "").strip()
        new_url = (patch.get("company_url") or "").strip()
        url_changed = "company_url" in patch and new_url != old_url

        patch["updated_at"] = utcnow()
        await self.repo.update(company_id, patch)

        # Auto-trigger scrape + reprocess if URL changed, otherwise just reprocess
        rescraping = False
        reprocessing = False
        if url_changed:
            rescraping = True
            reprocessing = True
            asyncio.create_task(self._scrape_and_process(company_id, owner_user_id))
        else:
            reprocessing = True
            asyncio.create_task(
                self._process_company_profile(
                    company_id=company_id,
                    owner_user_id=owner_user_id,
                    job_id=str(uuid.uuid4()),
                )
            )

        updated = await self._get_owned_profile(company_id, owner_user_id)
        result = self._serialize(updated or profile)
        result["rescraping"] = rescraping
        result["reprocessing"] = reprocessing
        return result

    async def _scrape_and_process(self, company_id: str, owner_user_id: str) -> None:
        """Background task: scrape the company website, then rebuild the profile."""
        job_id = str(uuid.uuid4())
        try:
            await self._broadcast_progress(
                job="PROCESS_COMPANY", job_id=job_id, status="started",
                current=0, total=4, message="Scraping company website...",
            )
            await self.scrape_website(company_id, owner_user_id)
            await self._broadcast_progress(
                job="PROCESS_COMPANY", job_id=job_id, status="progress",
                current=1, total=4, message="Website scraped, rebuilding profile...",
            )
        except Exception as exc:
            logger.info("company.scrape_failed_during_update", company_id=company_id, error=str(exc))
            await self._broadcast_progress(
                job="PROCESS_COMPANY", job_id=job_id, status="progress",
                current=1, total=4, message=f"Website scrape failed: {exc}. Continuing with profile rebuild...",
            )

        await self._process_company_profile(
            company_id=company_id, owner_user_id=owner_user_id, job_id=job_id,
        )

    async def start_processing(self, company_id: str, owner_user_id: str) -> Dict[str, Any]:
        profile = await self._get_owned_profile(company_id, owner_user_id)
        if not profile:
            raise ValueError("Company profile not found")

        job_id = str(uuid.uuid4())
        await self.repo.update(
            company_id,
            {
                "status": {
                    **(profile.get("status") or {}),
                    "processing_status": "processing",
                    "last_error": None,
                },
            },
        )

        asyncio.create_task(self._process_company_profile(company_id=company_id, owner_user_id=owner_user_id, job_id=job_id))
        return {"status": "processing", "job_id": job_id}

    async def _process_company_profile(self, company_id: str, owner_user_id: str, job_id: str) -> None:
        profile = await self._get_owned_profile(company_id, owner_user_id)
        if not profile:
            return

        await self._broadcast_progress(
            job="PROCESS_COMPANY",
            job_id=job_id,
            status="started",
            current=0,
            total=3,
            message="Starting company profile analysis",
        )

        try:
            combined_text = self._build_combined_text(profile)
            await self._broadcast_progress(
                job="PROCESS_COMPANY",
                job_id=job_id,
                status="progress",
                current=1,
                total=3,
                message="Generating structured metadata",
            )

            metadata: Dict[str, Any] = {}
            if combined_text:
                metadata = self._get_llm().extract_company(combined_text)

            summary_text = (metadata or {}).get("summary") or ""
            embedding = self.embedder.embed(summary_text)

            await self._broadcast_progress(
                job="PROCESS_COMPANY",
                job_id=job_id,
                status="progress",
                current=2,
                total=3,
                message="Building embeddings",
            )

            status = profile.get("status") or {}
            status.update(
                {
                    "processing_status": "ready",
                    "last_error": None,
                    "files_processed": len(
                        [item for item in profile.get("uploaded_files", []) if item.get("extract_status") == "extracted"]
                    ),
                    "total_files": len(profile.get("uploaded_files", [])),
                }
            )

            await self.repo.update(
                company_id,
                {
                    "metadata": metadata,
                    "summary_embedding": embedding,
                    "status": status,
                    "updated_at": utcnow(),
                },
            )

            await self._broadcast_progress(
                job="PROCESS_COMPANY",
                job_id=job_id,
                status="completed",
                current=3,
                total=3,
                message="Company profile is ready",
            )
        except Exception as exc:
            error_message = self._normalize_error_message(exc)
            logger.info("company.process_failed", company_id=company_id, error=error_message)
            status = profile.get("status") or {}
            status.update(
                {
                    "processing_status": "failed",
                    "last_error": error_message,
                }
            )
            await self.repo.update(company_id, {"status": status, "updated_at": utcnow()})
            await self._broadcast_progress(
                job="PROCESS_COMPANY",
                job_id=job_id,
                status="failed",
                current=0,
                total=3,
                message=error_message,
            )

    def _build_combined_text(self, profile: Dict[str, Any]) -> str:
        chunks: List[str] = []
        chunks.append(f"Company Name: {profile.get('name') or ''}")
        chunks.append(f"Company URL: {profile.get('company_url') or ''}")
        chunks.append(f"Experience Years: {profile.get('experience_years') or ''}")

        turnover = (profile.get("turnover") or "").strip()
        if turnover:
            chunks.append(f"Turnover: {turnover}")

        description = (profile.get("description") or "").strip()
        if description:
            chunks.append(f"Company Description: {description}")

        interest_tags = profile.get("interest_tags") or []
        if interest_tags:
            chunks.append(f"Interest Tags: {', '.join(interest_tags)}")

        interested_states = profile.get("interested_states") or []
        if interested_states:
            chunks.append(f"Interested States: {', '.join(interested_states)}")

        tender_topics = profile.get("tender_topics") or []
        if tender_topics:
            chunks.append(f"Tender Topics: {', '.join(tender_topics)}")

        website_text = ((profile.get("website_scrape") or {}).get("extracted_text") or "").strip()
        if website_text:
            chunks.append("Website Information:")
            chunks.append(website_text)

        for file_info in profile.get("uploaded_files", []):
            extracted = (file_info.get("extracted_text") or "").strip()
            if extracted:
                chunks.append(f"Document {file_info.get('original_name')}:\n{extracted}")

        full_text = "\n\n".join(part for part in chunks if part)
        max_chars = settings.LLM_GEMINI_MAX_CHARS if settings.LLM_PROVIDER.lower() == "gemini" else settings.LLM_INPUT_MAX_CHARS
        if len(full_text) > max_chars:
            return full_text[:max_chars]
        return full_text

    async def get_profile(self, company_id: str, owner_user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        profile = await self.repo.get_by_id(company_id)
        if not profile:
            return None
        if owner_user_id and profile.get("owner_user_id") != owner_user_id:
            return None
        return self._serialize(profile)

    async def list_companies(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        search: Optional[str] = None,
        owner_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        filters: Dict[str, Any] = {}
        if status:
            filters["status.processing_status"] = status
        if search:
            regex = {"$regex": search, "$options": "i"}
            filters["$or"] = [
                {"name": regex},
                {"metadata.company_name": regex},
                {"metadata.domains": regex},
            ]
        if owner_user_id:
            filters["owner_user_id"] = owner_user_id

        total = await self.repo.collection.count_documents(filters)
        cursor = self.repo.collection.find(filters).sort("created_at", -1).skip(skip).limit(limit)
        items = []
        async for profile in cursor:
            items.append(self._serialize(profile))
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    async def delete_profile(self, company_id: str, owner_user_id: Optional[str] = None) -> bool:
        profile = await self.repo.get_by_id(company_id)
        if not profile:
            return False
        if owner_user_id and profile.get("owner_user_id") != owner_user_id:
            return False

        for file_info in profile.get("uploaded_files", []):
            path = file_info.get("local_path")
            if path and os.path.exists(path):
                os.remove(path)
        return await self.repo.delete(company_id)

    async def get_search_history(self, company_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        cursor = (
            self.repo.collection.database.get_collection("search_history")
            .find({"company_id": company_id})
            .sort("searched_at", -1)
            .limit(limit)
        )
        items = []
        async for entry in cursor:
            entry_id = entry.get("_id")
            if entry_id is not None:
                entry["id"] = str(entry_id)
                entry["_id"] = str(entry_id)
            items.append(entry)
        return items

    async def _get_owned_profile(self, company_id: str, owner_user_id: str) -> Optional[Dict[str, Any]]:
        profile = await self.repo.get_by_id(company_id)
        if not profile:
            return None
        if profile.get("owner_user_id") != owner_user_id:
            return None
        return profile

    async def _broadcast_progress(
        self,
        job: str,
        job_id: str,
        status: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        payload = {
            "type": "JOB_PROGRESS",
            "job": job,
            "job_id": job_id,
            "status": status,
            "progress": {
                "current": current,
                "total": total,
                "percent": round((current / total), 4) if total else 0,
            },
            "message": message,
            "ts": utcnow().isoformat(),
        }
        await manager.broadcast(payload)

    def _normalize_error_message(self, exc: Exception) -> str:
        if isinstance(exc, RetryError):
            last_attempt = getattr(exc, "last_attempt", None)
            last_exc = last_attempt.exception() if last_attempt else None
            if last_exc:
                return str(last_exc)
        return str(exc)

    def _serialize(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        if not profile:
            return profile
        profile_data = dict(profile)
        profile_id = profile_data.get("_id")
        if profile_id is not None:
            profile_data["id"] = str(profile_id)
            profile_data["_id"] = str(profile_id)
        return profile_data

    async def create_profile(self, files: List[UploadFile], company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Backward-compatible helper used by legacy endpoint.
        Creates a company, uploads files, and starts processing.
        """
        owner_user_id = str(uuid.uuid4())
        profile = await self.create_company(
            owner_user_id=owner_user_id,
            name=company_name or "Unnamed Company",
            company_url="https://example.com",
            experience_years=0,
        )
        company_id = profile["company_id"]
        await self.upload_documents(company_id=company_id, owner_user_id=owner_user_id, files=files)
        await self.start_processing(company_id=company_id, owner_user_id=owner_user_id)
        latest = await self.get_profile(company_id)
        return latest or profile
