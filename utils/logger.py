"""
Centralized logging configuration for E-commerce Tracker.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "ecommerce_tracker", log_to_file: bool = True) -> logging.Logger:
    """
    Configure and return a logger with console + optional file output.

    Args:
        name: Logger name (used as prefix in log messages).
        log_to_file: If True, also writes logs to a timestamped file.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(log_dir / f"tracker_{timestamp}.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger


# Module-level default logger
logger = setup_logger()
