"""
run.py - CLI entry point for the Foxtale Intelligence scraping pipeline.

Runs: scrape → clean → deduplicate → save to CSV

Usage:
    python -m scripts.run [options]

Options:
    --brands        Comma-separated list of brand names (default: all 5).
    --max-pages     Max collection pages per brand (default: 5).
    --output        Output CSV path (default: data/products.csv).
    --dry-run       Scrape only page 1 of each brand.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import pandas as pd

# Ensure the project root is on sys.path so `scripts.*` imports work
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.cleaner import clean_dataframe, deduplicate
from scripts.scraper import BRANDS, scrape_brands
from scripts.utils import get_logger

logger = get_logger("run")

# Expected column order in the output CSV
COLUMNS = [
    "brand",
    "product_name",
    "category",
    "price",
    "discount",
    "rating",
    "review_count",
    "product_url",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Foxtale Competitor Intelligence — Skincare Product Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--brands",
        type=str,
        default=None,
        help=(
            "Comma-separated brand names to scrape. "
            f"Valid: {', '.join(BRANDS.keys())}. Default: all."
        ),
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        dest="max_pages",
        help="Maximum number of collection pages to scrape per brand (default: 5).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/products.csv",
        help="Output CSV file path (default: data/products.csv).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Scrape only page 1 of each brand (quick test mode).",
    )
    return parser.parse_args()


def _resolve_output_path(output_arg: str) -> Path:
    """Resolve output path relative to project root if not absolute."""
    path = Path(output_arg)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _print_summary(raw_count: int, df: pd.DataFrame, output_path: Path) -> None:
    """Print a structured summary to stdout."""
    print("\n" + "=" * 60)
    print("  SCRAPE PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Raw products scraped : {raw_count}")
    print(f"  After cleaning       : {len(df)}")
    print()
    print("  Products per brand:")
    if len(df) > 0:
        for brand, count in df["brand"].value_counts().items():
            print(f"    {brand:<20} {count:>5}")
    else:
        print("    (no products)")
    print()
    print(f"  Output file          : {output_path}")
    print("=" * 60 + "\n")


async def _run_pipeline(
    brands: list,
    max_pages: int,
    output_path: Path,
    dry_run: bool,
) -> None:
    effective_max_pages = 1 if dry_run else max_pages
    if dry_run:
        logger.info("DRY RUN mode — scraping only page 1 per brand")

    # --- Step 1: Scrape ---
    logger.info("Starting scrape for brands: %s (max_pages=%d)", brands, effective_max_pages)
    raw_products = await scrape_brands(brands=brands, max_pages=effective_max_pages)
    raw_count = len(raw_products)
    logger.info("Scrape complete: %d raw product records", raw_count)

    if not raw_products:
        logger.warning("No products scraped. Saving empty CSV.")
        df_final = pd.DataFrame(columns=COLUMNS)
        df_final.to_csv(output_path, index=False, encoding="utf-8-sig")
        _print_summary(0, df_final, output_path)
        return

    # --- Step 2: Build DataFrame ---
    df = pd.DataFrame(raw_products, columns=COLUMNS)
    logger.info("Built DataFrame: %d rows × %d cols", *df.shape)

    # --- Step 3: Clean ---
    df = clean_dataframe(df)

    # --- Step 4: Deduplicate ---
    df = deduplicate(df)

    # --- Step 5: Save ---
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info("Saved %d products to %s", len(df), output_path)

    _print_summary(raw_count, df, output_path)


def main() -> None:
    args = _parse_args()

    # Resolve brand list
    if args.brands:
        brand_list = [b.strip() for b in args.brands.split(",") if b.strip()]
        invalid = [b for b in brand_list if b not in BRANDS]
        if invalid:
            logger.error("Unknown brands: %s. Valid: %s", invalid, list(BRANDS.keys()))
            sys.exit(1)
    else:
        brand_list = list(BRANDS.keys())

    output_path = _resolve_output_path(args.output)

    logger.info(
        "Pipeline start — brands=%s, max_pages=%d, output=%s, dry_run=%s",
        brand_list,
        args.max_pages,
        output_path,
        args.dry_run,
    )

    asyncio.run(
        _run_pipeline(
            brands=brand_list,
            max_pages=args.max_pages,
            output_path=output_path,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
