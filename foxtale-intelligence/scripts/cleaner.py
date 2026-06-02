"""
cleaner.py - Data cleaning, validation, and deduplication for scraped skincare data.

All clean_* functions accept raw string values (possibly None) and return
typed Python values or None when the value cannot be parsed.
"""

import re
from typing import Optional

import pandas as pd

from scripts.utils import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Field-level cleaners
# ---------------------------------------------------------------------------


def clean_price(value: Optional[str]) -> Optional[float]:
    """
    Strip currency symbols, commas, and whitespace then parse as float.

    Handles:
      - "₹ 1,299.00" -> 1299.0
      - "Rs. 450"     -> 450.0
      - "1299"        -> 1299.0
      - None / ""     -> None

    Args:
        value: Raw price string from the scraped page.

    Returns:
        Numeric price as float, or None if unparseable.
    """
    if not value:
        return None
    # Remove currency symbols, whitespace, commas
    cleaned = re.sub(r"[₹Rs.,\s]", "", str(value))
    # Keep only digits and a single decimal point
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        logger.warning("clean_price: could not parse %r", value)
        return None


def clean_discount(value: Optional[str]) -> Optional[float]:
    """
    Extract a numeric percentage from a discount string.

    Handles:
      - "20% off"  -> 20.0
      - "Save 15%" -> 15.0
      - "-30%"     -> 30.0
      - None / ""  -> None

    Args:
        value: Raw discount string.

    Returns:
        Discount percentage as float, or None if unparseable.
    """
    if not value:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(value))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    logger.warning("clean_discount: could not parse %r", value)
    return None


def clean_rating(value: Optional[str]) -> Optional[float]:
    """
    Extract a numeric rating in the range 0–5 from a raw string.

    Handles:
      - "4.5"         -> 4.5
      - "4.5/5"       -> 4.5
      - "4.5 out of 5"-> 4.5
      - "4.5 stars"   -> 4.5
      - None / ""     -> None

    Args:
        value: Raw rating string or numeric value.

    Returns:
        Rating as float (0–5), or None if unparseable or out of range.
    """
    if value is None:
        return None
    # Try direct float conversion first (e.g. already numeric)
    try:
        rating = float(str(value).strip())
        if 0.0 <= rating <= 5.0:
            return rating
        # Might be on a 10-point scale — normalise
        if 0.0 <= rating <= 10.0:
            return round(rating / 2, 2)
        logger.warning("clean_rating: value %r out of expected range", value)
        return None
    except ValueError:
        pass
    # Try to extract leading float
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if match:
        try:
            rating = float(match.group(1))
            if 0.0 <= rating <= 5.0:
                return rating
            if 0.0 <= rating <= 10.0:
                return round(rating / 2, 2)
        except ValueError:
            pass
    logger.warning("clean_rating: could not parse %r", value)
    return None


def clean_review_count(value: Optional[str]) -> Optional[int]:
    """
    Strip non-numeric characters and parse review count as int.

    Handles:
      - "1,234 reviews" -> 1234
      - "(567)"         -> 567
      - "23"            -> 23
      - None / ""       -> None

    Args:
        value: Raw review count string.

    Returns:
        Review count as int, or None if unparseable.
    """
    if not value:
        return None
    digits = re.sub(r"[^\d]", "", str(value))
    if not digits:
        logger.warning("clean_review_count: could not parse %r", value)
        return None
    try:
        return int(digits)
    except ValueError:
        logger.warning("clean_review_count: could not parse %r", value)
        return None


def clean_product_name(value: Optional[str]) -> Optional[str]:
    """
    Normalise a product name: strip leading/trailing whitespace, collapse
    internal whitespace runs, then apply title case.

    Args:
        value: Raw product name string.

    Returns:
        Cleaned title-cased string, or None if input is empty/None.
    """
    if not value:
        return None
    # Collapse any run of whitespace (including newlines, tabs) to a single space
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    if not cleaned:
        return None
    return cleaned.title()


# ---------------------------------------------------------------------------
# Row-level validation
# ---------------------------------------------------------------------------


def validate_row(row: pd.Series) -> bool:
    """
    Return True only if the row has a non-empty brand and product_name.

    Args:
        row: A pandas Series representing one product row.

    Returns:
        True if valid, False otherwise.
    """
    brand = str(row.get("brand", "")).strip()
    name = str(row.get("product_name", "")).strip()
    return bool(brand) and bool(name)


# ---------------------------------------------------------------------------
# DataFrame-level operations
# ---------------------------------------------------------------------------


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where the combination of (brand, product_url) is duplicated,
    keeping the first occurrence.

    Args:
        df: Input DataFrame.

    Returns:
        Deduplicated DataFrame with reset index.
    """
    before = len(df)
    df = df.drop_duplicates(subset=["brand", "product_url"], keep="first")
    after = len(df)
    if before - after:
        logger.info("deduplicate: removed %d duplicate rows (%d -> %d)", before - after, before, after)
    return df.reset_index(drop=True)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all field-level cleaners to the appropriate columns of a DataFrame,
    validate rows, and return the cleaned result.

    Args:
        df: Raw DataFrame with columns matching the product schema.

    Returns:
        Cleaned, validated DataFrame.
    """
    logger.info("Cleaning %d raw rows …", len(df))

    df = df.copy()

    # Apply field cleaners
    df["product_name"] = df["product_name"].apply(clean_product_name)
    df["price"] = df["price"].apply(clean_price)
    df["discount"] = df["discount"].apply(clean_discount)
    df["rating"] = df["rating"].apply(clean_rating)
    df["review_count"] = df["review_count"].apply(clean_review_count)

    # Validate rows
    valid_mask = df.apply(validate_row, axis=1)
    invalid_count = (~valid_mask).sum()
    if invalid_count:
        logger.warning("Dropping %d rows that failed validation (missing brand or product_name)", invalid_count)
    df = df[valid_mask].reset_index(drop=True)

    logger.info("Cleaning complete: %d valid rows remaining", len(df))
    return df
