"""
main.py — Command-line interface for E-commerce Tracker.

Usage examples
--------------
# Search all platforms for "laptop":
    python main.py "laptop"

# Search only Amazon and Daraz, 15 results each:
    python main.py "iPhone 13" --platforms amazon daraz --max 15

# Export CSV + Excel + JSON, save to custom dir:
    python main.py "shoes" --formats csv excel json --out-dir results/

# Run without exporting (just print summary):
    python main.py "headphones" --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scraper.manager import ScraperManager
from utils.exporter import export_csv, export_excel, export_json
from utils.logger import setup_logger

logger = setup_logger("main")

AVAILABLE_PLATFORMS = ["amazon", "daraz", "ebay", "walmart", "noon", "all"]
AVAILABLE_FORMATS   = ["csv", "excel", "json"]


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecommerce-tracker",
        description=(
            "E-commerce Tracker — scrape product listings from multiple platforms "
            "and export to CSV / Excel / JSON."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "laptop"
  python main.py "iPhone 13" --platforms amazon daraz --max 15
  python main.py "shoes" --formats csv excel json --out-dir results/
  python main.py "headphones" --dry-run
        """,
    )

    parser.add_argument(
        "keyword",
        type=str,
        help="Product search keyword (e.g. 'iPhone 13', 'laptop', 'shoes').",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=AVAILABLE_PLATFORMS,
        default=["all"],
        metavar="PLATFORM",
        help=(
            f"Platforms to scrape. Options: {', '.join(AVAILABLE_PLATFORMS)}. "
            "Default: all"
        ),
    )
    parser.add_argument(
        "--max",
        type=int,
        default=20,
        dest="max_results",
        metavar="N",
        help="Maximum products per platform (default: 20, max: 100).",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=AVAILABLE_FORMATS,
        default=["csv", "excel"],
        metavar="FORMAT",
        help=(
            f"Output formats. Options: {', '.join(AVAILABLE_FORMATS)}. "
            "Default: csv excel"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output"),
        dest="out_dir",
        metavar="DIR",
        help="Output directory for exported files (default: output/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and print results to the terminal without exporting files.",
    )
    return parser


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    """Execute the scrape + export pipeline. Returns exit code."""
    keyword     = args.keyword.strip()
    platforms   = args.platforms
    max_results = max(1, min(args.max_results, 100))
    formats     = args.formats
    out_dir     = args.out_dir
    dry_run     = args.dry_run

    logger.info("=" * 60)
    logger.info("E-commerce Tracker started")
    logger.info("  Keyword   : %s", keyword)
    logger.info("  Platforms : %s", ", ".join(platforms))
    logger.info("  Max/site  : %d", max_results)
    logger.info("  Formats   : %s", ", ".join(formats))
    logger.info("  Dry run   : %s", dry_run)
    logger.info("=" * 60)

    # --- Scrape -----------------------------------------------------------
    manager = ScraperManager(
        keyword=keyword,
        platforms=platforms,
        max_results_per_platform=max_results,
    )
    products = manager.run()

    if not products:
        logger.warning("No products found. Exiting.")
        return 1

    # --- Print summary ----------------------------------------------------
    _print_summary(products, keyword)

    if dry_run:
        logger.info("Dry-run mode — no files written.")
        return 0

    # --- Export -----------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    exported: list[Path] = []

    if "csv" in formats:
        exported.append(export_csv(products, keyword, out_dir))

    if "excel" in formats:
        exported.append(export_excel(products, keyword, out_dir))

    if "json" in formats:
        exported.append(export_json(products, keyword, out_dir))

    logger.info("")
    logger.info("✅  Export complete — %d file(s) written:", len(exported))
    for path in exported:
        logger.info("   📄  %s", path.resolve())

    return 0


def _print_summary(products, keyword: str) -> None:
    """Print a concise tabular summary to stdout."""
    divider = "─" * 90
    print(f"\n{divider}")
    print(f"  Results for: \"{keyword}\"   ({len(products)} products)")
    print(divider)
    header = f"  {'#':<4}  {'Source':<10}  {'Price':>10}  {'Rating':>6}  {'Reviews':>8}  Title"
    print(header)
    print(divider)
    for i, p in enumerate(products, 1):
        price  = f"{p.currency} {p.price:.2f}" if p.price else "N/A"
        rating = f"{p.rating:.1f}" if p.rating else "N/A"
        reviews = str(p.review_count) if p.review_count else "N/A"
        title  = p.title[:48] + "…" if len(p.title) > 49 else p.title
        print(f"  {i:<4}  {p.source:<10}  {price:>10}  {rating:>6}  {reviews:>8}  {title}")
    print(divider + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = build_parser()
    args   = parser.parse_args()
    sys.exit(run(args))
