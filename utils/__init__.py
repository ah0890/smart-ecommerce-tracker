"""Utility modules for E-commerce Tracker."""
from utils.logger import setup_logger, logger
from utils.http_client import build_session, polite_get
from utils.helpers import (
    clean_text,
    parse_price,
    parse_rating,
    parse_review_count,
    normalise_url,
    deduplicate,
)

__all__ = [
    "setup_logger",
    "logger",
    "build_session",
    "polite_get",
    "clean_text",
    "parse_price",
    "parse_rating",
    "parse_review_count",
    "normalise_url",
    "deduplicate",
]
