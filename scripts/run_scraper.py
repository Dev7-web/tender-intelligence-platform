"""Manual scraper runner."""

import argparse
import asyncio

from app.database.mongodb import get_database
from app.scraper.gem_scraper import GemScraper
from app.services.tender_service import TenderService


async def run(max_pages: int, max_bids: int, test: bool) -> None:
    async with GemScraper() as scraper:
        bids = await scraper.scrape_bids(max_pages=max_pages, max_bids=max_bids)
        if test:
            print(f"Scraped {len(bids)} bids")
            return

        db = get_database()
        service = TenderService(db)
        for bid in bids:
            await service.create_or_update_from_scrape(bid)
            await service.process_tender(bid.get("bid_id"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--max-bids", type=int, default=20)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    asyncio.run(run(args.max_pages, args.max_bids, args.test))
