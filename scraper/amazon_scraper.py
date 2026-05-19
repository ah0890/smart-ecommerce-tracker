"""
Amazon scraper — searches amazon.com for a keyword and parses results.

Note: Amazon aggressively blocks scrapers.  This implementation uses
polite delays and browser-like headers.  It will work for casual,
low-frequency research usage.  Do NOT run at high volume.
"""
from __future__ import annotations

from urllib.parse import quote_plus

import requests

from parsers.models import Product
from parsers import amazon_parser
from scraper.base_scraper import BaseScraper

BASE_SEARCH_URL = "https://www.amazon.com/s?k={query}&ref=nb_sb_noss"


class AmazonScraper(BaseScraper):
    SOURCE = "amazon"

    def _build_url(self) -> str:
        return BASE_SEARCH_URL.format(query=quote_plus(self.keyword))

    def _parse_response(self, response: requests.Response) -> list[Product]:
        return amazon_parser.parse_search_results(response.text, self.max_results)
