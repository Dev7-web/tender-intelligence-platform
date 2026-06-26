import pytest

from app.scraper.gem_scraper import GemScraper


def _card(bid_id: str, ra_no: str | None = None) -> str:
    ra_html = f'<a href="/showbidDocument/ra">RA No: {ra_no}</a>' if ra_no else ""
    return f"""
    <div class="card">
      <a href="/showbidDocument/{bid_id}">Bid No.: {bid_id}</a>
      {ra_html}
      Items: Test Item
      Quantity: 1
      Department: Test Department
      Start Date: 27-06-2026 04:00 PM
      End Date: 30-06-2026 09:00 AM
    </div>
    """


class FakeNextButton:
    def __init__(self, page):
        self.page = page

    def click(self):
        self.page.index += 1


class FakeSortElement:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    def click(self):
        if self.selector == "#Bid-Start-Date-Latest":
            self.page.current_sort = "Bid Start Date: Latest First"
            self.page.sort_selected = True

    def inner_text(self):
        return self.page.current_sort


class FakePage:
    def __init__(self, pages, *, sort_mode="dropdown", can_apply_sort=True):
        self.pages = pages
        self.index = 0
        self.sort_mode = sort_mode
        self.can_apply_sort = can_apply_sort
        self.sort_selected = False
        self.current_sort = "Bid End Date: Oldest First"
        self.goto_urls = []

    def goto(self, url, timeout=None, wait_until=None):
        self.goto_urls.append(url)

    def wait_for_load_state(self, *_args, **_kwargs):
        return None

    def wait_for_function(self, _expression, sort_label, **_kwargs):
        if self.current_sort != sort_label:
            raise TimeoutError("sort label did not update")
        return True

    def evaluate(self, expression, *args):
        if "Ongoing Bids/RA" in expression:
            return True
        if "select.value" in expression:
            if self.sort_mode == "native":
                self.sort_selected = self.can_apply_sort
                return self.can_apply_sort
            return False
        if "selectedIndex" in expression:
            return self.sort_mode == "native" and self.sort_selected
        return True

    def content(self):
        return self.pages[self.index]

    def query_selector(self, selector):
        if selector == "#currentSort" and self.sort_mode == "dropdown":
            return FakeSortElement(self, selector)
        if selector == "#Bid-Start-Date-Latest" and self.sort_mode == "dropdown" and self.can_apply_sort:
            return FakeSortElement(self, selector)
        if selector == "text=Next" and self.index + 1 < len(self.pages):
            return FakeNextButton(self)
        return None


def _scraper_with_page(page):
    scraper = GemScraper()
    scraper.page = page
    scraper._sync_random_delay = lambda: None
    return scraper


def test_scraper_applies_latest_sort_and_stops_after_known_tenders():
    page = FakePage(
        [
            _card("GEM/2026/B/1001") + _card("GEM/2026/B/1002"),
            _card("GEM/2026/B/1003"),
        ],
        sort_mode="dropdown",
    )
    scraper = _scraper_with_page(page)
    try:
        result = scraper._sync_scrape_bids(
            max_pages=5,
            max_bids=10,
            known_bid_ids={"GEM/2026/B/1001", "GEM/2026/B/1002"},
            stop_after_known=2,
        )
    finally:
        scraper._executor.shutdown(wait=False, cancel_futures=True)

    assert result.bids == []
    assert result.pages_scraped == 1
    assert result.known_tenders_skipped == 2
    assert result.sort_applied is True
    assert page.current_sort == "Bid Start Date: Latest First"
    assert page.goto_urls == [GemScraper.BASE_URL]


def test_scraper_respects_max_bids():
    page = FakePage([
        _card("GEM/2026/B/2001") + _card("GEM/2026/B/2002") + _card("GEM/2026/B/2003")
    ])
    scraper = _scraper_with_page(page)
    try:
        result = scraper._sync_scrape_bids(max_pages=5, max_bids=2, known_bid_ids=set(), stop_after_known=20)
    finally:
        scraper._executor.shutdown(wait=False, cancel_futures=True)

    assert [bid["bid_id"] for bid in result.bids] == ["GEM/2026/B/2001", "GEM/2026/B/2002"]
    assert result.pages_scraped == 1


def test_scraper_respects_max_pages():
    page = FakePage([
        _card("GEM/2026/B/3001"),
        _card("GEM/2026/B/3002"),
    ])
    scraper = _scraper_with_page(page)
    try:
        result = scraper._sync_scrape_bids(max_pages=1, max_bids=10, known_bid_ids=set(), stop_after_known=20)
    finally:
        scraper._executor.shutdown(wait=False, cancel_futures=True)

    assert [bid["bid_id"] for bid in result.bids] == ["GEM/2026/B/3001"]
    assert result.pages_scraped == 1


def test_scraper_fails_when_latest_sort_cannot_be_applied():
    page = FakePage([_card("GEM/2026/B/4001")], sort_mode="none", can_apply_sort=False)
    scraper = _scraper_with_page(page)
    try:
        with pytest.raises(RuntimeError, match="Unable to apply GeM sort option"):
            scraper._sync_scrape_bids(max_pages=1, max_bids=10, known_bid_ids=set(), stop_after_known=20)
    finally:
        scraper._executor.shutdown(wait=False, cancel_futures=True)


def test_scraper_keeps_native_select_sort_fallback():
    page = FakePage([_card("GEM/2026/B/5001")], sort_mode="native")
    scraper = _scraper_with_page(page)
    try:
        result = scraper._sync_scrape_bids(max_pages=1, max_bids=10, known_bid_ids=set(), stop_after_known=20)
    finally:
        scraper._executor.shutdown(wait=False, cancel_futures=True)

    assert result.sort_applied is True
    assert [bid["bid_id"] for bid in result.bids] == ["GEM/2026/B/5001"]
