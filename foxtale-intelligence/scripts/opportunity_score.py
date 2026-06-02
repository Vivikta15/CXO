"""
Opportunity Score Engine
========================
Scores each skincare category 1–100 for Foxtale using a three-factor model:

    Opportunity Score = Growth Potential × Competitor Weakness × Foxtale Absence
                        (each sub-score 1–10, product normalised to 1–100)

Sub-score definitions
---------------------
Growth Potential  — How large and validated is demand in this category?
                    Signals: number of brands competing, total SKUs, avg review count
                    (more brands + more reviews = market is real and growing)

Competitor Weakness — How exploitable is the competitive field?
                    Signals: market fragmentation (low HHI = no dominant player),
                    avg competitor discount (high discount = weak pricing power),
                    inverted avg competitor rating (lower ratings = product gaps)

Foxtale Absence   — How much room does Foxtale have to capture share?
                    Signals: share of SKUs Foxtale owns in category
                    (0 SKUs = full absence = max score of 10)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSV  = BASE / "data" / "products.csv"
OUT_CSV  = BASE / "reports" / "opportunity_scores.csv"
OUT_JSON = BASE / "reports" / "opportunity_scores.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def minmax(series: pd.Series, low: float = 1.0, high: float = 10.0) -> pd.Series:
    """Rescale a Series to [low, high]. Handles zero-range gracefully."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([high] * len(series), index=series.index)
    return low + (series - mn) / (mx - mn) * (high - low)


def herfindahl(group: pd.Series) -> float:
    """Herfindahl-Hirschman Index for brand concentration within a category."""
    shares = group.value_counts(normalize=True)
    return float((shares ** 2).sum())


# ---------------------------------------------------------------------------
# Load & aggregate
# ---------------------------------------------------------------------------

df = pd.read_csv(CSV)
df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0)
df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").fillna(0)

cat = df.groupby("category").agg(
    total_skus    = ("product_name", "count"),
    num_brands    = ("brand",        "nunique"),
    foxtale_skus  = ("brand",        lambda x: (x == "Foxtale").sum()),
    avg_price     = ("price",        "mean"),
    avg_rating    = ("rating",       "mean"),
    avg_reviews   = ("review_count", "mean"),
    avg_discount  = ("discount",     "mean"),
).copy()

# HHI per category (exclude Foxtale to measure competitor concentration)
comp_df = df[df["brand"] != "Foxtale"]
cat["hhi"] = comp_df.groupby("category")["brand"].apply(herfindahl).reindex(cat.index).fillna(1.0)

# Competitor-only avg rating
cat["comp_avg_rating"] = (
    comp_df.groupby("category")["rating"].mean()
    .reindex(cat.index)
    .fillna(cat["avg_rating"])
)

# Foxtale SKU share in category
cat["foxtale_share"] = cat["foxtale_skus"] / cat["total_skus"]


# ---------------------------------------------------------------------------
# Sub-score 1 — Growth Potential (1–10)
# ---------------------------------------------------------------------------
# Brand breadth: how many of the 5 brands are in this category
brand_breadth = minmax(cat["num_brands"])

# SKU volume: total category size signals validated demand
sku_volume = minmax(cat["total_skus"])

# Review depth: avg review count proxies consumer engagement
review_depth = minmax(cat["avg_reviews"])

# Weighted composite
cat["growth_potential"] = (0.40 * brand_breadth + 0.35 * sku_volume + 0.25 * review_depth).round(3)


# ---------------------------------------------------------------------------
# Sub-score 2 — Competitor Weakness (1–10)
# ---------------------------------------------------------------------------
# Fragmentation: low HHI = fragmented = opportunity (invert HHI)
fragmentation = minmax(1 - cat["hhi"])   # high score = fragmented market

# Discount pressure: high avg discount = brands are struggling to hold price
discount_signal = minmax(cat["avg_discount"])

# Rating gap: lower competitor ratings signal product quality gaps
rating_gap = minmax(cat["comp_avg_rating"].max() - cat["comp_avg_rating"])  # invert

# Weighted composite
cat["competitor_weakness"] = (0.40 * fragmentation + 0.35 * discount_signal + 0.25 * rating_gap).round(3)


