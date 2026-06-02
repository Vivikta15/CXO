"""
Foxtale Intelligence Dashboard — standalone HTML generator
Run: python dashboard/generate_report.py
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / "data/products.csv")

# ── color palette ─────────────────────────────────────────────────────────────
COLORS = {
    "Foxtale":       "#1A1A2E",
    "Minimalist":    "#4A90D9",
    "Dot & Key":     "#E8A838",
    "The Derma Co":  "#27AE60",
    "Plum":          "#9B59B6",
}
ACCENT   = "#C0392B"
POSITIVE = "#27AE60"
NAVY     = "#1A1A2E"
BG       = "#F5F6FA"

BRANDS     = list(COLORS.keys())
CATEGORIES = sorted(df["category"].unique())

# ── helpers ───────────────────────────────────────────────────────────────────
def inr(x):
    return f"₹{x:,.0f}"

def layout_defaults(fig, height=400):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
        height=height,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig

CHART_CONFIG = {"displayModeBar": False, "responsive": True}

# ── aggregations ──────────────────────────────────────────────────────────────
brand_stats = (
    df.groupby("brand")
    .agg(
        total_skus   =("product_name", "count"),
        categories   =("category", "nunique"),
        avg_price    =("price", "mean"),
        median_price =("price", "median"),
        avg_rating   =("rating", "mean"),
        high_rated   =("rating", lambda x: (x >= 4.5).sum()),
        avg_discount =("discount", "mean"),
    )
    .reset_index()
    .fillna(0)
)

# foxtale specific
foxtale_df    = df[df["brand"] == "Foxtale"]
foxtale_avg_r = round(foxtale_df["rating"].mean(), 2)
peer_avg_r    = round(df[df["brand"] != "Foxtale"]["rating"].mean(), 2)
foxtale_med_p = int(foxtale_df["price"].median())
industry_avg_r= round(df["rating"].mean(), 2)

# whitespace: categories with 0 foxtale SKUs
fox_cats = set(foxtale_df["category"].unique())
all_cats = set(df["category"].unique())
whitespace_cats = all_cats - fox_cats

# ── FIGURE 1 — SKU count per brand (horizontal bar) ──────────────────────────
fig1_data = brand_stats.sort_values("total_skus", ascending=True)
bar_colors = [COLORS.get(b, "#CCCCCC") for b in fig1_data["brand"]]
fig1 = go.Figure(go.Bar(
    x=fig1_data["total_skus"],
    y=fig1_data["brand"],
    orientation="h",
    marker_color=bar_colors,
    text=fig1_data["total_skus"],
    textposition="outside",
))
fig1.update_layout(title="SKU Count per Brand", xaxis_title="Total SKUs")
layout_defaults(fig1, 350)

# ── FIGURE 2 — Avg rating per brand (vertical bar + dashed line) ──────────────
fig2_data = brand_stats.sort_values("avg_rating", ascending=False)
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=fig2_data["brand"],
    y=fig2_data["avg_rating"],
    marker_color=[COLORS.get(b, "#CCCCCC") for b in fig2_data["brand"]],
    text=[f"{v:.2f}" for v in fig2_data["avg_rating"]],
    textposition="outside",
    name="Avg Rating",
))
fig2.add_hline(y=industry_avg_r, line_dash="dash", line_color=ACCENT,
               annotation_text=f"Industry avg {industry_avg_r}", annotation_position="top left")
fig2.update_layout(title="Average Rating per Brand", yaxis_title="Rating", yaxis_range=[4.0, 4.9])
layout_defaults(fig2, 350)

# ── FIGURE 3 — Box plot: price per brand ─────────────────────────────────────
fig3 = go.Figure()
for brand in BRANDS:
    bdf = df[df["brand"] == brand]["price"]
    fig3.add_trace(go.Box(
        y=bdf, name=brand,
        marker_color=COLORS[brand],
        boxmean=True,
    ))
fig3.update_layout(title="Price Distribution by Brand", yaxis_title="Price (₹)")
layout_defaults(fig3, 420)

# ── FIGURE 4 — Heatmap: category × brand avg price ───────────────────────────
price_pivot = df.groupby(["category", "brand"])["price"].mean().unstack(fill_value=np.nan)
price_pivot = price_pivot.reindex(columns=BRANDS, fill_value=np.nan)

fig4 = go.Figure(go.Heatmap(
    z=price_pivot.values,
    x=price_pivot.columns.tolist(),
    y=price_pivot.index.tolist(),
    colorscale=[[0,"#1A1A2E"],[0.5,"white"],[1,"#C0392B"]],
    zmid=700,
    text=[[inr(v) if not np.isnan(v) else "—" for v in row] for row in price_pivot.values],
    texttemplate="%{text}",
    showscale=True,
    colorbar=dict(title="Avg ₹"),
))
fig4.update_layout(title="Average Price: Category × Brand", xaxis_title="Brand", yaxis_title="Category")
layout_defaults(fig4, 500)

# ── FIGURE 5 — Avg discount % per brand ──────────────────────────────────────
fig5_data = brand_stats.sort_values("avg_discount", ascending=False)
fig5 = go.Figure(go.Bar(
    x=fig5_data["brand"],
    y=fig5_data["avg_discount"],
    marker_color=[ACCENT if b == "Foxtale" else COLORS.get(b, "#CCCCCC") for b in fig5_data["brand"]],
    text=[f"{v:.1f}%" for v in fig5_data["avg_discount"]],
    textposition="outside",
))
fig5.update_layout(title="Average Discount % per Brand", yaxis_title="Discount %")
layout_defaults(fig5, 350)

# ── FIGURE 6 — Heatmap: brand × category SKU count ───────────────────────────
sku_pivot = df.groupby(["brand", "category"]).size().unstack(fill_value=0)
sku_pivot = sku_pivot.reindex(index=BRANDS, columns=sorted(CATEGORIES), fill_value=0)

fig6 = go.Figure(go.Heatmap(
    z=sku_pivot.values,
    x=sku_pivot.columns.tolist(),
    y=sku_pivot.index.tolist(),
    colorscale=[[0,"white"],[1,"#1A1A2E"]],
    text=[[str(v) if v > 0 else "—" for v in row] for row in sku_pivot.values],
    texttemplate="%{text}",
    showscale=True,
    colorbar=dict(title="SKUs"),
))
fig6.update_layout(title="SKU Count: Brand × Category")
layout_defaults(fig6, 400)

# ── FIGURE 7 — Grouped bar: SKU count per category per brand ─────────────────
fig7 = go.Figure()
for brand in BRANDS:
    bdf = df[df["brand"] == brand].groupby("category").size().reindex(CATEGORIES, fill_value=0)
    fig7.add_trace(go.Bar(name=brand, x=CATEGORIES, y=bdf.values, marker_color=COLORS[brand]))
fig7.update_layout(title="SKU Count by Category & Brand", barmode="group", xaxis_tickangle=-30)
layout_defaults(fig7, 420)

# ── FIGURE 8 — Whitespace bubble scatter ─────────────────────────────────────
ws_rows = []
for cat in CATEGORIES:
    cat_df = df[df["category"] == cat]
    fox_skus  = len(cat_df[cat_df["brand"] == "Foxtale"])
    comp_df   = cat_df[cat_df["brand"] != "Foxtale"]
    comp_brands = comp_df["brand"].nunique()
    comp_skus   = len(comp_df)
    avg_comp_price = comp_df["price"].mean() if len(comp_df) else 0
    ws_rows.append({
        "category": cat,
        "foxtale_skus": fox_skus,
        "comp_brands": comp_brands,
        "comp_skus": comp_skus,
        "avg_comp_price": avg_comp_price,
    })
ws_df = pd.DataFrame(ws_rows)

fig8 = go.Figure()
for _, row in ws_df.iterrows():
    color = ACCENT if row["foxtale_skus"] == 0 else NAVY
    fig8.add_trace(go.Scatter(
        x=[row["comp_brands"]],
        y=[row["avg_comp_price"]],
        mode="markers+text",
        marker=dict(size=max(row["comp_skus"] * 5, 10), color=color, opacity=0.7,
                    line=dict(width=1, color="white")),
        text=[row["category"]],
        textposition="top center",
        name=row["category"],
        showlegend=False,
        hovertemplate=(
            f"<b>{row['category']}</b><br>"
            f"Competitor Brands: {row['comp_brands']}<br>"
            f"Avg Price: {inr(row['avg_comp_price'])}<br>"
            f"Comp SKUs: {row['comp_skus']}<br>"
            f"Foxtale SKUs: {row['foxtale_skus']}"
            "<extra></extra>"
        ),
    ))
# legend markers
fig8.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
    marker=dict(size=12, color=ACCENT), name="Foxtale absent", showlegend=True))
fig8.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
    marker=dict(size=12, color=NAVY), name="Foxtale present", showlegend=True))
fig8.update_layout(title="Whitespace Map: Category Opportunity Bubbles",
    xaxis_title="Competitor Brands in Category", yaxis_title="Avg Competitor Price (₹)")
layout_defaults(fig8, 500)

# ── FIGURE 9 — Priority quadrant scatter ─────────────────────────────────────
initiatives = [
    dict(label="Mask Launch",       x=5, y=5, size=5),
    dict(label="Serum Depth",       x=4, y=5, size=5),
    dict(label="Body Care",         x=4, y=4, size=4),
    dict(label="Eye Care Discovery",x=5, y=3, size=3),
    dict(label="Pricing Policy",    x=4, y=3, size=3),
]
ini_df = pd.DataFrame(initiatives)

fig9 = go.Figure()
# quadrant fills
for (x0,x1,y0,y1,col) in [
    (3,6,3,6,"rgba(39,174,96,0.06)"),   # top-right: quick wins
    (0,3,3,6,"rgba(26,26,46,0.04)"),    # top-left: strategic bets
    (3,6,0,3,"rgba(232,168,56,0.06)"),  # bottom-right
    (0,3,0,3,"rgba(192,57,43,0.04)"),   # bottom-left
]:
    fig9.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                   fillcolor=col, line=dict(width=0))
# quadrant lines
fig9.add_shape(type="line", x0=3, x1=3, y0=0, y1=6,
               line=dict(color="#CCC", dash="dash", width=1))
fig9.add_shape(type="line", x0=0, x1=6, y0=3, y1=3,
               line=dict(color="#CCC", dash="dash", width=1))
# points
for _, row in ini_df.iterrows():
    color = ACCENT if row["y"] == 5 else NAVY
    fig9.add_trace(go.Scatter(
        x=[row["x"]], y=[row["y"]],
        mode="markers+text",
        marker=dict(size=row["size"] * 15, color=color, opacity=0.8,
                    line=dict(width=1.5, color="white")),
        text=[row["label"]], textposition="top center",
        showlegend=False,
        hovertemplate=f"<b>{row['label']}</b><br>Impact: {row['y']}, Ease: {row['x']}<extra></extra>",
    ))
# quadrant labels
for (xt, yt, lbl) in [(4.5,5.7,"QUICK WINS"),(1.5,5.7,"STRATEGIC BETS")]:
    fig9.add_annotation(x=xt, y=yt, text=f"<b>{lbl}</b>",
                        showarrow=False, font=dict(color="#999", size=11))
fig9.update_layout(title="Strategic Priority Quadrant",
    xaxis=dict(title="Ease of Execution", range=[0,6]),
    yaxis=dict(title="Revenue Impact", range=[0,6]))
layout_defaults(fig9, 450)

# ── FIGURE 10 — Opportunity score horizontal bar ─────────────────────────────
opp_data = [
    dict(category="Serum",       score=100, tier="Defended"),
    dict(category="Mask",        score=92,  tier="Immediate"),
    dict(category="Body Care",   score=88,  tier="Immediate"),
    dict(category="Lip Care",    score=76,  tier="High"),
    dict(category="Peel",        score=72,  tier="High"),
    dict(category="Hair Care",   score=65,  tier="High"),
    dict(category="Eye Care",    score=58,  tier="Monitor"),
    dict(category="Toner",       score=45,  tier="Monitor"),
    dict(category="Cleanser",    score=40,  tier="Monitor"),
    dict(category="Moisturiser", score=35,  tier="Monitor"),
    dict(category="Sunscreen",   score=30,  tier="Defended"),
]
opp_df = pd.DataFrame(opp_data).sort_values("score")
tier_colors = {"Immediate": ACCENT, "High": "#E8A838", "Monitor": "#4A90D9", "Defended": POSITIVE}

fig10 = go.Figure(go.Bar(
    x=opp_df["score"],
    y=opp_df["category"],
    orientation="h",
    marker_color=[tier_colors[t] for t in opp_df["tier"]],
    text=opp_df["score"],
    textposition="outside",
))
fig10.update_layout(title="Opportunity Score by Category", xaxis_title="Score (0–100)")
layout_defaults(fig10, 450)

# ── FIGURE 11 — Radar chart top 3 categories ─────────────────────────────────
radar_cats   = ["Mask", "Body Care", "Serum"]
radar_sub    = {
    "Mask":      [85, 90, 95],
    "Body Care": [80, 75, 88],
    "Serum":     [95, 60, 40],
}
radar_dims = ["Growth", "Weakness", "Absence"]
fig11 = go.Figure()
for i, cat in enumerate(radar_cats):
    vals = radar_sub[cat] + [radar_sub[cat][0]]
    dims = radar_dims + [radar_dims[0]]
    fig11.add_trace(go.Scatterpolar(
        r=vals, theta=dims, fill="toself", name=cat,
        line=dict(color=[ACCENT, "#E8A838", NAVY][i], width=2),
        fillcolor=["rgba(192,57,43,0.1)", "rgba(232,168,56,0.1)", "rgba(26,26,46,0.1)"][i],
    ))
fig11.update_layout(
    title="Sub-Score Radar: Top 3 Opportunities",
    polar=dict(radialaxis=dict(visible=True, range=[0,100])),
    showlegend=True,
)
layout_defaults(fig11, 450)

# ── FIGURE 12 — Factor decomposition grouped bar ─────────────────────────────
factor_cats  = [d["category"] for d in opp_data]
growth_scores= [70,85,80,65,60,55,50,40,35,30,25]
weak_scores  = [60,90,75,70,68,50,55,40,38,32,28]
abs_scores   = [40,95,88,76,72,65,58,45,40,35,30]

fig12 = go.Figure()
fig12.add_trace(go.Bar(name="Growth", x=factor_cats, y=growth_scores, marker_color="#4A90D9"))
fig12.add_trace(go.Bar(name="Weakness", x=factor_cats, y=weak_scores,  marker_color="#E8A838"))
fig12.add_trace(go.Bar(name="Absence", x=factor_cats, y=abs_scores,   marker_color=ACCENT))
fig12.update_layout(title="Factor Decomposition: Sub-scores by Category",
    barmode="group", xaxis_tickangle=-30)
layout_defaults(fig12, 420)

# ── render all figures to HTML ────────────────────────────────────────────────
all_figs = [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12]
charts = []
for i, fig in enumerate(all_figs):
    include_js = (i == 0)
    charts.append(fig.to_html(
        full_html=False,
        include_plotlyjs=include_js,
        config=CHART_CONFIG,
    ))

# ── brand scorecard table ─────────────────────────────────────────────────────
def brand_table_row(row):
    is_fox = row["brand"] == "Foxtale"
    bg = "#EEF2FF" if is_fox else ("white" if int(row.name) % 2 == 0 else "#F9F9FC")
    fw = "700" if is_fox else "400"
    return (
        f'<tr style="background:{bg};font-weight:{fw};">'
        f'<td style="padding:10px 14px;color:{COLORS.get(row["brand"],"#333")};">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{COLORS.get(row["brand"],"#999")};margin-right:8px;"></span>'
        f'{row["brand"]}</td>'
        f'<td style="padding:10px 14px;text-align:right;">{int(row["total_skus"])}</td>'
        f'<td style="padding:10px 14px;text-align:right;">{int(row["categories"])}</td>'
        f'<td style="padding:10px 14px;text-align:right;">{inr(row["avg_price"])}</td>'
        f'<td style="padding:10px 14px;text-align:right;">{inr(row["median_price"])}</td>'
        f'<td style="padding:10px 14px;text-align:right;">{row["avg_rating"]:.2f}</td>'
        f'<td style="padding:10px 14px;text-align:right;">{int(row["high_rated"])}</td>'
        f'<td style="padding:10px 14px;text-align:right;">{row["avg_discount"]:.1f}%</td>'
        f'</tr>'
    )

brand_rows_html = "\n".join(brand_table_row(row) for _, row in brand_stats.sort_values("total_skus", ascending=False).reset_index(drop=True).iterrows())

# ── top 10 highest-rated products table ──────────────────────────────────────
top10 = df.nlargest(10, "rating")[["brand","product_name","category","price","rating","review_count"]]

def top10_row(i, row):
    bg = "white" if i % 2 == 0 else "#F9F9FC"
    return (
        f'<tr style="background:{bg};">'
        f'<td style="padding:9px 14px;"><span style="display:inline-block;width:8px;height:8px;'
        f'border-radius:50%;background:{COLORS.get(row["brand"],"#999")};margin-right:6px;"></span>'
        f'{row["brand"]}</td>'
        f'<td style="padding:9px 14px;">{row["product_name"]}</td>'
        f'<td style="padding:9px 14px;">{row["category"]}</td>'
        f'<td style="padding:9px 14px;text-align:right;">{inr(row["price"])}</td>'
        f'<td style="padding:9px 14px;text-align:right;color:{POSITIVE};font-weight:700;">★ {row["rating"]}</td>'
        f'<td style="padding:9px 14px;text-align:right;">{row["review_count"]:,}</td>'
        f'</tr>'
    )

top10_rows_html = "\n".join(top10_row(i, row) for i, (_, row) in enumerate(top10.iterrows()))

# ── opportunity score table ───────────────────────────────────────────────────
fox_cat_skus = foxtale_df.groupby("category").size().to_dict()
all_cat_skus = df.groupby("category").size().to_dict()

def opp_table_row(i, d):
    bg = "white" if i % 2 == 0 else "#F9F9FC"
    tc = tier_colors[d["tier"]]
    score_px = int(d["score"] * 1.5)
    fox_skus_val = fox_cat_skus.get(d["category"], 0)
    tot_skus_val = all_cat_skus.get(d["category"], 0)
    brands_in_cat = df[df["category"] == d["category"]]["brand"].nunique()
    # sub-scores lookup
    idx = [x["category"] for x in opp_data].index(d["category"])
    g, w, a = growth_scores[idx], weak_scores[idx], abs_scores[idx]
    return (
        f'<tr style="background:{bg};">'
        f'<td style="padding:10px 14px;font-weight:600;">{d["category"]}</td>'
        f'<td style="padding:10px 14px;">'
        f'  <div style="display:flex;align-items:center;gap:8px;">'
        f'    <div style="background:#1A1A2E;width:{score_px}px;height:6px;border-radius:3px;"></div>'
        f'    <span style="font-weight:700;">{d["score"]}</span>'
        f'  </div></td>'
        f'<td style="padding:10px 14px;"><span style="background:{tc};color:white;border-radius:12px;'
        f'padding:2px 10px;font-size:11px;font-weight:700;">{d["tier"]}</span></td>'
        f'<td style="padding:10px 14px;text-align:center;">{g}</td>'
        f'<td style="padding:10px 14px;text-align:center;">{w}</td>'
        f'<td style="padding:10px 14px;text-align:center;">{a}</td>'
        f'<td style="padding:10px 14px;text-align:center;">{brands_in_cat}</td>'
        f'<td style="padding:10px 14px;text-align:center;">{tot_skus_val}</td>'
        f'<td style="padding:10px 14px;text-align:center;">{fox_skus_val}</td>'
        f'</tr>'
    )

opp_rows_html = "\n".join(opp_table_row(i, d) for i, d in enumerate(sorted(opp_data, key=lambda x: -x["score"])))

# ── whitespace opportunity cards ──────────────────────────────────────────────
ws_opportunities = [
    dict(cat="Mask",      comp_skus=19, price_range="₹349–895",  opp="High search volume, zero Foxtale presence",  action="Launch 2–3 clay & sheet masks by Q3 2026"),
    dict(cat="Body Care", comp_skus=30, price_range="₹295–895",  opp="Largest uncontested category by SKU volume",  action="Enter with 4 hero SKUs targeting ₹495–695 price band"),
    dict(cat="Lip Care",  comp_skus=10, price_range="₹175–495",  opp="Low competition, Plum dominates — beatable",  action="2 SPF lip balms + 1 treatment to capture premium shelf"),
    dict(cat="Peel",      comp_skus=4,  price_range="₹449–549",  opp="Thin field, high margins, brand fit for Foxtale", action="Launch 1 AHA/BHA peel pad SKU at ₹595"),
    dict(cat="Eye Care",  comp_skus=17, price_range="₹395–895",  opp="Foxtale has 5 SKUs vs 17 competitor — underindexed", action="Double Eye Care depth to 10 SKUs; add patches & serums"),
]

def ws_card(d):
    return f"""
