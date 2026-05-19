"""
Flask REST API for E-commerce Tracker.

Endpoints
---------
GET /search?query=<keyword>&platforms=amazon,daraz&max=20
    Returns JSON array of scraped products.

GET /health
    Returns service health status.

Run
---
    python api/app.py          # development server
    flask --app api/app run    # alternative
"""
from __future__ import annotations

import sys
import os

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from flask import Flask, jsonify, request, Response

from scraper.manager import ScraperManager
from utils.logger import setup_logger

logger = setup_logger("api")

app = Flask(__name__)
app.json.sort_keys = False


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> Response:
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------

@app.get("/search")
def search() -> Response:
    """
    Query params
    ~~~~~~~~~~~~
    query     : str   — required; search keyword
    platforms : str   — optional; comma-separated list (default: all)
                        e.g. platforms=amazon,daraz
    max       : int   — optional; max results per platform (default: 20)

    Returns
    ~~~~~~~
    200  { keyword, scraped_at, total, products: [...] }
    400  { error: "..." }
    500  { error: "..." }
    """
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Missing required query parameter 'query'."}), 400

    raw_platforms = request.args.get("platforms", "all")
    platforms = [p.strip() for p in raw_platforms.split(",") if p.strip()]

    try:
        max_results = int(request.args.get("max", 20))
        max_results = min(max(1, max_results), 100)   # clamp to [1, 100]
    except ValueError:
        return jsonify({"error": "Parameter 'max' must be an integer."}), 400

    logger.info("API /search  query=%r  platforms=%s  max=%d", query, platforms, max_results)

    try:
        manager = ScraperManager(
            keyword=query,
            platforms=platforms,
            max_results_per_platform=max_results,
        )
        products = manager.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error during scrape: %s", exc)
        return jsonify({"error": "Internal scraping error. See server logs."}), 500

    payload = {
        "keyword":    query,
        "platforms":  platforms,
        "scraped_at": datetime.now().isoformat(),
        "total":      len(products),
        "products":   [p.to_dict() for p in products],
    }
    return jsonify(payload)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
