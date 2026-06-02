"""
scraper.py - Async Playwright scraper for Indian skincare brand product data.

Scrapes product listings from 5 brands concurrently (max 2 at a time via
semaphore), with retry logic, randomised user-agent rotation, and polite
random delays between page loads.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from scripts.utils import get_logger, random_delay, random_user_agent, retry_async

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Brand configurations
# ---------------------------------------------------------------------------

BRANDS: Dict[str, Dict[str, Any]] = {
    "Foxtale": {
        "base_url": "https://foxtale.in",
        "collections_url": "https://foxtale.in/collections/all",
    },
    "Minimalist": {
        "base_url": "https://beminimalist.co",
        "collections_url": "https://beminimalist.co/collections/all",
    },
    "Dot & Key": {
        "base_url": "https://www.dotandkey.com",
        "collections_url": "https://www.dotandkey.com/collections/all",
    },
    "The Derma Co": {
        "base_url": "https://thederma.co",
        "collections_url": "https://thederma.co/collections/all",
    },
    "Plum": {
        "base_url": "https://plumgoodness.com",
        "collections_url": "https://plumgoodness.com/collections/all",
    },
}

# CSS selector fallback chains
_NAME_SELECTORS = [
    ".product-card__title",
    ".product-card__name",
    ".product-title",
    ".card__heading",
    ".card-title",
    "h3.product-name",
    "h2.product-name",
    "h3",
    "h2",
    "[class*='product-title']",
    "[class*='product-name']",
    "[class*='card-title']",
    "[class*='card__title']",
]

_PRICE_SELECTORS = [
    ".price__sale .price-item--sale",
    ".price-item--sale",
    ".price__regular .price-item",
    ".price-item",
    ".product-price",
    ".price",
    "[class*='price-item']",
    "[class*='product-price']",
    "[class*='price']",
]

_ORIGINAL_PRICE_SELECTORS = [
    ".price-item--regular",
    ".price__compare .price-item",
    "[class*='compare-price']",
    "[class*='original-price']",
    "s.price",
    "del",
]

_RATING_SELECTORS = [
    "[class*='rating-value']",
    "[class*='star-rating']",
    "[class*='review-rating']",
    "[class*='rating']",
    "[class*='stars']",
    "span.jdgm-prev-badge__stars",
    "[data-rating]",
    "[class*='yotpo-sum-reviews']",
]

_REVIEW_SELECTORS = [
    "[class*='review-count']",
    "[class*='reviews-count']",
    "[class*='rating-count']",
    "span.jdgm-prev-badge__count",
    "[class*='yotpo-count']",
    "[class*='review']",
]

_PRODUCT_CARD_SELECTORS = [
    ".product-card",
    ".grid__item",
    ".product-item",
    ".card-wrapper",
    ".product-grid-item",
    "li.grid__item",
    "li[class*='product']",
    "[class*='product-card']",
    "[class*='product-item']",
]


# ---------------------------------------------------------------------------
# Helper: try multiple selectors within a card element
# ---------------------------------------------------------------------------

async def _try_selectors(element, selectors: List[str]) -> Optional[str]:
    """
    Try each CSS selector in order against a Playwright element handle.
    Returns the inner text of the first match, or None.
    """
    for sel in selectors:
        try:
            child = await element.query_selector(sel)
            if child:
                text = await child.inner_text()
                text = text.strip()
                if text:
                    return text
        except Exception:
            continue
    return None


async def _get_attr(element, selectors: List[str], attr: str) -> Optional[str]:
    """Try selectors and return the given attribute value of the first match."""
    for sel in selectors:
        try:
            child = await element.query_selector(sel)
            if child:
                val = await child.get_attribute(attr)
                if val and val.strip():
                    return val.strip()
        except Exception:
            continue
    return None


async def _get_href(element) -> Optional[str]:
    """Extract href from <a> tag inside a product card element."""
    try:
        anchor = await element.query_selector("a[href]")
        if anchor:
            return await anchor.get_attribute("href")
    except Exception:
        pass
    return None


def _infer_category(url: str) -> str:
    """
    Infer a product category from its URL path segments.
    Falls back to 'General' if no useful segment is found.
    """
    skip = {"collections", "products", "all", "shop", "www", ""}
    parts = re.split(r"[/\-_]", url.lower())
    for part in parts:
        part = part.strip()
        if part and part not in skip and len(part) > 3 and not part.startswith("http"):
            return part.title()
    return "General"


def _extract_discount(sale_price_str: Optional[str], original_price_str: Optional[str]) -> Optional[str]:
    """
    Compute discount percentage from sale and original price strings.
    Returns a formatted string like '20.0' or None.
    """
    if not sale_price_str or not original_price_str:
        return None
    try:
        sale = float(re.sub(r"[^\d.]", "", sale_price_str))
        orig = float(re.sub(r"[^\d.]", "", original_price_str))
        if orig > 0 and sale < orig:
            pct = round((orig - sale) / orig * 100, 1)
            return str(pct)
    except (ValueError, ZeroDivisionError):
        pass
    return None


# ---------------------------------------------------------------------------
# Page-level scraper
# ---------------------------------------------------------------------------

async def _scrape_page(
    page: Page,
    brand: str,
    base_url: str,
    page_url: str,
    page_num: int,
) -> List[Dict[str, Any]]:
    """
    Navigate to page_url and extract all product cards found on that page.
    Returns a list of raw product dicts.
    """
    products: List[Dict[str, Any]] = []

    try:
        await page.goto(page_url, timeout=30_000)
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception as exc:
        logger.warning("Brand=%s page=%d: failed to load %s — %s", brand, page_num, page_url, exc)
        return products

    # Find product cards using fallback selector chain
    cards = []
    for card_sel in _PRODUCT_CARD_SELECTORS:
        try:
            cards = await page.query_selector_all(card_sel)
            if cards:
                logger.debug("Brand=%s page=%d: found %d cards with selector %r", brand, page_num, len(cards), card_sel)
                break
        except Exception:
            continue

    if not cards:
        logger.warning("Brand=%s page=%d: no product cards found on %s", brand, page_num, page_url)
        return products

    for card in cards:
        try:
            name = await _try_selectors(card, _NAME_SELECTORS)
            if not name:
                continue  # skip cards with no name

            sale_price = await _try_selectors(card, _PRICE_SELECTORS)
            original_price = await _try_selectors(card, _ORIGINAL_PRICE_SELECTORS)
            rating = await _try_selectors(card, _RATING_SELECTORS)
            if not rating:
                # Try data-rating attribute
                rating = await _get_attr(card, _RATING_SELECTORS, "data-rating")
            reviews = await _try_selectors(card, _REVIEW_SELECTORS)

            # Product URL
            href = await _get_href(card)
            if href:
                product_url = urljoin(base_url, href) if not href.startswith("http") else href
            else:
                product_url = page_url

            # Category: try to infer from the product URL path
            category = _infer_category(product_url)

            # Discount: compute from prices or look for explicit badge
            discount_raw = await _try_selectors(card, ["[class*='badge']", "[class*='discount']", "[class*='sale-badge']"])
            computed_discount = _extract_discount(sale_price, original_price)
            discount = discount_raw or computed_discount

            products.append(
                {
                    "brand": brand,
                    "product_name": name,
                    "category": category,
                    "price": sale_price or original_price,
                    "discount": discount,
                    "rating": rating,
                    "review_count": reviews,
                    "product_url": product_url,
                }
            )
        except Exception as exc:
            logger.warning("Brand=%s page=%d: error extracting card — %s", brand, page_num, exc)
            continue

    logger.info("Brand=%s page=%d: extracted %d products from %s", brand, page_num, len(products), page_url)
    return products


# ---------------------------------------------------------------------------
# Brand-level scraper
# ---------------------------------------------------------------------------

async def _scrape_brand(
    browser: Browser,
    brand: str,
    collections_url: str,
    base_url: str,
    max_pages: int,
) -> List[Dict[str, Any]]:
    """
    Scrape all pages for a single brand.  Opens a dedicated browser context
    with a randomised user-agent so each brand gets an independent session.
    """
    logger.info("Brand=%s: starting scrape (max_pages=%d)", brand, max_pages)
    all_products: List[Dict[str, Any]] = []

    context: BrowserContext = await browser.new_context(
        user_agent=random_user_agent(),
        viewport={"width": 1440, "height": 900},
        locale="en-IN",
    )

    try:
        page: Page = await context.new_page()
        # Block images/media for speed; keep JS active (needed for Shopify)
        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf}", lambda r: r.abort())

        seen_product_urls: set = set()

        for page_num in range(1, max_pages + 1):
            url = collections_url if page_num == 1 else f"{collections_url}?page={page_num}"

            async def _fetch(p=page, b=brand, bu=base_url, u=url, pn=page_num):
                return await _scrape_page(p, b, bu, u, pn)

            try:
                page_products = await retry_async(
                    _fetch,
                    retries=3,
                    backoff=2.0,
                    logger=logger,
                )
            except Exception as exc:
                logger.error("Brand=%s page=%d: all retries exhausted — %s", brand, page_num, exc)
                break

            # Stop paginating if no new products were found (end of catalogue)
            new_products = [p for p in page_products if p["product_url"] not in seen_product_urls]
            if not new_products and page_num > 1:
                logger.info("Brand=%s: no new products on page %d — stopping pagination", brand, page_num)
                break

            for p in new_products:
                seen_product_urls.add(p["product_url"])
            all_products.extend(new_products)

            if page_num < max_pages:
                await random_delay(1.0, 3.0)

    except Exception as exc:
        logger.error("Brand=%s: fatal scrape error — %s", brand, exc)
    finally:
        await context.close()

    logger.info("Brand=%s: finished — %d total products scraped", brand, len(all_products))
    return all_products


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def scrape_brands(
    brands: Optional[List[str]] = None,
    max_pages: int = 5,
) -> List[Dict[str, Any]]:
    """
    Scrape product data from the specified brands (default: all 5).

    Uses a semaphore to limit concurrent brand scraping to 2 at a time.

    Args:
        brands:    List of brand names to scrape (must match keys in BRANDS).
                   Defaults to all brands.
        max_pages: Maximum number of collection pages to scrape per brand.

    Returns:
        Combined list of raw product dicts from all brands.
    """
    if brands is None:
        brands = list(BRANDS.keys())

    # Validate brand names
    unknown = [b for b in brands if b not in BRANDS]
    if unknown:
        raise ValueError(f"Unknown brands: {unknown}. Valid options: {list(BRANDS.keys())}")

    semaphore = asyncio.Semaphore(2)
    all_products: List[Dict[str, Any]] = []

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        async def _run_brand(brand_name: str) -> List[Dict[str, Any]]:
            async with semaphore:
                cfg = BRANDS[brand_name]
                return await _scrape_brand(
                    browser=browser,
                    brand=brand_name,
                    collections_url=cfg["collections_url"],
                    base_url=cfg["base_url"],
                    max_pages=max_pages,
                )

        tasks = [asyncio.create_task(_run_brand(b)) for b in brands]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for brand_name, result in zip(brands, results):
            if isinstance(result, Exception):
                logger.error("Brand=%s: task raised exception — %s", brand_name, result)
            else:
                all_products.extend(result)

        await browser.close()

    logger.info("Scrape complete: %d total raw products across all brands", len(all_products))
    return all_products
