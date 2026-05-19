# 🛍 E-commerce Tracker Automation

A production-grade Python system that scrapes product listings from multiple
e-commerce platforms and exports clean CSV, Excel, and JSON reports.

---

## 📁 Project Structure

```
ecommerce_tracker/
│
├── main.py                     # CLI entry point
│
├── scraper/                    # Scraper layer
│   ├── __init__.py
│   ├── base_scraper.py         # Abstract base class (contract for all scrapers)
│   ├── amazon_scraper.py       # Amazon-specific scraper
│   ├── daraz_scraper.py        # Daraz-specific scraper
│   ├── generic_scraper.py      # Config-driven scraper for any site
│   └── manager.py              # Orchestrator — runs scrapers, deduplicates
│
├── parsers/                    # HTML/JSON parsing layer
│   ├── __init__.py
│   ├── models.py               # Product dataclass
│   ├── amazon_parser.py        # Amazon search-result HTML parser
│   ├── daraz_parser.py         # Daraz JSON + HTML parser
│   ├── generic_parser.py       # CSS-selector-driven generic parser
│   └── site_configs.py         # SiteConfig registry (eBay, Walmart, Noon …)
│
├── utils/                      # Shared utilities
│   ├── __init__.py
│   ├── logger.py               # Centralised logging (console + rotating file)
│   ├── http_client.py          # Requests session with retry, polite delays
│   ├── helpers.py              # Text cleaning, price/rating parsers, dedup
│   └── exporter.py             # CSV / Excel / JSON export
│
├── api/                        # Flask REST API (bonus)
│   ├── __init__.py
│   └── app.py                  # GET /search  GET /health
│
├── output/                     # Generated files land here (git-ignored)
├── logs/                       # Log files (git-ignored)
│
└── requirements.txt
```

---

## ⚡ Quick Start

### 1 — Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Run from CLI

```bash
# Search all platforms for "laptop"
python main.py "laptop"

# Amazon + Daraz only, 15 results each
python main.py "iPhone 13" --platforms amazon daraz --max 15

# Export CSV + Excel + JSON to a custom folder
python main.py "shoes" --formats csv excel json --out-dir results/

# Preview results in terminal without writing files
python main.py "headphones" --dry-run
```

### 3 — Run the Flask API

```bash
python api/app.py
# Server starts at http://localhost:5000
```

**API endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/search?query=iphone` | GET | Search products, return JSON |

**Query parameters for `/search`:**

| Param | Default | Description |
|-------|---------|-------------|
| `query` | *(required)* | Search keyword |
| `platforms` | `all` | Comma-separated list: `amazon,daraz,ebay` |
| `max` | `20` | Max results per platform (capped at 100) |

**Example:**
```
GET http://localhost:5000/search?query=iphone&platforms=amazon,daraz&max=10
```

---

## 🔧 Adding a New Website

Adding support for a new e-commerce site takes **< 5 minutes** and requires
touching only one file:

1. Open `parsers/site_configs.py`
2. Add a new `SiteConfig` entry:

```python
"mynewsite": SiteConfig(
    name="MyNewSite",
    base_url="https://www.mynewsite.com",
    currency="USD",
    card_selector="div.product-card",
    title_selector="h2.product-title",
    price_selector="span.price",
    rating_selector="span.rating",
    reviews_selector="span.review-count",
    url_selector="a.product-link",
    availability_selector="span.stock-status",
    image_selector="img.product-thumb",
),
```

3. Add its search URL template in `scraper/manager.py`:

```python
GENERIC_SEARCH_URLS["mynewsite"] = "https://www.mynewsite.com/search?q={query}"
```

That's it — the manager picks it up automatically.

---

## 📤 Output Files

All files land in `output/` (configurable via `--out-dir`).

| Format | Filename example | Contents |
|--------|-----------------|----------|
| CSV | `iphone_13_20250519_143022.csv` | Flat rows, UTF-8 |
| Excel | `iphone_13_20250519_143022.xlsx` | Formatted, avg formulas, frozen header |
| JSON | `iphone_13_20250519_143022.json` | Full payload with metadata |

### Excel features
- Title banner + metadata row
- Alternating row shading
- Frozen header row
- Summary row with `AVERAGEIF` formulas for price and rating
- Column auto-width

---

## 🏗 Architecture

```
CLI (main.py)  /  Flask API (api/app.py)
        │
        ▼
   ScraperManager          ← selects & runs scrapers
   ├── AmazonScraper       ← fetches + delegates to amazon_parser
   ├── DarazScraper        ← fetches + delegates to daraz_parser
   └── GenericScraper      ← fetches + delegates to generic_parser (SiteConfig)
        │
        ▼
   Parser layer            ← pure HTML/JSON → list[Product]
        │
        ▼
   Deduplication           ← MD5 fingerprint on (title, price, url)
        │
        ▼
   Exporter                ← CSV / Excel / JSON
```

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| `BaseScraper` ABC | Enforces the `_build_url` / `_parse_response` contract; new scrapers can't skip either |
| Parser ↔ Scraper split | Parsers are pure functions → easy unit testing without HTTP |
| `SiteConfig` data class | Adding a site = adding data, not code |
| `polite_get` with random delay | Respects rate limits; randomness avoids fixed-interval detection |
| MD5 deduplication | Fast, deterministic; survives page re-ordering |
| `AVERAGEIF` in Excel | Dynamic — recalculates if user edits prices manually |

---

## ⚙ Configuration

| Setting | Where | Default |
|---------|-------|---------|
| Request delay | `utils/http_client.py` → `polite_get(delay_range=...)` | 1.5 – 3.5 s |
| Retry attempts | `utils/http_client.py` → `build_session(retries=...)` | 3 |
| Backoff factor | `utils/http_client.py` → `build_session(backoff_factor=...)` | 1.5 |
| Log level | `utils/logger.py` | INFO (console), DEBUG (file) |
| Output directory | CLI `--out-dir` flag | `output/` |

---

## ⚠ Ethical & Legal Notes

- Only public, non-authenticated pages are accessed.
- No CAPTCHA bypass or anti-bot circumvention is implemented or intended.
- Polite delays and low request rates are enforced by default.
- Always review the `robots.txt` and Terms of Service of any site before scraping.
- This project is intended for learning and portfolio purposes.

---

## 🧪 Running Tests (optional)

```bash
pip install pytest
pytest tests/          # if you add tests/
```

---

## 📦 Tech Stack

| Library | Purpose |
|---------|---------|
| `requests` | HTTP client |
| `beautifulsoup4` | HTML parsing |
| `lxml` | Fast BS4 parser backend |
| `pandas` | DataFrame / CSV export |
| `openpyxl` | Excel (.xlsx) creation & formatting |
| `flask` | REST API |

---

*Built as a portfolio project demonstrating OOP, modular design, robust HTTP
handling, and professional data export in Python.*
