"""
Generic / configurable HTML parser for arbitrary e-commerce sites.

Usage
-----
Define a SiteConfig with the CSS selectors specific to a target site,
then call parse_search_results(html, config).

This makes adding a new site a zero-code-change operation — just add a
new SiteConfig entry to parsers/site_configs.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup, Tag

from parsers.models import Product
from utils.helpers import clean_text, parse_price, parse_rating, parse_review_count, normalise_url
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class SiteConfig:
    """
    CSS-selector map for a single e-commerce site.

    Set any selector to None / "" to skip that field gracefully.
    """
    name: str                              # Human-readable site name
    base_url: str                          # Used to absolutise relative URLs
    currency: str = "USD"                  # ISO-4217 code

    # Container selector — one card per product
    card_selector: str = "div.product"

    # Field selectors (relative to each card)
    title_selector: str = ""
    price_selector: str = ""
    rating_selector: str = ""
    reviews_selector: str = ""
    url_selector: str = ""                 # selector for <a> tag; href extracted
    availability_selector: str = ""
    image_selector: str = ""              # selector for <img>; src extracted

    # When a field is found, use .get_text() unless an attribute name is given
    url_attribute: str = "href"
    image_attribute: str = "src"

    # Extra per-site metadata to attach to every product
    extra: dict = field(default_factory=dict)


def parse_search_results(
    html: str,
    config: SiteConfig,
    max_results: int = 20,
) -> list[Product]:
    """
    Extract products from HTML using the provided SiteConfig.

    Args:
        html: Raw HTML of the search-results page.
        config: Site-specific CSS-selector configuration.
        max_results: Maximum number of products to return.

    Returns:
        List of Product instances.
    """
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(config.card_selector)
    logger.info(
        "Generic parser (%s) found %d cards with selector '%s'.",
        config.name, len(cards), config.card_selector,
    )

    products: list[Product] = []
    for card in cards[:max_results]:
        product = _parse_card(card, config)
        if product:
            products.append(product)

    logger.info("Generic parser (%s) extracted %d valid products.", config.name, len(products))
    return products


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _text(card: Tag, selector: str) -> str:
    if not selector:
        return "N/A"
    el = card.select_one(selector)
    return clean_text(el.get_text()) if el else "N/A"


def _attr(card: Tag, selector: str, attribute: str) -> str:
    if not selector:
        return "N/A"
    el = card.select_one(selector)
    if el:
        val = el.get(attribute, "")
        return clean_text(val) if val else "N/A"
    return "N/A"


def _parse_card(card: Tag, config: SiteConfig) -> Optional[Product]:
    try:
        title = _text(card, config.title_selector)
        if not title or title == "N/A":
            return None

        raw_price    = _text(card, config.price_selector)
        raw_rating   = _text(card, config.rating_selector)
        raw_reviews  = _text(card, config.reviews_selector)
        raw_avail    = _text(card, config.availability_selector)

        url = _attr(card, config.url_selector, config.url_attribute)
        url = normalise_url(url, config.base_url) if url != "N/A" else "N/A"

        image_url = _attr(card, config.image_selector, config.image_attribute)
        if image_url == "N/A":
            # Fallback: try data-src (lazy-loaded images)
            image_url_lazy = _attr(card, config.image_selector, "data-src")
            if image_url_lazy != "N/A":
                image_url = image_url_lazy

        availability = raw_avail if raw_avail != "N/A" else "Unknown"

        return Product(
            title=title,
            price=parse_price(raw_price),
            rating=parse_rating(raw_rating),
            review_count=parse_review_count(raw_reviews),
            url=url,
            availability=availability,
            source=config.name.lower(),
            currency=config.currency,
            image_url=image_url if image_url != "N/A" else None,
            extra=dict(config.extra),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Generic parser (%s) skipping card: %s", config.name, exc)
        return None