# ---------------------------------------------------------------------------
# Sub-score 3 — Foxtale Absence (1–10)
# ---------------------------------------------------------------------------
# Full absence = 10, proportional presence reduces the score
# Formula: 10 × (1 - foxtale_share) — already in [0,1] range; rescale to [1,10]
raw_absence = 1 - cat["foxtale_share"]
cat["foxtale_absence"] = (1 + raw_absence * 9).round(3)   # maps 0→1 present, 1→10 absent


# ---------------------------------------------------------------------------
# Composite Opportunity Score (1–100)
# ---------------------------------------------------------------------------
raw_score = cat["growth_potential"] * cat["competitor_weakness"] * cat["foxtale_absence"]
cat["opportunity_score_raw"] = raw_score

# Normalise product to 1–100
lo, hi = raw_score.min(), raw_score.max()
cat["opportunity_score"] = (1 + (raw_score - lo) / (hi - lo) * 99).round(1)

# Rank
cat = cat.sort_values("opportunity_score", ascending=False)
cat.insert(0, "rank", range(1, len(cat) + 1))

# Priority tier
def tier(score):
    if score >= 75:  return "🔴 Immediate Priority"
    if score >= 50:  return "🟠 High Opportunity"
    if score >= 25:  return "🟡 Monitor"
    return              "🟢 Defended"

cat["priority_tier"] = cat["opportunity_score"].apply(tier)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

display_cols = [
    "rank", "priority_tier", "opportunity_score",
    "growth_potential", "competitor_weakness", "foxtale_absence",
    "num_brands", "total_skus", "foxtale_skus",
    "avg_price", "avg_rating", "avg_discount",
]

out = cat[display_cols].copy()
out.columns = [
    "Rank", "Priority Tier", "Opportunity Score",
    "Growth Potential", "Competitor Weakness", "Foxtale Absence",
    "# Brands", "Total SKUs", "Foxtale SKUs",
    "Avg Price ₹", "Avg Rating", "Avg Discount %",
]

OUT_CSV.parent.mkdir(exist_ok=True)
out.to_csv(OUT_CSV, index_label="Category")

# JSON for dashboard consumption
records = []
for category, row in cat.iterrows():
    records.append({
        "category":            category,
        "rank":                int(row["rank"]),
        "opportunity_score":   round(float(row["opportunity_score"]), 1),
        "growth_potential":    round(float(row["growth_potential"]), 2),
        "competitor_weakness": round(float(row["competitor_weakness"]), 2),
        "foxtale_absence":     round(float(row["foxtale_absence"]), 2),
        "priority_tier":       row["priority_tier"],
        "num_brands":          int(row["num_brands"]),
        "total_skus":          int(row["total_skus"]),
        "foxtale_skus":        int(row["foxtale_skus"]),
        "avg_price":           round(float(row["avg_price"]), 0),
        "avg_rating":          round(float(row["avg_rating"]), 2),
        "avg_discount":        round(float(row["avg_discount"]), 1),
    })

with open(OUT_JSON, "w") as f:
    json.dump(records, f, indent=2)


# ---------------------------------------------------------------------------
# Print ranked table
# ---------------------------------------------------------------------------

print("\n" + "=" * 90)
print("  FOXTALE CATEGORY OPPORTUNITY SCORE  —  Ranked 1 to 100")
print("  Score = Growth Potential × Competitor Weakness × Foxtale Absence")
print("=" * 90)
print(f"\n{'Rank':<5} {'Category':<14} {'Score':>7}  {'Tier':<22}  "
      f"{'Growth':>7} {'Weakness':>9} {'Absence':>8}  "
      f"{'Brands':>7} {'Tot.SKU':>8} {'Fox.SKU':>8}")
print("-" * 90)
for category, row in cat.iterrows():
    print(
        f"  {int(row['rank']):<3} {category:<14} {row['opportunity_score']:>7.1f}  "
        f"{row['priority_tier']:<22}  "
        f"{row['growth_potential']:>7.2f} {row['competitor_weakness']:>9.2f} {row['foxtale_absence']:>8.2f}  "
        f"{int(row['num_brands']):>7} {int(row['total_skus']):>8} {int(row['foxtale_skus']):>8}"
    )
print("=" * 90)
print(f"\nSaved → {OUT_CSV}")
print(f"Saved → {OUT_JSON}\n")
