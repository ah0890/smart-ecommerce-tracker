"""
Generic scraper — uses a SiteConfig to scrape any supported site.

Adding a new site requires only a new entry in parsers/site_configs.py.
"""
from __future__ import annotations

from urllib.parse import quote_plus

import requests

from parsers.models import Product
from parsers.generic_parser import SiteConfig, parse_search_results
from scraper.base_scraper import BaseScraper


class GenericScraper(BaseScraper):
    """
    A configurable scraper driven entirely by a SiteConfig.

    Args:
        session: Shared HTTP session.
        keyword: Search keyword.
        config: SiteConfig for the target site.
        search_url_template: URL template with a ``{query}`` placeholder.
        max_results: Maximum products to return.
    """

    def __init__(
        self,
        session: requests.Session,
        keyword: str,
        config: SiteConfig,
        search_url_template: str,
        max_results: int = 20,
    ) -> None:
        super().__init__(session, keyword, max_results)
        self.config = config
        self.search_url_template = search_url_template
        self.SOURCE = config.name.lower()

    def _build_url(self) -> str:
        return self.search_url_template.format(query=quote_plus(self.keyword))

    def _parse_response(self, response: requests.Response) -> list[Product]:
        return parse_search_results(response.text, self.config, self.max_results)
