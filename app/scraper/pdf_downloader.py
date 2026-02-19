"""
Async PDF download utility.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Optional

import aiofiles
import aiohttp

from app.config import settings
from app.utils.helpers import ensure_dir, sha256_file, safe_filename


class PDFDownloader:
    """Download and validate PDFs."""

    def __init__(self) -> None:
        ensure_dir(settings.TENDER_PDF_DIR)

    async def download_pdf(self, url: str, filename_hint: Optional[str] = None) -> Optional[str]:
        if not url:
            return None

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                temp_name = f"tmp_{uuid.uuid4().hex}.pdf"
                temp_path = os.path.join(settings.TENDER_PDF_DIR, temp_name)
                size = 0

                async with aiofiles.open(temp_path, "wb") as handle:
                    async for chunk in response.content.iter_chunked(8192):
                        if not chunk:
                            continue
                        size += len(chunk)
                        if size > settings.MAX_UPLOAD_SIZE:
                            await handle.close()
                            os.remove(temp_path)
                            return None
                        await handle.write(chunk)

        if not self._is_valid_pdf(temp_path):
            os.remove(temp_path)
            return None

        file_hash = sha256_file(temp_path)
        safe_name = safe_filename(filename_hint or file_hash)
        final_name = f"{safe_name}_{file_hash[:8]}.pdf"
        final_path = os.path.join(settings.TENDER_PDF_DIR, final_name)

        if os.path.exists(final_path):
            os.remove(temp_path)
            return final_path

        os.replace(temp_path, final_path)
        return final_path

    def _is_valid_pdf(self, path: str) -> bool:
        try:
            with open(path, "rb") as handle:
                header = handle.read(4)
            return header == b"%PDF"
        except OSError:
            return False


async def download_with_retry(url: str, filename_hint: Optional[str] = None, retries: int = 3) -> Optional[str]:
    downloader = PDFDownloader()
    for attempt in range(retries):
        result = await downloader.download_pdf(url, filename_hint=filename_hint)
        if result:
            return result
        await asyncio.sleep(2 ** attempt)
    return None
