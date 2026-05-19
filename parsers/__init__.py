"""Parser modules for E-commerce Tracker."""
from parsers.models import Product
from parsers.generic_parser import SiteConfig, parse_search_results as generic_parse
from parsers.site_configs import SITE_CONFIGS
import parsers.amazon_parser as amazon_parser
import parsers.daraz_parser as daraz_parser

__all__ = [
    "Product",
    "SiteConfig",
    "generic_parse",
    "SITE_CONFIGS",
    "amazon_parser",
    "daraz_parser",
]
