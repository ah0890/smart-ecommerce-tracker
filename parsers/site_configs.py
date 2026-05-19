"""
Pre-built SiteConfig entries for common e-commerce sites.

To add a new site, create a new SiteConfig here — no changes needed
anywhere else in the codebase.  The GenericScraper picks configs up
automatically via the SITE_CONFIGS registry.
"""
from parsers.generic_parser import SiteConfig

# ---------------------------------------------------------------------------
# Registry — key matches scraper 'source' identifier
# ---------------------------------------------------------------------------

SITE_CONFIGS: dict[str, SiteConfig] = {

    "ebay": SiteConfig(
        name="eBay",
        base_url="https://www.ebay.com",
        currency="USD",
        card_selector="li.s-item",
        title_selector="div.s-item__title span",
        price_selector="span.s-item__price",
        rating_selector="div.x-star-rating span.clipped",
        reviews_selector="span.s-item__reviews-count span",
        url_selector="a.s-item__link",
        availability_selector="span.s-item__availability",
        image_selector="img.s-item__image-img",
    ),

    "walmart": SiteConfig(
        name="Walmart",
        base_url="https://www.walmart.com",
        currency="USD",
        card_selector="div[data-item-id]",
        title_selector="span[data-automation-id='product-title']",
        price_selector="div[data-automation-id='product-price'] span.f2",
        rating_selector="span.stars-reviews-count-node",
        reviews_selector="span.stars-reviews-count-node",
        url_selector="a[link-identifier='item-title']",
        availability_selector="span[data-automation-id='fulfillment-label']",
        image_selector="img[data-automation-id='product-tile-image']",
    ),

    "noon": SiteConfig(
        name="Noon",
        base_url="https://www.noon.com",
        currency="AED",
        card_selector="div.productContainer",
        title_selector="div.name",
        price_selector="strong.sellingPrice",
        rating_selector="span.rating",
        reviews_selector="span.ratingCount",
        url_selector="a.link",
        image_selector="img.image",
    ),

    # Template — copy and fill in selectors for any new site
    "_template": SiteConfig(
        name="NewSite",
        base_url="https://www.example.com",
        currency="USD",
        card_selector="div.product-card",         # update
        title_selector="h2.product-title",        # update
        price_selector="span.price",              # update
        rating_selector="span.rating",            # update
        reviews_selector="span.reviews",          # update
        url_selector="a.product-link",            # update
        availability_selector="span.stock",       # update
        image_selector="img.product-image",       # update
    ),
}
