"""
GeM Portal Scraper using Playwright.

Uses sync_playwright in a thread executor to avoid Windows asyncio subprocess issues.
"""

from __future__ import annotations

import asyncio
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set

from playwright.sync_api import sync_playwright, Browser, Page

from app.config import settings
from app.scraper.parser import parse_bid_cards
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScrapeResult:
    bids: List[Dict[str, Any]]
    pages_scraped: int = 0
    known_tenders_skipped: int = 0
    sort_applied: bool = False

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self.bids)

    def __len__(self) -> int:
        return len(self.bids)


class GemScraper:
    """Scraper for GeM bid listings using sync Playwright in a thread."""

    BASE_URL = "https://bidplus.gem.gov.in/all-bids"

    PAGE_LOAD_TIMEOUT = 60000
    ELEMENT_TIMEOUT = 30000

    def __init__(self) -> None:
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._initialized = False
        # Playwright sync objects must stay on one thread for their lifetime.
        self._executor: Optional[ThreadPoolExecutor] = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="gem-scraper",
        )

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False

    async def initialize(self) -> None:
        """Initialize the scraper in a background thread."""
        await self._run_in_executor(self._sync_initialize)

    def _sync_initialize(self) -> None:
        """Synchronous initialization - runs in thread."""
        logger.info("scraper.initializing", headless=settings.SCRAPER_HEADLESS)
        self.playwright = self._start_playwright_with_windows_fallback()
        logger.info("scraper.playwright_started")
        self.browser = self.playwright.chromium.launch(
            headless=settings.SCRAPER_HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        logger.info("scraper.browser_launched")
        self.page = self.browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        logger.info("scraper.page_created")
        self._initialized = True

    def _start_playwright_with_windows_fallback(self):
        """Start Playwright and recover from Windows SelectorEventLoopPolicy limitations."""
        if self._is_windows_selector_policy():
            logger.warning(
                "scraper.windows_selector_policy_detected",
                message=(
                    "WindowsSelectorEventLoopPolicy does not support asyncio subprocesses. "
                    "Switching to WindowsProactorEventLoopPolicy for Playwright startup."
                ),
            )
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        return sync_playwright().start()

    @staticmethod
    def _is_windows_selector_policy() -> bool:
        if sys.platform != "win32":
            return False
        selector_policy_type = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
        if selector_policy_type is None:
            return False
        return isinstance(asyncio.get_event_loop_policy(), selector_policy_type)

    async def close(self) -> None:
        """Close the scraper in a background thread."""
        try:
            if self._initialized:
                await self._run_in_executor(self._sync_close)
        finally:
            if self._executor is not None:
                self._executor.shutdown(wait=False, cancel_futures=True)
                self._executor = None

    def _sync_close(self) -> None:
        """Synchronous close - runs in thread."""
        if self.page is not None:
            self.page.close()
        if self.browser is not None:
            self.browser.close()
        if self.playwright is not None:
            self.playwright.stop()
        self._initialized = False

    async def scrape_bids(
        self,
        max_pages: Optional[int] = None,
        max_bids: Optional[int] = None,
        known_bid_ids: Optional[Iterable[str]] = None,
        stop_after_known: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> ScrapeResult:
        """Scrape bids from GeM listing pages."""
        return await self._run_in_executor(
            self._sync_scrape_bids,
            max_pages,
            max_bids,
            set(known_bid_ids or []),
            stop_after_known,
            search_query,
        )

    def _sync_scrape_bids(
        self,
        max_pages: Optional[int] = None,
        max_bids: Optional[int] = None,
        known_bid_ids: Optional[Set[str]] = None,
        stop_after_known: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> ScrapeResult:
        """Synchronous scraping - runs in thread."""
        if self.page is None:
            raise RuntimeError("Scraper not initialized")

        max_pages = max_pages or settings.SCRAPE_MAX_PAGES
        max_bids = max_bids or settings.SCRAPE_MAX_BIDS
        known_bid_ids = known_bid_ids or set()
        stop_after_known = stop_after_known if stop_after_known is not None else settings.SCRAPE_STOP_AFTER_KNOWN_BIDS

        logger.info("scraper.start", max_pages=max_pages, max_bids=max_bids, search_query=search_query)
        sort_applied = self._sync_prepare_latest_listing(search_query=search_query)

        collected: List[Dict[str, Any]] = []
        seen: set = set()
        pages_scraped = 0
        known_tenders_skipped = 0
        consecutive_known = 0

        for page_index in range(max_pages):
            self._sync_random_delay()
            html = self.page.content()
            bids = parse_bid_cards(html)
            pages_scraped += 1

            for bid in bids:
                bid_id = bid.get("bid_id")
                if not bid_id or bid_id in seen:
                    continue
                seen.add(bid_id)

                if bid_id in known_bid_ids:
                    known_tenders_skipped += 1
                    consecutive_known += 1
                    if stop_after_known > 0 and consecutive_known >= stop_after_known:
                        logger.info(
                            "scraper.known_stop_reached",
                            consecutive_known=consecutive_known,
                            known_tenders_skipped=known_tenders_skipped,
                        )
                        return ScrapeResult(
                            bids=collected,
                            pages_scraped=pages_scraped,
                            known_tenders_skipped=known_tenders_skipped,
                            sort_applied=sort_applied,
                        )
                    continue

                consecutive_known = 0
                collected.append(bid)
                if len(collected) >= max_bids:
                    logger.info("scraper.max_bids_reached", count=len(collected))
                    return ScrapeResult(
                        bids=collected,
                        pages_scraped=pages_scraped,
                        known_tenders_skipped=known_tenders_skipped,
                        sort_applied=sort_applied,
                    )

            logger.info(
                "scraper.page_parsed",
                page=page_index + 1,
                bids=len(bids),
                total=len(collected),
                known_tenders_skipped=known_tenders_skipped,
            )

            if not self._sync_try_next_page():
                if not self._sync_try_scroll():
                    break

        return ScrapeResult(
            bids=collected,
            pages_scraped=pages_scraped,
            known_tenders_skipped=known_tenders_skipped,
            sort_applied=sort_applied,
        )

    def _sync_prepare_latest_listing(self, search_query: Optional[str] = None) -> bool:
        if self.page is None:
            raise RuntimeError("Scraper not initialized")

        sort_label = settings.SCRAPE_SORT_LABEL
        self.page.goto(self.BASE_URL, timeout=self.PAGE_LOAD_TIMEOUT, wait_until="networkidle")
        self._sync_ensure_ongoing_bids_filter()
        if search_query and not self._sync_apply_search_query(search_query):
            raise RuntimeError(f"Unable to apply GeM search query: {search_query}")

        sort_applied = self._sync_select_sort_label(sort_label)
        if sort_applied:
            self._sync_wait_for_sort_label(sort_label)

        if not sort_applied or not self._sync_verify_sort_label(sort_label):
            raise RuntimeError(f"Unable to apply GeM sort option: {sort_label}")

        return True

    def _sync_apply_search_query(self, search_query: str) -> bool:
        if self.page is None:
            return False

        query = search_query.strip()
        if not query:
            return False

        try:
            applied = bool(
                self.page.evaluate(
                    """
                    (query) => {
                        const normalize = (value) => (value || "").toLowerCase();
                        const inputs = Array.from(document.querySelectorAll("input, textarea"));
                        const input = inputs.find((item) => {
                            const haystack = [
                                item.getAttribute("placeholder"),
                                item.getAttribute("aria-label"),
                                item.getAttribute("name"),
                                item.getAttribute("id"),
                                item.getAttribute("class")
                            ].map(normalize).join(" ");
                            return haystack.includes("search")
                                || haystack.includes("keyword")
                                || haystack.includes("bid")
                                || haystack.includes("item");
                        }) || inputs.find((item) => {
                            const type = normalize(item.getAttribute("type"));
                            return type === "search" || type === "text" || !type;
                        });
                        if (!input) return false;

                        input.focus();
                        input.value = query;
                        input.dispatchEvent(new Event("input", { bubbles: true }));
                        input.dispatchEvent(new Event("change", { bubbles: true }));

                        const form = input.closest("form");
                        if (form) {
                            form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
                        }

                        const buttons = Array.from(document.querySelectorAll("button, input[type='submit']"));
                        const button = buttons.find((item) => {
                            const text = normalize(item.textContent || item.value || item.getAttribute("aria-label"));
                            return text.includes("search") || text.includes("submit");
                        });
                        if (button) button.click();
                        return true;
                    }
                    """,
                    query,
                )
            )
            if not applied:
                return False
            try:
                self.page.wait_for_load_state("networkidle", timeout=self.PAGE_LOAD_TIMEOUT)
            except Exception as exc:
                logger.info("scraper.search_networkidle_timeout", error=str(exc), search_query=query)
            time.sleep(1)
            return True
        except Exception as exc:
            logger.info("scraper.search_apply_failed", error=str(exc), search_query=query)
            return False

    def _sync_ensure_ongoing_bids_filter(self) -> None:
        if self.page is None:
            return

        try:
            self.page.evaluate(
                """
                () => {
                    const labels = Array.from(document.querySelectorAll("label"));
                    const label = labels.find((item) => (item.innerText || "").includes("Ongoing Bids/RA"));
                    if (!label) return false;
                    const input = label.querySelector("input[type='checkbox']")
                        || (label.htmlFor ? document.getElementById(label.htmlFor) : null);
                    if (!input) return false;
                    if (!input.checked) input.click();
                    return true;
                }
                """
            )
        except Exception as exc:
            logger.info("scraper.ongoing_filter_failed", error=str(exc))

    def _sync_select_sort_label(self, sort_label: str) -> bool:
        if self.page is None:
            return False

        if self._sync_select_gem_dropdown_sort(sort_label):
            return True

        return self._sync_select_native_sort(sort_label)

    def _sync_select_gem_dropdown_sort(self, sort_label: str) -> bool:
        if self.page is None:
            return False

        try:
            current_sort = self.page.query_selector("#currentSort")
            sort_option = self.page.query_selector(self._gem_sort_option_selector(sort_label))
            if not current_sort or not sort_option:
                return False

            current_sort.click()
            sort_option.click()
            return True
        except Exception as exc:
            logger.info("scraper.gem_sort_select_failed", error=str(exc))
            return False

    def _sync_select_native_sort(self, sort_label: str) -> bool:
        if self.page is None:
            return False

        try:
            return bool(
                self.page.evaluate(
                    """
                    (sortLabel) => {
                        const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
                        for (const select of Array.from(document.querySelectorAll("select"))) {
                            const option = Array.from(select.options || []).find(
                                (item) => normalize(item.textContent) === sortLabel
                            );
                            if (!option) continue;
                            select.value = option.value;
                            select.dispatchEvent(new Event("change", { bubbles: true }));
                            return true;
                        }
                        return false;
                    }
                    """,
                    sort_label,
                )
            )
        except Exception as exc:
            logger.info("scraper.sort_select_failed", error=str(exc))
            return False

    def _sync_wait_for_sort_label(self, sort_label: str) -> None:
        if self.page is None:
            return

        try:
            self.page.wait_for_load_state("networkidle", timeout=self.PAGE_LOAD_TIMEOUT)
        except Exception as exc:
            logger.info("scraper.sort_networkidle_timeout", error=str(exc))

        try:
            if self.page.query_selector("#currentSort"):
                self.page.wait_for_function(
                    """
                    (sortLabel) => {
                        const current = document.querySelector("#currentSort");
                        if (!current) return true;
                        const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
                        return normalize(current.textContent) === sortLabel;
                    }
                    """,
                    sort_label,
                    timeout=self.ELEMENT_TIMEOUT,
                )
        except Exception as exc:
            logger.info("scraper.sort_label_wait_failed", error=str(exc))

        time.sleep(1)

    def _sync_verify_sort_label(self, sort_label: str) -> bool:
        if self.page is None:
            return False

        if self._sync_verify_gem_dropdown_sort(sort_label):
            return True

        return self._sync_verify_native_sort(sort_label)

    def _sync_verify_gem_dropdown_sort(self, sort_label: str) -> bool:
        if self.page is None:
            return False

        try:
            current_sort = self.page.query_selector("#currentSort")
            if not current_sort:
                return False
            current_text = current_sort.inner_text()
            return self._normalize_text(current_text) == sort_label
        except Exception as exc:
            logger.info("scraper.gem_sort_verify_failed", error=str(exc))
            return False

    def _sync_verify_native_sort(self, sort_label: str) -> bool:
        if self.page is None:
            return False

        try:
            return bool(
                self.page.evaluate(
                    """
                    (sortLabel) => {
                        const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
                        return Array.from(document.querySelectorAll("select")).some((select) => {
                            const selected = select.options && select.options[select.selectedIndex];
                            return selected && normalize(selected.textContent) === sortLabel;
                        });
                    }
                    """,
                    sort_label,
                )
            )
        except Exception as exc:
            logger.info("scraper.sort_verify_failed", error=str(exc))
            return False

    def _gem_sort_option_selector(self, sort_label: str) -> str:
        mapping = {
            "Bid Start Date: Latest First": "#Bid-Start-Date-Latest",
            "Bid Start Date: Oldest First": "#Bid-Start-Date-Oldest",
            "Bid End Date: Latest First": "#Bid-End-Date-Latest",
            "Bid End Date: Oldest First": "#Bid-End-Date-Oldest",
        }
        return mapping.get(sort_label, f"#{sort_label.replace(':', '').replace(' ', '-')}")

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join((value or "").split()).strip()

    def _sync_try_next_page(self) -> bool:
        """Try to navigate to next page - runs in thread."""
        if self.page is None:
            return False
        try:
            next_button = self.page.query_selector("text=Next")
            if next_button:
                next_button.click()
                self.page.wait_for_load_state("networkidle", timeout=self.PAGE_LOAD_TIMEOUT)
                return True
        except Exception as exc:
            logger.info("scraper.next_failed", error=str(exc))
        return False

    def _sync_try_scroll(self) -> bool:
        """Try to scroll for more content - runs in thread."""
        if self.page is None:
            return False
        try:
            previous_height = self.page.evaluate("document.body.scrollHeight")
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            new_height = self.page.evaluate("document.body.scrollHeight")
            return new_height > previous_height
        except Exception as exc:
            logger.info("scraper.scroll_failed", error=str(exc))
            return False

    def _sync_random_delay(self) -> None:
        """Random delay between requests - runs in thread."""
        delay = random.uniform(settings.SCRAPE_MIN_DELAY, settings.SCRAPE_MAX_DELAY)
        time.sleep(delay)

    async def _run_in_executor(self, func, *args):
        executor = self._executor
        if executor is None:
            raise RuntimeError("Scraper executor is not available")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(executor, lambda: func(*args))