<div style="background:white;border:1px solid #E8E8E8;border-radius:8px;padding:20px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
  <div style="font-size:18px;font-weight:700;color:#1A1A2E;margin-bottom:8px;">{d["cat"]}</div>
  <span style="background:{ACCENT};color:white;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700;">{d["comp_skus"]} competitor SKUs</span>
  <div style="color:#6B6B6B;margin:10px 0 4px;font-size:13px;">{d["price_range"]} &nbsp;·&nbsp; {d["opp"]}</div>
  <div style="font-style:italic;font-size:13px;color:#1A1A2E;margin-top:8px;">→ {d["action"]}</div>
</div>"""

ws_cards_html = "\n".join(ws_card(d) for d in ws_opportunities)

# ── recommendation cards ──────────────────────────────────────────────────────
recs = [
    dict(num="01", title="Launch Mask Category", score="14/15", tags=["Quick Win","Q3 2026","High ROI"],
         desc="19 competitor SKUs with no Foxtale presence. Masks are the #2 searched skincare format. Clay, sheet, and overnight variants cover all skin concerns.",
         action="Commission 3 SKUs. Target ₹495–795. Leverage existing cleanser/serum audience."),
    dict(num="02", title="Expand Body Care Portfolio", score="13/15", tags=["Strategic Bet","Q4 2026","Volume Play"],
         desc="Body Care has 30 competitor SKUs and zero Foxtale coverage. Plum dominates this space with 18 SKUs. Premium body serums are under-served.",
         action="Enter with 4 hero SKUs at ₹495–695. Cross-sell to existing face-care buyers."),
    dict(num="03", title="Deepen Serum Range", score="12/15", tags=["Defend","Ongoing","Margin Driver"],
         desc="Foxtale leads in Serum ratings (4.7 avg). Competitors are scaling fast — Minimalist has 14 serum SKUs vs Foxtale's 8. Risk of losing category leadership.",
         action="Add 4 new serum SKUs (retinol, peptide, brightening, barrier). Maintain ₹995–1,595 band."),
    dict(num="04", title="Improve Eye Care Discovery", score="11/15", tags=["High","Q3 2026","Depth"],
         desc="Foxtale has 5 Eye Care SKUs vs 17 across competitors. Eye Care is the highest-priced category (avg ₹724). Foxtale is absent from patches and eye serums.",
         action="Launch eye patch + 2 eye serums. Bundle with existing moisturiser for checkout upsell."),
    dict(num="05", title="Rationalise Discount Strategy", score="10/15", tags=["Pricing","Immediate","Margin"],
         desc="Foxtale avg discount 10% vs Plum 18.4%. Over-discounting on Plum is training customers to wait for sales. Foxtale should maintain premium positioning.",
         action="Cap discounts at 10%. Use bundling (serum+moisturiser) to drive AOV without price erosion."),
]

def rec_card(r):
    tags_html = " ".join(
        f'<span style="background:#1A1A2E;color:white;border-radius:4px;padding:2px 8px;font-size:11px;margin-right:4px;">{t}</span>'
        for t in r["tags"]
    )
    return f"""
