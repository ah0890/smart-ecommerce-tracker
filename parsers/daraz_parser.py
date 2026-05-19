"""
HTML parser for Daraz search-result pages.

Daraz serves product listings as JSON embedded in a <script> tag
(window.pageData or __NEXT_DATA__). This parser handles both the
script-embedded JSON path and a CSS-selector fallback for static HTML.
"""
from __future__ import annotations

import json
import re
from typing import Optional
from bs4 import BeautifulSoup, Tag

from parsers.models import Product
from utils.helpers import clean_text, parse_price, parse_rating, parse_review_count, normalise_url
from utils.logger import setup_logger

logger = setup_logger(__name__)

BASE_URL = "https://www.daraz.pk"


def parse_search_results(html: str, max_results: int = 20) -> list[Product]:
    """
    Extract product listings from a Daraz search-results HTML page.

    Attempts JSON extraction first; falls back to CSS selectors.
    """
    products = _parse_from_json(html, max_results)
    if products:
        logger.info("Daraz JSON parser extracted %d products.", len(products))
        return products

    products = _parse_from_html(html, max_results)
    logger.info("Daraz HTML parser extracted %d products.", len(products))
    return products


# ------------------------------------------------------------------
# JSON extraction path
# ------------------------------------------------------------------

def _parse_from_json(html: str, max_results: int) -> list[Product]:
    """Try to extract products from the embedded JSON payload."""
    soup = BeautifulSoup(html, "html.parser")
    products: list[Product] = []

    # Daraz embeds JSON in window.pageData or __moduleData__
    for script in soup.find_all("script"):
        text = script.string or ""
        if "window.pageData" in text or "__moduleData__" in text:
            try:
                # Extract the JSON object assigned to window.pageData
                match = re.search(r"window\.pageData\s*=\s*(\{.*?\});", text, re.DOTALL)
                if not match:
                    match = re.search(r'"listItems"\s*:\s*(\[.*?\])\s*[,\}]', text, re.DOTALL)
                    if match:
                        items = json.loads(match.group(1))
                        products = _items_to_products(items, max_results)
                        if products:
                            return products
                        continue

                if match:
                    data = json.loads(match.group(1))
                    items = (
                        data.get("mods", {}).get("listItems")
                        or data.get("data", {}).get("result")
                        or []
                    )
                    products = _items_to_products(items, max_results)
                    if products:
                        return products
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    return products


def _items_to_products(items: list, max_results: int) -> list[Product]:
    products: list[Product] = []
    for item in items[:max_results]:
        try:
            p = _json_item_to_product(item)
            if p:
                products.append(p)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Skipping Daraz JSON item: %s", exc)
    return products


def _json_item_to_product(item: dict) -> Optional[Product]:
    title = clean_text(item.get("name") or item.get("title"))
    if not title or title == "N/A":
        return None

    raw_price = item.get("price") or item.get("originalPrice") or item.get("priceShow")
    price = parse_price(str(raw_price)) if raw_price else None

    raw_rating = item.get("ratingScore") or item.get("rating")
    rating = parse_rating(str(raw_rating)) if raw_rating else None

    raw_reviews = item.get("review") or item.get("reviewCount")
    review_count = parse_review_count(str(raw_reviews)) if raw_reviews else None

    item_url = item.get("itemUrl") or item.get("url") or ""
    if item_url and not item_url.startswith("http"):
        item_url = BASE_URL + item_url

    image = item.get("image") or item.get("mainImage") or None
    stock = item.get("inStock")
    availability = "In Stock" if stock else ("Out of Stock" if stock is False else "Unknown")

    return Product(
        title=title,
        price=price,
        rating=rating,
        review_count=review_count,
        url=item_url or "N/A",
        availability=availability,
        source="daraz",
        currency="PKR",
        image_url=image,
    )


# ------------------------------------------------------------------
# HTML CSS-selector fallback path
# ------------------------------------------------------------------

def _parse_from_html(html: str, max_results: int) -> list[Product]:
    soup = BeautifulSoup(html, "html.parser")
    products: list[Product] = []

    # Daraz product cards share a common container class
    cards = (
        soup.select("div[data-item-id]")
        or soup.select(".Bm3ON")          # older layout
        or soup.select("._17mcb")         # alternate layout
    )
    logger.debug("Daraz HTML fallback found %d cards.", len(cards))

    for card in cards[:max_results]:
        product = _parse_html_card(card)
        if product:
            products.append(product)

    return products


def _parse_html_card(card: Tag) -> Optional[Product]:
    try:
        title_el = card.select_one("[class*='title']") or card.select_one("a")
        title = clean_text(title_el.get_text()) if title_el else "N/A"
        if title == "N/A":
            return None

        price_el = card.select_one("[class*='price']")
        price = parse_price(price_el.get_text()) if price_el else None

        rating_el = card.select_one("[class*='rating']")
        rating = parse_rating(rating_el.get_text()) if rating_el else None

        review_el = card.select_one("[class*='review']")
        review_count = parse_review_count(review_el.get_text()) if review_el else None

        a_tag = card.select_one("a[href]")
        url = normalise_url(a_tag["href"], BASE_URL) if a_tag else "N/A"

        img = card.select_one("img")
        image_url = img.get("src") or img.get("data-src") if img else None

        return Product(
            title=title,
            price=price,
            rating=rating,
            review_count=review_count,
            url=url,
            availability="Unknown",
            source="daraz",
            currency="PKR",
            image_url=image_url,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Skipping Daraz HTML card: %s", exc)
        return None
