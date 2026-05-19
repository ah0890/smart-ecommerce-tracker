"""
Data model for a scraped product.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Product:
    """
    Canonical representation of a scraped product.

    All monetary values are stored as plain floats (no currency symbols).
    Missing fields default to None; exporters handle None → 'N/A' as needed.
    """

    title: str
    price: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    url: str
    availability: str
    source: str                        # e.g. "amazon", "daraz", "generic"
    currency: str = "USD"              # ISO-4217 currency code
    image_url: Optional[str] = None
    extra: dict = field(default_factory=dict)   # platform-specific extras

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a flat dict suitable for pandas / CSV export."""
        return {
            "source":        self.source,
            "title":         self.title,
            "price":         self.price,
            "currency":      self.currency,
            "rating":        self.rating,
            "review_count":  self.review_count,
            "availability":  self.availability,
            "url":           self.url,
            "image_url":     self.image_url or "N/A",
        }

    def to_full_dict(self) -> dict:
        """Return the complete dict including the extra payload."""
        d = self.to_dict()
        d.update(self.extra)
        return d

    def __repr__(self) -> str:
        price_str = f"{self.currency} {self.price:.2f}" if self.price else "N/A"
        return f"<Product [{self.source}] '{self.title[:50]}' @ {price_str}>"