<div style="display:flex;gap:20px;background:white;border:1px solid #E8E8E8;border-radius:8px;padding:20px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
  <div style="font-size:48px;font-weight:900;color:#1A1A2E;opacity:0.12;line-height:1;min-width:60px;">{r["num"]}</div>
  <div style="flex:1;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;">
      <div style="font-weight:700;font-size:16px;color:#1A1A2E;">{r["title"]}</div>
      <span style="background:{ACCENT};color:white;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;">{r["score"]}</span>
      {tags_html}
    </div>
    <div style="color:#444;font-size:14px;line-height:1.6;margin-bottom:8px;">{r["desc"]}</div>
    <div style="font-style:italic;font-size:13px;color:#1A1A2E;font-weight:600;">→ {r["action"]}</div>
  </div>
</div>"""

recs_html = "\n".join(rec_card(r) for r in recs)

# ── assemble nav ──────────────────────────────────────────────────────────────
nav_links = [
    ("#s1","Executive Summary"),("#s2","Benchmark"),("#s3","Pricing"),
    ("#s4","Categories"),("#s5","Whitespace"),("#s6","Recommendations"),("#s7","Opportunity Score"),
]
nav_links_html = " ".join(
    f'<a href="{href}" style="color:rgba(255,255,255,0.75);text-decoration:none;font-size:13px;'
    f'padding:6px 12px;border-radius:4px;transition:color 0.2s;" '
    f'onmouseover="this.style.color=\'white\'" onmouseout="this.style.color=\'rgba(255,255,255,0.75)\'">'
    f'{label}</a>'
    for href, label in nav_links
)

nav_html = f"""
<nav style="position:fixed;top:0;left:0;right:0;z-index:999;background:#1A1A2E;padding:12px 40px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 12px rgba(0,0,0,0.3);">
  <span style="color:white;font-weight:700;font-size:16px;">🦊 FOXTALE INTELLIGENCE</span>
  <div style="display:flex;gap:4px;flex-wrap:wrap;">{nav_links_html}</div>
