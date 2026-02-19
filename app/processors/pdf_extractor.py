"""
PDF text extraction using PyMuPDF.
"""

from __future__ import annotations

import re
from typing import Optional

import fitz

from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """Extract text from PDFs."""

    def extract_text(self, path: str) -> Optional[str]:
        try:
            doc = fitz.open(path)
        except Exception as exc:
            logger.info("pdf.open_failed", path=path, error=str(exc))
            return None

        if doc.is_encrypted:
            logger.info("pdf.encrypted", path=path)
            doc.close()
            return None

        text_parts = []
        for page in doc:
            text_parts.append(page.get_text("text"))
        doc.close()

        text = "\n".join(text_parts)
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        cleaned = re.sub(r"Page\s+\d+", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
