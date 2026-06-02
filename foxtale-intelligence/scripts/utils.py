"""
utils.py - Shared utilities for the Foxtale Intelligence scraping system.
Provides logging, async retry, random delays, and list chunking helpers.
"""

import asyncio
import logging
import random
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Coroutine, List, TypeVar

T = TypeVar("T")

# Ensure logs directory exists relative to the project root
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "scraper.log"


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger writing to both stdout and logs/scraper.log.

    Args:
        name: Logger name, typically __name__ of the calling module.

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
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    # File handler — DEBUG and above
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def retry_async(retries: int = 3, backoff: float = 2.0):
    """
    Decorator for async functions that retries on any Exception with
    exponential backoff.

    Delays between attempts: backoff^1, backoff^2, ... seconds.

    Args:
        retries: Maximum number of retry attempts (default 3).
        backoff: Base multiplier for exponential backoff (default 2.0).

    Usage:
        @retry_async(retries=3, backoff=2)
        async def fetch(...):
            ...
    """

    def decorator(fn: Callable[..., Coroutine[Any, Any, T]]):
        @wraps(fn)
        async def wrapper(*args, **kwargs) -> T:
            logger = get_logger("retry_async")
            last_exc: Exception = RuntimeError("No attempts made")
            for attempt in range(1, retries + 2):  # +1 for the initial try
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt <= retries:
                        delay = backoff ** attempt
                        logger.warning(
                            "Attempt %d/%d failed for %s — retrying in %.1fs. Error: %s",
                            attempt,
                            retries + 1,
                            fn.__qualname__,
                            delay,
                            exc,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "All %d attempts failed for %s. Last error: %s",
                            retries + 1,
                            fn.__qualname__,
                            exc,
                        )
            raise last_exc

        return wrapper

    return decorator


async def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """
    Sleep for a random duration between min_s and max_s seconds.

    Args:
        min_s: Minimum sleep time in seconds (default 1.0).
        max_s: Maximum sleep time in seconds (default 3.0).
    """
    duration = random.uniform(min_s, max_s)
    await asyncio.sleep(duration)


def chunk_list(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split a list into sub-lists of at most n elements each.

    Args:
        lst: The list to split.
        n:   Maximum chunk size.

    Returns:
        List of chunks (each a list). Empty input returns [].

    Example:
        chunk_list([1,2,3,4,5], 2) -> [[1,2],[3,4],[5]]
    """
    if n <= 0:
        raise ValueError(f"Chunk size n must be > 0, got {n}")
    return [lst[i : i + n] for i in range(0, len(lst), n)]


# ---------------------------------------------------------------------------
# User-agent pool (5 common Chrome UAs for desktop)
# ---------------------------------------------------------------------------
USER_AGENTS: List[str] = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
]


def random_user_agent() -> str:
    """Return a randomly chosen user agent string from the pool."""
    return random.choice(USER_AGENTS)