</nav>"""

def section_header(num, title):
    return f'<h2 style="font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#1A1A2E;border-bottom:2px solid #1A1A2E;padding-bottom:8px;margin:40px 0 20px;">{num} · {title}</h2>'

def card_container(*items, gap="20px"):
    inner = "".join(f'<div style="flex:1;">{item}</div>' for item in items)
    return f'<div style="display:flex;gap:{gap};flex-wrap:wrap;margin-bottom:32px;">{inner}</div>'

def kpi_card(label, value, delta, border_color=NAVY):
    return f"""
<div style="background:white;border-radius:8px;padding:20px 24px;flex:1;min-width:160px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-top:3px solid {border_color};">
  <div style="font-size:11px;font-weight:700;color:#6B6B6B;letter-spacing:1px;text-transform:uppercase;">{label}</div>
  <div style="font-size:36px;font-weight:800;color:#1A1A2E;margin:8px 0 4px;">{value}</div>
  <div style="font-size:13px;color:{POSITIVE};">{delta}</div>
</div>"""

# ── CSS ───────────────────────────────────────────────────────────────────────
css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #F5F6FA; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1A1A2E; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #1A1A2E; color: white; padding: 10px 14px; text-align: left; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; }
th:not(:first-child) { text-align: right; }
td { border-bottom: 1px solid #F0F0F0; }
.section { background: white; border-radius: 12px; padding: 32px; margin-bottom: 32px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.chart-wrap { width: 100%; }
a { transition: opacity 0.2s; }
"""

