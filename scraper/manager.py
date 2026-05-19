"""
ScraperManager — orchestrates one or more scrapers and returns combined results.

Design goals
------------
* Single entry point for the CLI and the Flask API.
* Scraper selection is driven by a simple platform list (strings).
* Results are deduplicated before being returned.
* Adding a new scraper requires only registering it in SCRAPER_REGISTRY.
"""
from __future__ import annotations

from typing import Literal

from parsers.models import Product
from scraper.amazon_scraper import AmazonScraper
from scraper.daraz_scraper import DarazScraper
from scraper.generic_scraper import GenericScraper
from parsers.site_configs import SITE_CONFIGS
from utils.http_client import build_session
from utils.helpers import deduplicate
from utils.logger import setup_logger

logger = setup_logger(__name__)

Platform = Literal["amazon", "daraz", "ebay", "walmart", "noon", "all"]

# Search URL templates for generic scrapers
GENERIC_SEARCH_URLS: dict[str, str] = {
    "ebay":    "https://www.ebay.com/sch/i.html?_nkw={query}",
    "walmart": "https://www.walmart.com/search?q={query}",
    "noon":    "https://www.noon.com/uae-en/search/?q={query}",
}


class ScraperManager:
    """
    High-level coordinator for the E-commerce Tracker.

    Usage::

        manager = ScraperManager(keyword="iPhone 13", platforms=["amazon", "daraz"])
        products = manager.run()
    """

    def __init__(
        self,
        keyword: str,
        platforms: list[str] | None = None,
        max_results_per_platform: int = 20,
    ) -> None:
        self.keyword = keyword.strip()
        self.platforms = [p.lower() for p in (platforms or ["all"])]
        self.max_results = max_results_per_platform
        self.session = build_session()
        self._results: list[Product] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> list[Product]:
        """
        Execute all selected scrapers sequentially and return combined,
        deduplicated results.

        Returns:
            List of unique Product objects.
        """
        scrapers = self._build_scrapers()
        if not scrapers:
            logger.warning("No scrapers configured for platforms: %s", self.platforms)
            return []

        all_products: list[Product] = []
        for scraper in scrapers:
            logger.info("Running scraper: %s", scraper.SOURCE)
            results = scraper.scrape()
            logger.info("  → %d products from %s", len(results), scraper.SOURCE)
            all_products.extend(results)

        unique = deduplicate(all_products)
        logger.info(
            "Total: %d products (%d after deduplication).",
            len(all_products), len(unique),
        )
        self._results = unique
        return unique

    @property
    def results(self) -> list[Product]:
        return self._results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_scrapers(self) -> list:
        active: list = []
        wants_all = "all" in self.platforms

        if wants_all or "amazon" in self.platforms:
            active.append(AmazonScraper(self.session, self.keyword, self.max_results))

        if wants_all or "daraz" in self.platforms:
            active.append(DarazScraper(self.session, self.keyword, self.max_results))

        # Generic scrapers registered in SITE_CONFIGS
        for key, config in SITE_CONFIGS.items():
            if key.startswith("_"):   # skip template entries
                continue
            if wants_all or key in self.platforms:
                url_template = GENERIC_SEARCH_URLS.get(key)
                if url_template:
                    active.append(
                        GenericScraper(
                            session=self.session,
                            keyword=self.keyword,
                            config=config,
                            search_url_template=url_template,
                            max_results=self.max_results,
                        )
                    )

        return active
