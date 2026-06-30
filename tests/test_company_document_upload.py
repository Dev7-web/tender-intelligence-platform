import base64
import io

import fitz
import pytest

from app.config import settings
from app.processors.document_extractor import DocumentExtractor
from app.services import company_service as company_service_module
from app.services.company_service import CompanyService


ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class DummyUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str = "application/octet-stream"):
        self.filename = filename
        self._buffer = io.BytesIO(content)
        self.content_type = content_type

    async def read(self, size: int = -1):
        return self._buffer.read(size)


def make_image_only_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(72, 72, 144, 144), stream=ONE_PIXEL_PNG)
    payload = doc.tobytes()
    doc.close()
    return payload


def make_text_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Company registration certificate")
    payload = doc.tobytes()
    doc.close()
    return payload


def close_created_task(coro):
    coro.close()

    class DummyTask:
        pass

    return DummyTask()


def fail_if_task_created(_coro):
    raise AssertionError("Profile rebuild should not be scheduled")


def test_document_extractor_detects_image_only_pdf(tmp_path):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(make_image_only_pdf())

    extractor = DocumentExtractor()

    assert extractor.extract_text(str(pdf_path)) == ""
    assert extractor.needs_ocr(str(pdf_path)) is True


def test_document_extractor_does_not_flag_text_pdf_as_ocr(tmp_path):
    pdf_path = tmp_path / "text.pdf"
    pdf_path.write_bytes(make_text_pdf())

    extractor = DocumentExtractor()

    assert extractor.extract_text(str(pdf_path))
    assert extractor.needs_ocr(str(pdf_path)) is False


@pytest.mark.asyncio
async def test_image_only_pdf_upload_is_marked_needs_ocr_without_reprocessing(fake_db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "PROFILE_UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(company_service_module.asyncio, "create_task", fail_if_task_created)

    service = CompanyService(fake_db)
    company = await service.create_company(
        owner_user_id="user-1",
        name="Demo InfraTech",
        company_url="https://example.com",
        experience_years=8,
    )

    pdf_payload = make_image_only_pdf()

    result = await service.upload_documents(
        company_id=company["company_id"],
        owner_user_id="user-1",
        files=[DummyUploadFile("certificate.pdf", pdf_payload, "application/pdf")],
    )

    assert result["reprocessing"] is False
    assert result["files"][0]["status"] == "needs_ocr"
    assert result["files"][0]["extract_status"] == "needs_ocr"
    assert result["files"][0]["extracted_text_len"] == 0

    profile = await service.get_profile(company["company_id"], owner_user_id="user-1")
    assert profile["uploaded_files"][0]["extract_status"] == "needs_ocr"
    assert profile["status"]["files_processed"] == 0
    assert profile["status"]["total_files"] == 1

    duplicate = await service.upload_documents(
        company_id=company["company_id"],
        owner_user_id="user-1",
        files=[DummyUploadFile("certificate.pdf", pdf_payload, "application/pdf")],
    )

    assert duplicate["reprocessing"] is False
    assert duplicate["files"][0]["status"] == "already_exists"
    assert duplicate["files"][0]["extract_status"] == "needs_ocr"


@pytest.mark.asyncio
async def test_text_file_upload_still_schedules_reprocessing(fake_db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "PROFILE_UPLOAD_DIR", str(tmp_path))
    created_tasks = []

    def fake_create_task(coro):
        created_tasks.append(coro)
        return close_created_task(coro)

    monkeypatch.setattr(company_service_module.asyncio, "create_task", fake_create_task)

    service = CompanyService(fake_db)
    company = await service.create_company(
        owner_user_id="user-1",
        name="Demo InfraTech",
        company_url="https://example.com",
        experience_years=8,
    )

    result = await service.upload_documents(
        company_id=company["company_id"],
        owner_user_id="user-1",
        files=[DummyUploadFile("profile.txt", b"Road and solar delivery experience", "text/plain")],
    )

    assert result["reprocessing"] is True
    assert result["files"][0]["status"] == "extracted"
    assert created_tasks