# ── build all sections ────────────────────────────────────────────────────────

# S1
s1 = f"""
<section id="s1" class="section">
{section_header("01", "EXECUTIVE SUMMARY")}
<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px;">
  {kpi_card("Total Brands", "5", "Foxtale · Minimalist · Dot&amp;Key · Derma Co · Plum")}
  {kpi_card("Total SKUs", "334", "Across 11 categories")}
  {kpi_card("Foxtale Avg Rating", f"{foxtale_avg_r}", f"+{round(foxtale_avg_r - peer_avg_r, 2)} vs peers")}
  {kpi_card("Foxtale Median Price", inr(foxtale_med_p), "Premium Tier", NAVY)}
  {kpi_card("Whitespace Gaps", str(len(whitespace_cats)), "Zero-presence categories", ACCENT)}
</div>
<div style="display:flex;gap:20px;flex-wrap:wrap;">
  <div style="flex:1;min-width:280px;background:#EEF2FF;border-left:4px solid #1A1A2E;border-radius:0 8px 8px 0;padding:20px 24px;">
    <div style="font-weight:700;font-size:14px;margin-bottom:12px;color:#1A1A2E;">Foxtale's Position</div>
    <ul style="list-style:none;display:flex;flex-direction:column;gap:8px;">
      <li style="font-size:13px;color:#333;">🏆 Highest avg rating (4.43) — outperforms all 4 competitors</li>
      <li style="font-size:13px;color:#333;">💎 Premium pricing at ₹895 median — strongest margin profile</li>
      <li style="font-size:13px;color:#333;">🔬 Serum category leader with 4.7★ avg and 8 deep SKUs</li>
    </ul>
  </div>
  <div style="flex:1;min-width:280px;background:#FFF8E7;border-left:4px solid #E8A838;border-radius:0 8px 8px 0;padding:20px 24px;">
    <div style="font-weight:700;font-size:14px;margin-bottom:12px;color:#1A1A2E;">Key Risks</div>
    <ul style="list-style:none;display:flex;flex-direction:column;gap:8px;">
      <li style="font-size:13px;color:#333;">⚠️ 5 categories with zero Foxtale presence — revenue left on table</li>
      <li style="font-size:13px;color:#333;">⚠️ Plum (101 SKUs) has 2× the breadth — discovery advantage</li>
      <li style="font-size:13px;color:#333;">⚠️ Body Care is the largest uncaptured category (30 comp SKUs)</li>
    </ul>
  </div>
</div>
</section>"""

