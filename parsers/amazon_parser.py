"""
HTML parser for Amazon search-result pages.

Parses the static HTML returned by Amazon's search endpoint.
Handles the most common layout variants; gracefully degrades when
selectors don't match (returns None / 'N/A' for individual fields).
"""
from __future__ import annotations

from typing import Optional
from bs4 import BeautifulSoup, Tag

from parsers.models import Product
from utils.helpers import clean_text, parse_price, parse_rating, parse_review_count, normalise_url
from utils.logger import setup_logger

logger = setup_logger(__name__)

BASE_URL = "https://www.amazon.com"


def parse_search_results(html: str, max_results: int = 20) -> list[Product]:
    """
    Extract product listings from an Amazon search-results HTML page.

    Args:
        html: Raw HTML string of the search-results page.
        max_results: Maximum number of products to return.

    Returns:
        List of Product instances.
    """
    soup = BeautifulSoup(html, "html.parser")
    products: list[Product] = []

    # Amazon wraps each result in a div with data-component-type="s-search-result"
    cards = soup.select('div[data-component-type="s-search-result"]')
    logger.info("Amazon parser found %d raw cards.", len(cards))

    for card in cards[:max_results]:
        product = _parse_card(card)
        if product:
            products.append(product)

    logger.info("Amazon parser extracted %d valid products.", len(products))
    return products


def _parse_card(card: Tag) -> Optional[Product]:
    """Parse a single Amazon search-result card into a Product."""
    try:
        title = _extract_title(card)
        if not title or title == "N/A":
            return None

        price         = _extract_price(card)
        rating        = _extract_rating(card)
        review_count  = _extract_reviews(card)
        url           = _extract_url(card)
        availability  = _extract_availability(card)
        image_url     = _extract_image(card)

        return Product(
            title=title,
            price=price,
            rating=rating,
            review_count=review_count,
            url=url,
            availability=availability,
            source="amazon",
            currency="USD",
            image_url=image_url,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Skipping Amazon card due to parse error: %s", exc)
        return None


# ------------------------------------------------------------------
# Field extractors
# ------------------------------------------------------------------

def _extract_title(card: Tag) -> str:
    for selector in [
        "h2 a span",
        "span.a-size-medium.a-color-base.a-text-normal",
        "span.a-size-base-plus.a-color-base.a-text-normal",
    ]:
        el = card.select_one(selector)
        if el:
            return clean_text(el.get_text())
    return "N/A"


def _extract_price(card: Tag) -> Optional[float]:
    # Whole + fraction (e.g. $1,299 + .99)
    whole = card.select_one("span.a-price-whole")
    frac  = card.select_one("span.a-price-fraction")
    if whole:
        raw = whole.get_text().replace(",", "").rstrip(".")
        if frac:
            raw += f".{frac.get_text()}"
        return parse_price(raw)
    # Fallback: any offscreen price
    offscreen = card.select_one("span.a-offscreen")
    if offscreen:
        return parse_price(offscreen.get_text())
    return None


def _extract_rating(card: Tag) -> Optional[float]:
    el = card.select_one("span[aria-label*='out of']")
    if el:
        return parse_rating(el.get("aria-label", ""))
    el = card.select_one("span.a-icon-alt")
    if el:
        return parse_rating(el.get_text())
    return None


def _extract_reviews(card: Tag) -> Optional[int]:
    el = card.select_one("span[aria-label*='ratings']")
    if el:
        return parse_review_count(el.get("aria-label", ""))
    # Fallback: second aria-label on the ratings row
    els = card.select("a[aria-label]")
    for e in els:
        label = e.get("aria-label", "")
        if "rating" in label.lower():
            return parse_review_count(label)
    return None


def _extract_url(card: Tag) -> str:
    a = card.select_one("h2 a")
    if a and a.get("href"):
        return normalise_url(a["href"], BASE_URL)
    return "N/A"


def _extract_availability(card: Tag) -> str:
    # If price is present, assume in stock
    if card.select_one("span.a-price-whole") or card.select_one("span.a-offscreen"):
        return "In Stock"
    # Check for explicit out-of-stock signals
    for selector in ["span.a-size-small.a-color-error", "span[data-a-badge-type='stock']"]:
        el = card.select_one(selector)
        if el and "unavailable" in el.get_text().lower():
            return "Out of Stock"
    return "Unknown"


def _extract_image(card: Tag) -> Optional[str]:
    img = card.select_one("img.s-image")
    if img:
        return img.get("src")
    return None
