"""Scraper modules for E-commerce Tracker."""
from scraper.base_scraper import BaseScraper
from scraper.amazon_scraper import AmazonScraper
from scraper.daraz_scraper import DarazScraper
from scraper.generic_scraper import GenericScraper
from scraper.manager import ScraperManager

__all__ = [
    "BaseScraper",
    "AmazonScraper",
    "DarazScraper",
    "GenericScraper",
    "ScraperManager",
]