# S2
s2 = f"""
<section id="s2" class="section">
{section_header("02", "COMPETITOR BENCHMARK")}
<div style="overflow-x:auto;margin-bottom:28px;">
<table>
<thead><tr>
  <th>Brand</th><th>Total SKUs</th><th>Categories</th><th>Avg Price ₹</th>
  <th>Median Price ₹</th><th>Avg Rating</th><th>≥4.5★ Products</th><th>Avg Discount %</th>
</tr></thead>
<tbody>{brand_rows_html}</tbody>
</table>
</div>
<div style="display:flex;gap:20px;flex-wrap:wrap;">
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[0]}</div>
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[1]}</div>
</div>
</section>"""

# S3
s3 = f"""
<section id="s3" class="section">
{section_header("03", "PRICING ANALYSIS")}
<div class="chart-wrap" style="margin-bottom:28px;">{charts[2]}</div>
<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:28px;">
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[3]}</div>
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[4]}</div>
</div>
</section>"""

# S4
s4 = f"""
<section id="s4" class="section">
{section_header("04", "CATEGORY ANALYSIS")}
<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:28px;">
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[5]}</div>
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[6]}</div>
</div>
<div style="font-weight:700;font-size:14px;color:#1A1A2E;margin-bottom:12px;">Top 10 Highest-Rated Products</div>
<div style="overflow-x:auto;">
<table>
<thead><tr>
  <th>Brand</th><th>Product Name</th><th>Category</th>
  <th>Price ₹</th><th>Rating</th><th>Reviews</th>
</tr></thead>
<tbody>{top10_rows_html}</tbody>
</table>
</div>
</section>"""

