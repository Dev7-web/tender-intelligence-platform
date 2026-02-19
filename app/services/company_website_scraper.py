"""
Best-effort company website scraper for onboarding step 1 enrichment.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

PREFERRED_PATH_HINTS = [
    "/about",
    "/company",
    "/who-we-are",
    "/services",
    "/solutions",
    "/products",
    "/projects",
    "/portfolio",
    "/case-studies",
    "/clients",
    "/contact",
]


class CompanyWebsiteScraper:
    def __init__(self) -> None:
        self.max_pages = settings.WEBSITE_SCRAPE_MAX_PAGES
        self.max_chars = settings.WEBSITE_SCRAPE_MAX_CHARS
        self.timeout = settings.WEBSITE_SCRAPE_TIMEOUT_SECONDS

    async def scrape(self, company_url: str) -> Dict[str, object]:
        if not company_url:
            return {
                "status": "failed",
                "pages": [],
                "extracted_text": "",
                "last_error": "Company URL is required",
            }

        normalized = company_url.strip()
        if not normalized.startswith("http://") and not normalized.startswith("https://"):
            normalized = f"https://{normalized}"

        base = urlparse(normalized)
        if not base.netloc:
            return {
                "status": "failed",
                "pages": [],
                "extracted_text": "",
                "last_error": "Invalid company URL",
            }

        visited: Set[str] = set()
        queued: deque[str] = deque([normalized])
        pages: List[str] = []
        chunks: List[str] = []

        try:
            timeout = httpx.Timeout(self.timeout)
            headers = {
                "User-Agent": (
                    "TenderAgentBot/1.0 (+https://localhost) "
                    "Mozilla/5.0 (compatible; TenderAgentBot/1.0)"
                )
            }
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
                preferred_urls = [urljoin(normalized, path) for path in PREFERRED_PATH_HINTS]
                for preferred in preferred_urls:
                    if preferred not in queued:
                        queued.append(preferred)

                while queued and len(pages) < self.max_pages and self._total_len(chunks) < self.max_chars:
                    url = queued.popleft()
                    if url in visited:
                        continue
                    if not self._is_same_domain(base.netloc, url):
                        continue
                    visited.add(url)

                    try:
                        response = await client.get(url)
                    except Exception as exc:
                        logger.info("company.website_fetch_failed", url=url, error=str(exc))
                        continue

                    if response.status_code >= 400:
                        continue

                    content_type = (response.headers.get("content-type") or "").lower()
                    if "text/html" not in content_type:
                        continue

                    html = response.text
                    text, links = self._extract_content_and_links(html, url)
                    if text:
                        pages.append(url)
                        chunks.append(text)

                    for link in links:
                        if link not in visited and self._is_same_domain(base.netloc, link):
                            queued.append(link)

                    if len(pages) >= self.max_pages:
                        break

            extracted_text = "\n\n".join(chunks)
            if len(extracted_text) > self.max_chars:
                extracted_text = extracted_text[: self.max_chars]

            status = "success" if pages else "failed"
            error = None if pages else "No extractable website content found"
            return {
                "status": status,
                "pages": pages,
                "extracted_text": extracted_text,
                "last_error": error,
            }
        except Exception as exc:
            logger.info("company.website_scrape_failed", url=normalized, error=str(exc))
            return {
                "status": "failed",
                "pages": pages,
                "extracted_text": "\n\n".join(chunks)[: self.max_chars],
                "last_error": str(exc),
            }

    def _extract_content_and_links(self, html: str, page_url: str) -> Tuple[str, List[str]]:
        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "noscript", "svg", "img", "video"]):
            tag.decompose()

        for selector in ["nav", "footer", "header", "aside"]:
            for node in soup.select(selector):
                node.decompose()

        content_parts: List[str] = []
        for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            text = tag.get_text(" ", strip=True)
            if not text:
                continue
            if len(text) < 3:
                continue
            content_parts.append(text)

        links: List[str] = []
        for anchor in soup.find_all("a", href=True):
            href = (anchor.get("href") or "").strip()
            if not href:
                continue
            if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            absolute = urljoin(page_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            if any(parsed.path.lower().endswith(ext) for ext in [".pdf", ".jpg", ".png", ".zip", ".js", ".css"]):
                continue
            links.append(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")

        return "\n".join(content_parts), links

    def _is_same_domain(self, base_domain: str, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        base = base_domain.lower()
        return host == base or host.endswith(f".{base}")

    def _total_len(self, chunks: List[str]) -> int:
        return sum(len(chunk) for chunk in chunks)