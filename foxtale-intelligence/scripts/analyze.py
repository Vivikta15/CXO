"""
Foxtale Competitor Intelligence — Analysis Script
Reads data/products.csv and prints Q1–Q6 analysis to stdout.
Saves summary to reports/analysis_data.json.
"""

import csv
import json
import os
from collections import defaultdict
from statistics import mean, median

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["price"] = float(row["price"])
            row["discount"] = float(row["discount"])
            row["rating"] = float(row["rating"])
            row["review_count"] = int(row["review_count"])
            rows.append(row)
    return rows


def group_by(rows, key):
    groups = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    return dict(groups)


def quartiles(values):
    s = sorted(values)
    n = len(s)
    q1 = s[n // 4]
    q3 = s[(3 * n) // 4]
    return q1, q3


def section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def table(headers, rows, widths=None):
    if widths is None:
        widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
                  for i, h in enumerate(headers)]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  " + "  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*[str(v) for v in row]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    csv_path = os.path.join(base_dir, "data", "products.csv")
    out_path = os.path.join(base_dir, "reports", "analysis_data.json")

    products = load_csv(csv_path)
    print(f"\nLoaded {len(products)} products across {len(set(r['brand'] for r in products))} brands.")

    by_brand = group_by(products, "brand")
    brands = sorted(by_brand.keys())
    all_categories = sorted(set(r["category"] for r in products))

    # -----------------------------------------------------------------------
    # Q1: Assortment size per brand
    # -----------------------------------------------------------------------
    section("Q1 — Assortment Size per Brand")
    q1_rows = []
    for b in brands:
        cats = set(r["category"] for r in by_brand[b])
        q1_rows.append((b, len(by_brand[b]), len(cats)))
    table(["Brand", "Total SKUs", "Categories"], q1_rows, [20, 10, 10])

    # -----------------------------------------------------------------------
    # Q2: Category coverage per brand (presence matrix)
    # -----------------------------------------------------------------------
    section("Q2 — Category Coverage per Brand")
    header_cats = all_categories
    widths = [20] + [max(len(c), 3) for c in header_cats]
    print("  " + "  ".join(f"{h:<{w}}" for h, w in zip(["Brand"] + header_cats, widths)))
    print("  " + "  ".join("-" * w for w in widths))
    for b in brands:
        cats_in_brand = set(r["category"] for r in by_brand[b])
        row_vals = [b] + ["YES" if c in cats_in_brand else "---" for c in header_cats]
        print("  " + "  ".join(f"{str(v):<{w}}" for v, w in zip(row_vals, widths)))

    # -----------------------------------------------------------------------
    # Q3: Category competition — brands per category & SKU counts
    # -----------------------------------------------------------------------
    section("Q3 — Category Competition (Brands & SKUs per Category)")
    by_cat = group_by(products, "category")
    q3_rows = []
    for cat in all_categories:
        cat_rows = by_cat[cat]
        brands_in_cat = set(r["brand"] for r in cat_rows)
        leading = max(brands_in_cat, key=lambda b: sum(1 for r in cat_rows if r["brand"] == b))
        leading_skus = sum(1 for r in cat_rows if r["brand"] == leading)
        foxtale_skus = sum(1 for r in cat_rows if r["brand"] == "Foxtale")
        q3_rows.append((cat, len(brands_in_cat), len(cat_rows), leading, leading_skus, foxtale_skus))
    q3_rows.sort(key=lambda x: -x[2])
    table(["Category", "# Brands", "Total SKUs", "Leader", "Leader SKUs", "Foxtale SKUs"],
          q3_rows, [12, 8, 10, 18, 11, 12])

    # -----------------------------------------------------------------------
    # Q4: Avg rating per brand
    # -----------------------------------------------------------------------
    section("Q4 — Ratings Benchmark per Brand")
    q4_rows = []
    for b in brands:
        ratings = [r["rating"] for r in by_brand[b]]
        above_45 = sum(1 for x in ratings if x >= 4.5)
        q4_rows.append((b, f"{mean(ratings):.3f}", f"{median(ratings):.1f}", above_45))
    table(["Brand", "Avg Rating", "Median Rating", "#Products >=4.5"], q4_rows, [20, 10, 13, 15])

    # -----------------------------------------------------------------------
    # Q5: Price positioning per brand
    # -----------------------------------------------------------------------
    section("Q5 — Price Positioning per Brand")
    q5_rows = []
    for b in brands:
        prices = [r["price"] for r in by_brand[b]]
        q1v, q3v = quartiles(prices)
        q5_rows.append((b, int(min(prices)), int(mean(prices)), int(median(prices)),
                        int(q1v), int(q3v), int(max(prices))))
    table(["Brand", "Min ₹", "Avg ₹", "Median ₹", "Q1 ₹", "Q3 ₹", "Max ₹"],
          q5_rows, [20, 6, 6, 9, 6, 6, 6])

    # -----------------------------------------------------------------------
    # Q6: Whitespace gaps — categories where competitors dominate but Foxtale thin
    # -----------------------------------------------------------------------
    section("Q6 — Whitespace Gaps for Foxtale")
    foxtale_cats = defaultdict(int)
    for r in by_brand.get("Foxtale", []):
        foxtale_cats[r["category"]] += 1

    competitor_brands = [b for b in brands if b != "Foxtale"]
    gaps = []
    for cat in all_categories:
        competitor_skus = sum(1 for r in products if r["brand"] != "Foxtale" and r["category"] == cat)
        brands_with_cat = sum(1 for b in competitor_brands
                              if any(r["category"] == cat for r in by_brand.get(b, [])))
        foxtale_count = foxtale_cats.get(cat, 0)
        if brands_with_cat >= 3 and foxtale_count < 3:
            gaps.append((cat, brands_with_cat, competitor_skus, foxtale_count))
    gaps.sort(key=lambda x: -x[2])

    print(f"\n  {'Category':<14}  {'Competitor Brands':<17}  {'Competitor SKUs':<15}  {'Foxtale SKUs':<12}")
    print(f"  {'-'*14}  {'-'*17}  {'-'*15}  {'-'*12}")
    for cat, cb, cs, fs in gaps:
        print(f"  {cat:<14}  {cb:<17}  {cs:<15}  {fs:<12}")

    # -----------------------------------------------------------------------
    # Save summary JSON
    # -----------------------------------------------------------------------
    summary = {}
    for b in brands:
        prices = [r["price"] for r in by_brand[b]]
        ratings = [r["rating"] for r in by_brand[b]]
        cats = list(set(r["category"] for r in by_brand[b]))
        summary[b] = {
            "total_skus": len(by_brand[b]),
            "categories": cats,
            "num_categories": len(cats),
            "avg_price": round(mean(prices), 2),
            "median_price": round(median(prices), 2),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_rating": round(mean(ratings), 3),
            "median_rating": round(median(ratings), 2),
            "products_above_45": sum(1 for x in ratings if x >= 4.5),
        }

    whitespace = [{"category": c, "competitor_brands": cb, "competitor_skus": cs, "foxtale_skus": fs}
                  for c, cb, cs, fs in gaps]

    output = {
        "total_products": len(products),
        "brands": summary,
        "whitespace_gaps": whitespace,
        "category_competition": {
            cat: {
                "total_skus": len(by_cat[cat]),
                "brands_present": list(set(r["brand"] for r in by_cat[cat])),
            }
            for cat in all_categories
        }
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Summary saved to: {out_path}")
    print("\nAnalysis complete.\n")


if __name__ == "__main__":
    main()
