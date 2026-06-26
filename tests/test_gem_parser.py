from datetime import datetime, timezone

from app.scraper.parser import parse_bid_cards


def test_parse_bid_dates_as_ist_and_convert_to_utc():
    html = """
    <div class="card">
      <a href="/showbidDocument/123">GEM/2026/B/1234567</a>
      Items: Router Supply
      Quantity: 10
      Department: IT Department
      Start Date: 26-06-2026 09:00 AM
      End Date: 26-06-2026 03:15 PM
      Bid Type: Open
    </div>
    """

    [bid] = parse_bid_cards(html)

    assert bid["start_date"] == datetime(2026, 6, 26, 3, 30, tzinfo=timezone.utc)
    assert bid["end_date"] == datetime(2026, 6, 26, 9, 45, tzinfo=timezone.utc)


def test_parse_card_uses_bid_no_as_primary_id_and_ra_no_separately():
    html = """
    <div class="card">
      <a href="/showbidDocument/123">Bid No.: GEM/2026/B/7566492</a>
      <a href="/showbidDocument/ra">RA No: GEM/2026/R/688292</a>
      Items: X-RAY FILM(PART NO -651-PC010...
      Quantity: 10000
      Department Name And Address: Ministry of Defence Department of Defence Production
      Start Date: 27-06-2026 04:00 PM
      End Date: 30-06-2026 09:00 AM
    </div>
    """

    bids = parse_bid_cards(html)

    assert len(bids) == 1
    assert bids[0]["bid_id"] == "GEM/2026/B/7566492"
    assert bids[0]["ra_no"] == "GEM/2026/R/688292"
