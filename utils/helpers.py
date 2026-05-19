"""
Shared helper utilities: text cleaning, price normalisation, deduplication.
"""
import re
import hashlib
from typing import Optional
from urllib.parse import urljoin, urlparse


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def clean_text(raw: Optional[str]) -> str:
    """Strip leading/trailing whitespace and collapse internal whitespace."""
    if not raw:
        return "N/A"
    return re.sub(r"\s+", " ", raw.strip())


def parse_price(raw: Optional[str]) -> Optional[float]:
    """
    Extract a float price from a raw string like '$1,299.99' or 'PKR 45,000'.

    Returns:
        Float price, or None if extraction fails.
    """
    if not raw:
        return None
    digits = re.sub(r"[^\d.]", "", raw.replace(",", ""))
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def parse_rating(raw: Optional[str]) -> Optional[float]:
    """
    Extract a rating float from strings like '4.5 out of 5 stars' or '4.3'.

    Returns:
        Float rating, or None if extraction fails.
    """
    if not raw:
        return None
    match = re.search(r"(\d+\.?\d*)", raw)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_review_count(raw: Optional[str]) -> Optional[int]:
    """
    Extract an integer review count from strings like '(1,234 ratings)' or '2345'.

    Returns:
        Integer review count, or None if extraction fails.
    """
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", raw)
    try:
        return int(digits) if digits else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def normalise_url(url: str, base: str = "") -> str:
    """Ensure the URL is absolute; join with base if relative."""
    if not url:
        return "N/A"
    if url.startswith("//"):
        scheme = urlparse(base).scheme or "https"
        return f"{scheme}:{url}"
    if url.startswith("/") and base:
        return urljoin(base, url)
    return url


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def product_fingerprint(title: str, price: Optional[float], url: str) -> str:
    """
    Generate a deterministic fingerprint for a product to detect duplicates.

    Uses title (lowercased, stripped) + price string + URL path.
    """
    normalised_title = re.sub(r"\s+", " ", title.lower().strip())
    price_str = str(round(price, 2)) if price else "none"
    path = urlparse(url).path

    raw = f"{normalised_title}|{price_str}|{path}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def deduplicate(products: list) -> list:
    """
    Remove duplicate products by fingerprint.

    Accepts either Product dataclass instances or plain dicts.

    Args:
        products: List of Product objects or dicts
                  (must have 'title', 'price', 'url' as attributes or keys).

    Returns:
        Deduplicated list preserving first occurrence.
    """
    seen: set[str] = set()
    unique: list = []
    for product in products:
        if hasattr(product, "title"):
            # Product dataclass
            title = getattr(product, "title", "")
            price = getattr(product, "price", None)
            url   = getattr(product, "url", "")
        else:
            # Plain dict
            title = product.get("title", "")
            price = product.get("price")
            url   = product.get("url", "")

        fp = product_fingerprint(title, price, url)
        if fp not in seen:
            seen.add(fp)
            unique.append(product)
    return unique
