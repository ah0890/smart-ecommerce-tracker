"""
Daraz scraper — searches daraz.pk for a keyword.

Daraz embeds product data as JSON inside a <script> tag, which means
the static HTML is parseable without a headless browser.
"""
from __future__ import annotations

from urllib.parse import quote_plus

import requests

from parsers.models import Product
from parsers import daraz_parser
from scraper.base_scraper import BaseScraper

# Daraz exposes a clean JSON catalogue endpoint on /catalog
BASE_SEARCH_URL = (
    "https://www.daraz.pk/catalog/?q={query}&_keyori=ss&from=input&spm=a2a0e.11779170.search.d_go"
)


class DarazScraper(BaseScraper):
    SOURCE = "daraz"

    def _build_url(self) -> str:
        return BASE_SEARCH_URL.format(query=quote_plus(self.keyword))

    def _parse_response(self, response: requests.Response) -> list[Product]:
        return daraz_parser.parse_search_results(response.text, self.max_results)
