"""
Abstract base class that every scraper must implement.

Contract
--------
- __init__ receives shared HTTP session + keyword + optional max_results
- scrape() returns a list[Product]
- Subclasses override _build_url() and _parse_response()

This keeps the main loop in scraper/manager.py completely scraper-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import requests

from parsers.models import Product
from utils.http_client import polite_get
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseScraper(ABC):
    """
    Abstract scraper interface.

    All scrapers must inherit from this class and implement the two
    abstract methods.
    """

    #: Human-readable label used in logs and output (override in subclass)
    SOURCE: str = "unknown"

    def __init__(
        self,
        session: requests.Session,
        keyword: str,
        max_results: int = 20,
    ) -> None:
        self.session = session
        self.keyword = keyword
        self.max_results = max_results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self) -> list[Product]:
        """
        Fetch the search-results page and parse it into Product objects.

        Returns an empty list on network or parse failure; never raises.
        """
        url = self._build_url()
        logger.info("[%s] Fetching: %s", self.SOURCE, url)

        response = polite_get(self.session, url)
        if response is None:
            logger.warning("[%s] No response for keyword '%s'.", self.SOURCE, self.keyword)
            return []

        try:
            products = self._parse_response(response)
            logger.info("[%s] Parsed %d products.", self.SOURCE, len(products))
            return products[: self.max_results]
        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] Parse error: %s", self.SOURCE, exc, exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_url(self) -> str:
        """Return the search URL for self.keyword."""

    @abstractmethod
    def _parse_response(self, response: requests.Response) -> list[Product]:
        """Parse the HTTP response and return a list of Product objects."""
