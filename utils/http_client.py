"""
Reusable HTTP client with retry logic, rate limiting, and safe browser-like headers.
"""
import time
import random
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Rotate user agents to appear as a normal browser
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}


def build_session(
    retries: int = 3,
    backoff_factor: float = 1.5,
    timeout: int = 15,
) -> requests.Session:
    """
    Create a requests.Session pre-configured with:
      - Retry on 429, 500, 502, 503, 504
      - Exponential backoff between retries
      - Randomised User-Agent header

    Args:
        retries: Max number of retry attempts.
        backoff_factor: Seconds to wait between retries (doubles each attempt).
        timeout: Default request timeout (stored on the session, not enforced here).

    Returns:
        Configured requests.Session.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = dict(DEFAULT_HEADERS)
    headers["User-Agent"] = random.choice(USER_AGENTS)
    session.headers.update(headers)

    # Store timeout so callers can read it
    session.timeout = timeout  # type: ignore[attr-defined]

    return session


def polite_get(
    session: requests.Session,
    url: str,
    delay_range: tuple[float, float] = (1.5, 3.5),
    timeout: Optional[int] = None,
) -> Optional[requests.Response]:
    """
    GET a URL with a random polite delay before the request.

    Args:
        session: An active requests.Session.
        url: Target URL.
        delay_range: (min, max) seconds to sleep before the request.
        timeout: Request timeout in seconds; falls back to session.timeout.

    Returns:
        Response object on success, None on irrecoverable error.
    """
    sleep_time = random.uniform(*delay_range)
    logger.debug("Sleeping %.1fs before fetching: %s", sleep_time, url)
    time.sleep(sleep_time)

    _timeout = timeout or getattr(session, "timeout", 15)
    try:
        response = session.get(url, timeout=_timeout)
        response.raise_for_status()
        logger.debug("GET %s → %d (%d bytes)", url, response.status_code, len(response.content))
        return response
    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP error for %s: %s", url, exc)
    except requests.exceptions.ConnectionError as exc:
        logger.warning("Connection error for %s: %s", url, exc)
    except requests.exceptions.Timeout:
        logger.warning("Timeout for %s (>%ds)", url, _timeout)
    except requests.exceptions.RequestException as exc:
        logger.error("Unexpected request error for %s: %s", url, exc)
    return None