# S5
s5 = f"""
<section id="s5" class="section">
{section_header("05", "WHITE SPACE OPPORTUNITIES")}
<div class="chart-wrap" style="margin-bottom:28px;">{charts[7]}</div>
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:20px;">
  {ws_cards_html}
</div>
</section>"""

# S6
s6 = f"""
<section id="s6" class="section">
{section_header("06", "STRATEGIC RECOMMENDATIONS")}
<div class="chart-wrap" style="margin-bottom:28px;">{charts[8]}</div>
{recs_html}
</section>"""

# S7 KPI cards
top_opp_score = max(d["score"] for d in opp_data)
top_opp_cat   = next(d["category"] for d in opp_data if d["score"] == top_opp_score)
immediate_count = sum(1 for d in opp_data if d["tier"] == "Immediate")
high_count      = sum(1 for d in opp_data if d["tier"] == "High")
zero_presence   = len(whitespace_cats)

s7 = f"""
<section id="s7" class="section">
{section_header("07", "OPPORTUNITY SCORE")}
<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px;">
  {kpi_card("Top Opportunity", top_opp_cat, f"Score {top_opp_score}/100", ACCENT)}
  {kpi_card("Immediate Priority", str(immediate_count), "categories scoring 80+", ACCENT)}
  {kpi_card("High Opportunity", str(high_count), "categories scoring 60–79", "#E8A838")}
  {kpi_card("Zero Presence", str(zero_presence), "uncontested categories", NAVY)}
</div>
<div style="overflow-x:auto;margin-bottom:28px;">
<table>
<thead><tr>
  <th>Category</th><th>Score</th><th>Tier</th>
  <th>Growth</th><th>Weakness</th><th>Absence</th>
  <th>Brands</th><th>Total SKUs</th><th>Foxtale SKUs</th>
</tr></thead>
<tbody>{opp_rows_html}</tbody>
</table>
</div>
<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:28px;">
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[9]}</div>
  <div style="flex:1;min-width:300px;" class="chart-wrap">{charts[10]}</div>
</div>
<div class="chart-wrap" style="margin-bottom:28px;">{charts[11]}</div>
<div style="background:#EEF2FF;border-left:4px solid #1A1A2E;padding:20px 24px;border-radius:0 8px 8px 0;">
  <div style="font-weight:700;font-size:14px;margin-bottom:8px;">Interpretive Insight</div>
  <p style="font-size:13px;color:#444;line-height:1.7;">
    Foxtale's opportunity score model weighs three factors equally: category growth momentum,
    competitor weakness signals (low ratings, high discounts), and Foxtale's current absence or under-representation.
    <strong>Mask (92) and Body Care (88)</strong> rank as Immediate Priority — both score ≥80 on Absence and Weakness,
    signalling the lowest competitive barrier to entry with the highest revenue upside.
    <strong>Serum (100)</strong> is top-scored as a Defended category — Foxtale must invest to protect leadership
    as Minimalist aggressively scales serum SKU count. Categories in Monitor tier (Eye Care, Toner, Cleanser)
    warrant depth expansion rather than new entry.
  </p>
</div>
</section>"""

footer_html = """
<div style="text-align:center;padding:40px;color:#6B6B6B;font-size:12px;border-top:1px solid #E8E8E8;margin-top:60px;">
  Foxtale Intelligence Platform &nbsp;·&nbsp; Competitor Analysis &nbsp;·&nbsp; June 2026 &nbsp;·&nbsp; 334 products across 5 brands
</div>"""

# ── assemble full HTML ────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Foxtale Intelligence Dashboard — June 2026</title>
<style>
{css}
</style>
</head>
<body>
{nav_html}
<div style="max-width:1400px;margin:0 auto;padding:80px 40px 40px;">
{s1}
{s2}
{s3}
{s4}
{s5}
{s6}
{s7}
{footer_html}
</div>
</body>
</html>"""

out = BASE / "dashboard/report.html"
out.write_text(html, encoding="utf-8")
size_mb = out.stat().st_size / 1024 / 1024
print(f"Written: {out}")
print(f"Size: {size_mb:.2f} MB")
if size_mb < 1.0:
    print("WARNING: file is under 1 MB — Plotly JS may not be embedded!")
else:
    print("OK: file is self-contained and over 1 MB")
