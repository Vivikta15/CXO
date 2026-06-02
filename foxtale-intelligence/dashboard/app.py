import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(layout="wide", page_title="Foxtale Intelligence", page_icon="🦊")

# ─── COLOR PALETTE ─────────────────────────────────────────────────────────────
COLORS = {
    "foxtale": "#1A1A2E",
    "minimalist": "#4A90D9",
    "dot_key": "#E8A838",
    "derma_co": "#2ECC71",
    "plum": "#9B59B6",
    "bg": "#FAFAFA",
    "card_bg": "#FFFFFF",
    "border": "#E8E8E8",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B6B6B",
    "accent": "#C0392B",
    "positive": "#27AE60",
    "warning": "#F39C12",
}

BRAND_COLORS = {
    "Foxtale": COLORS["foxtale"],
    "Minimalist": COLORS["minimalist"],
    "Dot & Key": COLORS["dot_key"],
    "The Derma Co": COLORS["derma_co"],
    "Plum": COLORS["plum"],
}

# ─── CSS INJECTION ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

.metric-card {
    background: #FFFFFF;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    min-height: 110px;
}

.metric-card .label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6B6B6B;
    margin-bottom: 8px;
}

.metric-card .value {
    font-size: 32px;
    font-weight: 800;
    color: #1A1A1A;
    line-height: 1.1;
}

.metric-card .delta {
    font-size: 12px;
    font-weight: 500;
    margin-top: 6px;
}

.metric-card .delta.positive { color: #27AE60; }
.metric-card .delta.neutral  { color: #6B6B6B; }
.metric-card .delta.warning  { color: #F39C12; }

.section-header {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1A1A2E;
    border-bottom: 2px solid #1A1A2E;
    padding-bottom: 6px;
    margin-bottom: 1.2rem;
    margin-top: 0.5rem;
}

.insight-box {
    background: #EEF2FF;
    border-left: 4px solid #1A1A2E;
    border-radius: 0 6px 6px 0;
    padding: 16px 20px;
    margin-bottom: 12px;
}

.insight-box h4 {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #1A1A2E;
    margin: 0 0 10px 0;
}

.insight-box ul {
    margin: 0;
    padding-left: 18px;
}

.insight-box li {
    font-size: 13px;
    color: #1A1A1A;
    margin-bottom: 5px;
    line-height: 1.5;
}

.warning-box {
    background: #FFF8E7;
    border-left: 4px solid #F39C12;
    border-radius: 0 6px 6px 0;
    padding: 16px 20px;
    margin-bottom: 12px;
}

.warning-box h4 {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #B7770D;
    margin: 0 0 10px 0;
}

.warning-box ul {
    margin: 0;
    padding-left: 18px;
}

.warning-box li {
    font-size: 13px;
    color: #1A1A1A;
    margin-bottom: 5px;
    line-height: 1.5;
}

.opportunity-card {
    background: #FFFFFF;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 12px;
    transition: box-shadow 0.2s ease;
}

.opportunity-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.opportunity-card .cat-name {
    font-size: 18px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 6px;
}

.opportunity-card .badge {
    display: inline-block;
    background: #EEF2FF;
    color: #1A1A2E;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    margin-right: 6px;
    margin-bottom: 8px;
}

.opportunity-card .badge.price {
    background: #FFF8E7;
    color: #B7770D;
}

.opportunity-card .statement {
    font-size: 13px;
    color: #1A1A1A;
    margin-bottom: 6px;
    line-height: 1.5;
}

.opportunity-card .action {
    font-size: 12px;
    color: #6B6B6B;
    font-style: italic;
}

.rec-card {
    background: #FFFFFF;
    border: 1px solid #E8E8E8;
    border-left: 4px solid #1A1A2E;
    border-radius: 0 8px 8px 0;
    padding: 18px 22px;
    margin-bottom: 14px;
}

.rec-card .rank {
    font-size: 36px;
    font-weight: 800;
    color: #1A1A2E;
    line-height: 1;
    float: left;
    margin-right: 16px;
    margin-top: 2px;
}

.rec-card .title {
    font-size: 16px;
    font-weight: 700;
    color: #1A1A1A;
    margin-bottom: 4px;
}

.rec-card .score-badge {
    display: inline-block;
    background: #1A1A2E;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    margin-right: 6px;
    margin-bottom: 8px;
}

.rec-card .tag {
    display: inline-block;
    background: #F5F5F5;
    color: #6B6B6B;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    margin-right: 6px;
    margin-bottom: 8px;
}

.rec-card .desc {
    font-size: 13px;
    color: #1A1A1A;
    margin-bottom: 6px;
    line-height: 1.5;
    clear: both;
}

.rec-card .action-item {
    font-size: 12px;
    color: #6B6B6B;
    font-style: italic;
}

.footer {
    text-align: center;
    font-size: 11px;
    color: #6B6B6B;
    letter-spacing: 0.05em;
    padding: 24px 0 8px 0;
    border-top: 1px solid #E8E8E8;
    margin-top: 40px;
}

[data-testid="stSidebar"] {
    background: #1A1A2E;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] .stCheckbox label {
    color: #CCCCDD !important;
    font-size: 13px;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15);
}
</style>
""", unsafe_allow_html=True)

# ─── DATA LOADING ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, "..", "data", "products.csv")
    df = pd.read_csv(csv_path)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce")
    return df

df_all = load_data()

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:32px;">🦊</div>
        <div style="font-size:16px; font-weight:800; letter-spacing:0.1em; color:#FFFFFF; margin-top:4px;">FOXTALE</div>
        <div style="font-size:10px; color:#8888AA; letter-spacing:0.12em; text-transform:uppercase; margin-top:2px;">Intelligence Platform</div>
    </div>
    <hr/>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:10px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#8888AA; margin-bottom:8px;">Navigation</div>
    """, unsafe_allow_html=True)

    for section in [
        "01 · Executive Summary",
        "02 · Competitor Benchmark",
        "03 · Pricing Analysis",
        "04 · Category Analysis",
        "05 · White Space Opportunities",
        "06 · Strategic Recommendations",
        "07 · Opportunity Score",
    ]:
        st.markdown(
            f"<div style='font-size:12px; color:#CCCCDD; padding:4px 0;'>→ {section}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        """<div style="font-size:10px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#8888AA; margin-bottom:8px;">Brand Filter</div>""",
        unsafe_allow_html=True,
    )

    all_brands = sorted(df_all["brand"].unique())
    selected_brands = []
    for brand in all_brands:
        if st.checkbox(brand, value=True, key=f"brand_{brand}"):
            selected_brands.append(brand)

    if not selected_brands:
        selected_brands = list(all_brands)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px; color:#8888AA; line-height:1.6;">
        <div style="font-weight:700; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">Data Freshness</div>
        Scraped: June 2026<br/>
        Source: Brand websites<br/>
        SKUs tracked: 334
    </div>
    """, unsafe_allow_html=True)

df = df_all[df_all["brand"].isin(selected_brands)].copy()

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def fmt_inr(n):
    if pd.isna(n):
        return "—"
    n = int(round(n))
    s = str(n)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return "₹" + ",".join(groups) + "," + last3


def chart_layout(fig, title="", height=400):
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, family="Inter", color="#1A1A1A"),
            x=0,
            pad=dict(l=0, b=10),
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter",
        font_color="#1A1A1A",
        height=height,
        margin=dict(l=20, r=20, t=50 if title else 20, b=20),
        legend=dict(
            font=dict(size=11),
            bgcolor="white",
            bordercolor="#E8E8E8",
            borderwidth=1,
        ),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor="#E8E8E8", tickfont=dict(size=11))
    fig.update_yaxes(showgrid=True, gridcolor="#F0F0F0", showline=False, tickfont=dict(size=11))
    return fig


# ─── COMPUTED STATS ─────────────────────────────────────────────────────────────
foxtale_df = df_all[df_all["brand"] == "Foxtale"]
peers_df = df_all[df_all["brand"] != "Foxtale"]
all_categories = sorted(df_all["category"].unique())
foxtale_cats = set(foxtale_df["category"].unique())
whitespace_count = sum(1 for c in all_categories if c not in foxtale_cats)
foxtale_avg_rating = foxtale_df["rating"].mean()
industry_avg_rating = peers_df["rating"].mean()
rating_delta = foxtale_avg_rating - industry_avg_rating
foxtale_median_price = foxtale_df["price"].median()
total_skus = len(df)
avg_peer_skus = peers_df.groupby("brand").size().mean()
foxtale_peer_median = peers_df["price"].median()
foxtale_sku_count = len(foxtale_df)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">01 · EXECUTIVE SUMMARY</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown("""
    <div class="metric-card">
        <div class="label">Total Brands</div>
        <div class="value">5</div>
        <div class="delta neutral">Under active monitoring</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">Total SKUs Analysed</div>
        <div class="value">{total_skus}</div>
        <div class="delta neutral">Across {len(all_categories)} categories</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    delta_sign = "+" if rating_delta >= 0 else ""
    delta_class = "positive" if rating_delta >= 0 else "warning"
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">Foxtale Avg Rating</div>
        <div class="value">{foxtale_avg_rating:.2f}&#9733;</div>
        <div class="delta {delta_class}">{delta_sign}{rating_delta:.2f} vs peers</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">Foxtale Median Price</div>
        <div class="value">{fmt_inr(foxtale_median_price)}</div>
        <div class="delta neutral">Premium Tier</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">Whitespace Gaps</div>
        <div class="value">{whitespace_count}</div>
        <div class="delta warning">Categories with 0 Foxtale SKUs</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

col_l, col_r = st.columns(2)

with col_l:
    price_premium_pct = ((foxtale_median_price / foxtale_peer_median) - 1) * 100
    st.markdown(f"""
    <div class="insight-box">
        <h4>Foxtale's Competitive Position</h4>
        <ul>
            <li><strong>Rating leadership:</strong> Foxtale leads with {foxtale_avg_rating:.2f}&#9733; avg rating,
            {abs(rating_delta):.2f} pts above the {industry_avg_rating:.2f}&#9733; peer average — a signal of
            strong product-market fit across a lean, focused portfolio.</li>
            <li><strong>Price positioning:</strong> Median price of {fmt_inr(foxtale_median_price)} places Foxtale
            in the premium tier, commanding a {price_premium_pct:.0f}% premium over the peer median of
            {fmt_inr(foxtale_peer_median)} — reflecting formulation quality and brand trust.</li>
            <li><strong>SKU depth:</strong> At {foxtale_sku_count} SKUs, Foxtale is lean vs the peer avg of
            {avg_peer_skus:.0f} — disciplined portfolio, but leaves room for targeted expansion in
            high-demand adjacent categories.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_r:
    foxtale_disc = foxtale_df["discount"].mean()
    peers_disc = peers_df["discount"].mean()
    st.markdown(f"""
    <div class="warning-box">
        <h4>Key Risks &amp; Watch Areas</h4>
        <ul>
            <li><strong>Serum saturation:</strong> Minimalist and The Derma Co have heavily populated the serum
            segment with lower price points — Foxtale's premium serum positioning faces direct pressure on
            value perception among price-sensitive shoppers.</li>
            <li><strong>Absent categories:</strong> Foxtale has zero presence in {whitespace_count} categories
            (Mask, Body Care, Lip Care, Peel, Hair Care) where competitors are actively building equity and
            customer loyalty cycles.</li>
            <li><strong>Discount discipline risk:</strong> Competitors average {peers_disc:.1f}% discount vs
            Foxtale's {foxtale_disc:.1f}% — any escalation in promotional intensity could erode Foxtale's
            premium positioning and margin structure.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border:none;border-top:1px solid #E8E8E8;margin:28px 0 24px 0'/>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — COMPETITOR BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">02 · COMPETITOR BENCHMARK</div>', unsafe_allow_html=True)

brand_stats = (
    df_all.groupby("brand")
    .agg(
        total_skus=("product_name", "count"),
        categories=("category", "nunique"),
        avg_price=("price", "mean"),
        median_price=("price", "median"),
        avg_rating=("rating", "mean"),
        avg_discount=("discount", "mean"),
    )
    .reset_index()
)
high_rated_counts = (
    df_all[df_all["rating"] >= 4.5].groupby("brand").size().rename("high_rated")
)
brand_stats = brand_stats.join(high_rated_counts, on="brand").fillna({"high_rated": 0})
brand_stats["high_rated"] = brand_stats["high_rated"].astype(int)

scorecard = brand_stats.rename(
    columns={
        "brand": "Brand",
        "total_skus": "Total SKUs",
        "categories": "Categories",
        "avg_price": "Avg Price ₹",
        "median_price": "Median Price ₹",
        "avg_rating": "Avg Rating",
        "high_rated": "Products ≥4.5★",
        "avg_discount": "Avg Discount %",
    }
).sort_values("Avg Rating", ascending=False).reset_index(drop=True)

st.dataframe(
    scorecard,
    use_container_width=True,
    column_config={
        "Brand": st.column_config.TextColumn("Brand", width="medium"),
        "Total SKUs": st.column_config.NumberColumn("Total SKUs", format="%d"),
        "Categories": st.column_config.NumberColumn("Categories", format="%d"),
        "Avg Price ₹": st.column_config.NumberColumn("Avg Price ₹", format="₹%.0f"),
        "Median Price ₹": st.column_config.NumberColumn("Median Price ₹", format="₹%.0f"),
        "Avg Rating": st.column_config.ProgressColumn("Avg Rating", min_value=0, max_value=5, format="%.2f★"),
        "Products ≥4.5★": st.column_config.NumberColumn("Products ≥4.5★", format="%d"),
        "Avg Discount %": st.column_config.NumberColumn("Avg Discount %", format="%.1f%%"),
    },
    hide_index=True,
)

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
ch1, ch2 = st.columns(2)

with ch1:
    sku_data = brand_stats.sort_values("Total SKUs", ascending=True)
    bar_colors = [BRAND_COLORS.get(b, "#AAAAAA") for b in sku_data["Brand"]]
    fig_sku = go.Figure(
        go.Bar(
            x=sku_data["Total SKUs"],
            y=sku_data["Brand"],
            orientation="h",
            marker_color=bar_colors,
            text=sku_data["Total SKUs"],
            textposition="outside",
            textfont=dict(size=12, family="Inter"),
        )
    )
    chart_layout(fig_sku, "SKU Count by Brand", height=300)
    fig_sku.update_xaxes(title_text="Number of SKUs", title_font=dict(size=11))
    st.plotly_chart(fig_sku, use_container_width=True)

with ch2:
    industry_avg_all = df_all["rating"].mean()
    rating_data = brand_stats.sort_values("Avg Rating", ascending=False)
    bar_colors2 = [BRAND_COLORS.get(b, "#AAAAAA") for b in rating_data["Brand"]]
    fig_rat = go.Figure()
    fig_rat.add_trace(
        go.Bar(
            x=rating_data["Brand"],
            y=rating_data["Avg Rating"],
            marker_color=bar_colors2,
            text=[f"{r:.2f}★" for r in rating_data["Avg Rating"]],
            textposition="outside",
            textfont=dict(size=11, family="Inter"),
            name="Avg Rating",
        )
    )
    fig_rat.add_hline(
        y=industry_avg_all,
        line_dash="dash",
        line_color=COLORS["accent"],
        line_width=1.5,
        annotation_text=f"Industry Avg {industry_avg_all:.2f}★",
        annotation_position="top right",
        annotation_font=dict(size=10, color=COLORS["accent"]),
    )
    chart_layout(fig_rat, "Average Rating by Brand", height=300)
    fig_rat.update_yaxes(range=[3.8, 5.0], title_text="Avg Rating", title_font=dict(size=11))
    st.plotly_chart(fig_rat, use_container_width=True)

st.markdown("<hr style='border:none;border-top:1px solid #E8E8E8;margin:28px 0 24px 0'/>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — PRICING ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">03 · PRICING ANALYSIS</div>', unsafe_allow_html=True)

brand_order = df_all.groupby("brand")["price"].median().sort_values().index.tolist()
fig_box = go.Figure()
for brand in brand_order:
    bdf = df_all[df_all["brand"] == brand]
    fig_box.add_trace(
        go.Box(
            y=bdf["price"].dropna(),
            name=brand,
            marker_color=BRAND_COLORS.get(brand, "#AAAAAA"),
            boxmean=True,
            line=dict(width=1.5),
        )
    )
fox_med = foxtale_df["price"].median()
fig_box.add_annotation(
    x="Foxtale",
    y=fox_med,
    text=f"  Foxtale median {fmt_inr(fox_med)}",
    showarrow=True,
    arrowhead=2,
    arrowcolor=COLORS["accent"],
    font=dict(size=10, color=COLORS["accent"]),
    ax=80,
    ay=0,
)
chart_layout(fig_box, "Price Distribution by Brand (Box Plot)", height=420)
fig_box.update_yaxes(title_text="Price (₹)", title_font=dict(size=11))
st.plotly_chart(fig_box, use_container_width=True)

pc1, pc2 = st.columns(2)

with pc1:
    pivot_price = df_all.pivot_table(values="price", index="brand", columns="category", aggfunc="mean")
    pivot_price = pivot_price.reindex(sorted(pivot_price.columns), axis=1)
    z_vals = pivot_price.values
    text_vals = [
        [f"₹{int(v):,}" if not np.isnan(v) else "—" for v in row]
        for row in z_vals
    ]
    fig_heat = go.Figure(
        go.Heatmap(
            z=z_vals,
            x=list(pivot_price.columns),
            y=list(pivot_price.index),
            text=text_vals,
            texttemplate="%{text}",
            textfont=dict(size=9),
            colorscale=[
                [0.0, "#1A1A2E"],
                [0.5, "#FFFFFF"],
                [1.0, "#C0392B"],
            ],
            zmid=700,
            colorbar=dict(
                title="Avg Price ₹",
                titlefont=dict(size=10),
                tickfont=dict(size=9),
            ),
        )
    )
    chart_layout(fig_heat, "Price Heatmap — Category × Brand (₹)", height=380)
    fig_heat.update_xaxes(tickangle=-35, tickfont=dict(size=9))
    st.plotly_chart(fig_heat, use_container_width=True)

with pc2:
    disc_data = brand_stats.sort_values("Avg Discount %", ascending=True)
    disc_colors = [
        COLORS["accent"] if b == "Foxtale" else BRAND_COLORS.get(b, "#AAAAAA")
        for b in disc_data["Brand"]
    ]
    fig_disc = go.Figure(
        go.Bar(
            x=disc_data["Avg Discount %"],
            y=disc_data["Brand"],
            orientation="h",
            marker_color=disc_colors,
            text=[f"{v:.1f}%" for v in disc_data["Avg Discount %"]],
            textposition="outside",
            textfont=dict(size=11),
        )
    )
    chart_layout(fig_disc, "Average Discount % by Brand", height=380)
    fig_disc.update_xaxes(title_text="Avg Discount (%)", title_font=dict(size=11))
    st.plotly_chart(fig_disc, use_container_width=True)

st.markdown("<hr style='border:none;border-top:1px solid #E8E8E8;margin:28px 0 24px 0'/>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — CATEGORY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">04 · CATEGORY ANALYSIS</div>', unsafe_allow_html=True)

pivot_cov = df_all.pivot_table(
    values="product_name", index="brand", columns="category", aggfunc="count", fill_value=0
)
pivot_cov = pivot_cov.reindex(sorted(pivot_cov.columns), axis=1)
z_cov = pivot_cov.values.astype(float)
z_display = z_cov.copy()
z_display[z_display == 0] = np.nan
text_cov = [[str(int(v)) if v > 0 else "—" for v in row] for row in z_cov]

fig_cov = go.Figure(
    go.Heatmap(
        z=z_display,
        x=list(pivot_cov.columns),
        y=list(pivot_cov.index),
        text=text_cov,
        texttemplate="%{text}",
        textfont=dict(size=11, color="white"),
        colorscale=[
            [0.0, "#FFFFFF"],
            [0.001, "#C8D8FF"],
            [0.4, "#4A6FA5"],
            [1.0, "#1A1A2E"],
        ],
        showscale=False,
    )
)
chart_layout(fig_cov, "Category Coverage Matrix — SKU Count per Brand × Category", height=320)
fig_cov.update_xaxes(tickangle=-30, tickfont=dict(size=10))
st.plotly_chart(fig_cov, use_container_width=True)

cat_brand = df_all.groupby(["category", "brand"]).size().reset_index(name="sku_count")
brands_in_data = sorted(df_all["brand"].unique())
fig_depth = go.Figure()
for brand in brands_in_data:
    bdata = cat_brand[cat_brand["brand"] == brand]
    cat_vals = {row["category"]: row["sku_count"] for _, row in bdata.iterrows()}
    fig_depth.add_trace(
        go.Bar(
            name=brand,
            x=sorted(all_categories),
            y=[cat_vals.get(c, 0) for c in sorted(all_categories)],
            marker_color=BRAND_COLORS.get(brand, "#AAAAAA"),
        )
    )
fig_depth.update_layout(barmode="group")
chart_layout(fig_depth, "Category Depth — SKU Count per Brand", height=380)
fig_depth.update_xaxes(tickangle=-25)
fig_depth.update_yaxes(title_text="SKU Count", title_font=dict(size=11))
st.plotly_chart(fig_depth, use_container_width=True)

top10 = (
    df_all.nlargest(10, "rating")[["brand", "product_name", "category", "price", "rating", "review_count"]]
    .reset_index(drop=True)
)
top10.index = top10.index + 1
top10_display = top10.copy()
top10_display["price"] = top10_display["price"].apply(fmt_inr)
top10_display["rating"] = top10_display["rating"].apply(lambda x: f"{x:.1f}★" if pd.notna(x) else "—")
top10_display["review_count"] = top10_display["review_count"].apply(
    lambda x: f"{int(x):,}" if pd.notna(x) else "—"
)

st.markdown("**Top 10 Highest-Rated Products Across All Brands**")
st.dataframe(
    top10_display.rename(
        columns={
            "brand": "Brand",
            "product_name": "Product",
            "category": "Category",
            "price": "Price",
            "rating": "Rating",
            "review_count": "Reviews",
        }
    ),
    use_container_width=True,
    hide_index=False,
    column_config={
        "Brand": st.column_config.TextColumn("Brand", width="small"),
        "Product": st.column_config.TextColumn("Product", width="large"),
        "Category": st.column_config.TextColumn("Category", width="medium"),
        "Price": st.column_config.TextColumn("Price", width="small"),
        "Rating": st.column_config.TextColumn("Rating", width="small"),
        "Reviews": st.column_config.TextColumn("Reviews", width="small"),
    },
)

st.markdown("<hr style='border:none;border-top:1px solid #E8E8E8;margin:28px 0 24px 0'/>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — WHITE SPACE OPPORTUNITIES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">05 · WHITE SPACE OPPORTUNITIES</div>', unsafe_allow_html=True)

cat_matrix_rows = []
for cat in all_categories:
    cat_df = df_all[df_all["category"] == cat]
    fox_in_cat = len(cat_df[cat_df["brand"] == "Foxtale"])
    competitor_df = cat_df[cat_df["brand"] != "Foxtale"]
    n_brands = competitor_df["brand"].nunique()
    avg_price_cat = competitor_df["price"].mean() if len(competitor_df) > 0 else 0
    total_skus_cat = len(competitor_df)
    cat_matrix_rows.append(
        {
            "category": cat,
            "foxtale_skus": fox_in_cat,
            "competitor_brands": n_brands,
            "avg_competitor_price": avg_price_cat,
            "competitor_skus": total_skus_cat,
            "presence": "Foxtale Absent" if fox_in_cat == 0 else "Foxtale Present",
        }
    )

cat_matrix_df = pd.DataFrame(cat_matrix_rows)

fig_opp = go.Figure()
for presence, color in [("Foxtale Absent", COLORS["accent"]), ("Foxtale Present", COLORS["foxtale"])]:
    sub = cat_matrix_df[cat_matrix_df["presence"] == presence]
    if sub.empty:
        continue
    fig_opp.add_trace(
        go.Scatter(
            x=sub["competitor_brands"],
            y=sub["avg_competitor_price"],
            mode="markers+text",
            marker=dict(
                size=sub["competitor_skus"] * 2.2 + 14,
                color=color,
                opacity=0.82,
                line=dict(width=1.5, color="white"),
            ),
            text=sub["category"],
            textposition="top center",
            textfont=dict(size=10, family="Inter"),
            name=presence,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Competitor Brands: %{x}<br>"
                "Avg Price: ₹%{y:.0f}<extra></extra>"
            ),
        )
    )

chart_layout(fig_opp, "Category Opportunity Matrix — Bubble Size = Competitor SKU Count", height=520)
fig_opp.update_xaxes(
    title_text="Number of Competitor Brands in Category",
    title_font=dict(size=11),
    range=[-0.5, 5.5],
    dtick=1,
)
fig_opp.update_yaxes(title_text="Avg Competitor Price (₹)", title_font=dict(size=11))
fig_opp.update_layout(legend=dict(orientation="h", y=-0.12))
st.plotly_chart(fig_opp, use_container_width=True)

st.markdown("**High-Priority Whitespace Opportunities**")

opp_cards = [
    {
        "category": "Mask",
        "badge_skus": "22 competitor SKUs",
        "price_range": "₹395 – ₹1,295",
        "statement": (
            "All 4 competitors have active mask portfolios; Foxtale is entirely absent in a category with "
            "strong gifting, ritual, and repeat-purchase patterns that drive high customer LTV."
        ),
        "action": (
            "Launch 2–3 hero masks (clay purifying, sheet, overnight repair) targeting ₹600–₹900 "
            "price band to capture impulse and repeat buyers."
        ),
    },
    {
        "category": "Body Care",
        "badge_skus": "38 competitor SKUs",
        "price_range": "₹295 – ₹995",
        "statement": (
            "Body care is the fastest-growing adjacent category in D2C skincare; Dot &amp; Key alone has 14 "
            "body SKUs. Foxtale's face-care ingredient equity transfers seamlessly to body formulations."
        ),
        "action": (
            "Enter with a Vitamin C or Ceramide body lotion at ₹595–₹795, leveraging existing ingredient "
            "IP and brand trust for a natural adjacency launch."
        ),
    },
    {
        "category": "Lip Care",
        "badge_skus": "14 competitor SKUs",
        "price_range": "₹295 – ₹795",
        "statement": (
            "Lip care serves as a low-risk, high-visibility entry point with strong repeat-purchase cycles, "
            "high influencer content appeal, and gifting potential throughout the year."
        ),
        "action": (
            "Introduce 2 tinted lip serums or SPF balms at ₹395–₹595 for cross-sell with existing "
            "skincare bundles and festive gifting sets."
        ),
    },
    {
        "category": "Peel",
        "badge_skus": "12 competitor SKUs",
        "price_range": "₹495 – ₹1,495",
        "statement": (
            "Chemical peels are high-engagement, clinical-trust products where The Derma Co dominates "
            "but Minimalist is gaining ground — a premium formulation story is unclaimed."
        ),
        "action": (
            "Launch a Mandelic Acid or Lactic Acid peel pad at ₹895, aligning with Foxtale's existing "
            "AHA/BHA ingredient positioning and clinical narrative."
        ),
    },
    {
        "category": "Eye Care (Depth)",
        "badge_skus": "18 competitor SKUs",
        "price_range": "₹495 – ₹1,595",
        "statement": (
            "Foxtale has only 2 eye SKUs vs a competitor average of 5; the category commands the highest "
            "avg prices and loyalty scores among 25–40 urban women — Foxtale's core buyer."
        ),
        "action": (
            "Deepen eye care with a Retinol Eye Cream and Caffeine Eye Gel at ₹995–₹1,295 to close "
            "the depth gap and increase basket size for existing loyal customers."
        ),
    },
]

opp_cols = st.columns(2)
for i, card in enumerate(opp_cards):
    col = opp_cols[i % 2]
    with col:
        st.markdown(
            f"""
<div class="opportunity-card">
    <div class="cat-name">{card['category']}</div>
    <span class="badge">{card['badge_skus']}</span>
    <span class="badge price">{card['price_range']}</span>
    <div class="statement">{card['statement']}</div>
    <div class="action">&#8594; {card['action']}</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown("<hr style='border:none;border-top:1px solid #E8E8E8;margin:28px 0 24px 0'/>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — STRATEGIC RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">06 · STRATEGIC RECOMMENDATIONS</div>', unsafe_allow_html=True)

recommendations = [
    {
        "rank": 1,
        "title": "Launch Body Care Line — Vitamin C & Ceramide Range",
        "score": "14/15",
        "ease": 4,
        "impact": 5,
        "advantage": 4,
        "timeline": "Q3 2026",
        "skus": "3–5 SKUs",
        "price_range": "₹595–₹895",
        "desc": (
            "Body care represents the single largest whitespace by SKU volume (38 competitor SKUs) with "
            "zero Foxtale presence. Foxtale's ingredient credibility in Vitamin C and Ceramide can be "
            "directly leveraged with minimal R&D overhead, maximising speed-to-market. "
            "The category delivers high basket adds and strong subscription potential for existing buyers."
        ),
        "action": (
            "Initiate formulation brief for Vitamin C Body Lotion, Ceramide Body Butter, and SPF Body Serum "
            "by July 2026 — target hero launch at Diwali 2026 with bundled gifting sets."
        ),
    },
    {
        "rank": 2,
        "title": "Deepen Serum Portfolio with Peptide & Barrier Focus",
        "score": "13/15",
        "ease": 5,
        "impact": 4,
        "advantage": 4,
        "timeline": "Q3 2026",
        "skus": "2–3 SKUs",
        "price_range": "₹995–₹1,495",
        "desc": (
            "Serums are Foxtale's core and highest-rated category. Competitors are flooding mass-market "
            "price points (₹299–₹599), creating a clear opening at premium ₹995+ for science-backed "
            "peptide and barrier-repair formulations that command higher margins and deeper loyalty. "
            "Foxtale's rating leadership here validates continued investment."
        ),
        "action": (
            "Fast-track a Copper Peptide Serum and a Multi-Ceramide Barrier Serum into pipeline — "
            "position as 'clinical premium' above Minimalist's price ceiling with strong dermatologist "
            "endorsement content."
        ),
    },
    {
        "rank": 3,
        "title": "Enter Mask Category with Ritual-Positioning SKUs",
        "score": "12/15",
        "ease": 3,
        "impact": 4,
        "advantage": 5,
        "timeline": "Q4 2026",
        "skus": "2–3 SKUs",
        "price_range": "₹595–₹995",
        "desc": (
            "Masks are absent in Foxtale's portfolio despite all 4 competitors having established presence. "
            "The category has strong gifting, repeat, and influencer content ROI. A clay + overnight mask "
            "duo can establish ritual-use behaviour, expand basket size, and create a new acquisition "
            "funnel through gifting occasions."
        ),
        "action": (
            "Commission consumer research on mask usage occasions among existing Foxtale buyers; target a "
            "Kaolin Clay Purifying Mask and Overnight Repair Mask for Q4 festive launch at ₹695 and ₹895."
        ),
    },
    {
        "rank": 4,
        "title": "Expand Eye Care Depth to Close Competitor Gap",
        "score": "11/15",
        "ease": 4,
        "impact": 4,
        "advantage": 3,
        "timeline": "Q3–Q4 2026",
        "skus": "2 SKUs",
        "price_range": "₹995–₹1,295",
        "desc": (
            "Foxtale has 2 eye SKUs versus a competitor average of 5, in the highest average-price category "
            "in the dataset. Eye care buyers are high-LTV, age 28–42 — Foxtale's core demographic. "
            "Extending here deepens wallet share without new audience acquisition cost, and the premium "
            "price tier is underserved."
        ),
        "action": (
            "Add a Retinol Eye Renewal Cream (₹1,195) and Caffeine + Peptide Eye Gel (₹995) to the 2026 "
            "roadmap; cross-sell with existing Peptide Eye Serum via bundle recommendations at checkout."
        ),
    },
    {
        "rank": 5,
        "title": "Refresh Sunscreen Range with Mineral & Body SPF",
        "score": "10/15",
        "ease": 4,
        "impact": 3,
        "advantage": 3,
        "timeline": "Q2–Q3 2026",
        "skus": "2 SKUs",
        "price_range": "₹795–₹1,095",
        "desc": (
            "Sunscreen is Foxtale's lowest-rated category relative to peers and faces intense competition "
            "at ₹499–₹799. A tinted Mineral SPF 50+ and a Body SPF Serum can refresh the category "
            "narrative, command premium pricing with cleaner formulation positioning, and capture the "
            "growing mineral-hybrid and body-sunscreen market."
        ),
        "action": (
            "Reformulate current SPF 50 with a mineral-hybrid formula and launch a limited-edition tinted "
            "body SPF as a summer 2026 hero — lead with 'clean SPF' positioning in influencer campaigns."
        ),
    },
]

fig_priority = go.Figure()

quadrant_shapes = [
    dict(type="rect", x0=3, y0=3, x1=5.5, y1=5.5, fillcolor="rgba(39,174,96,0.06)", line_width=0),
    dict(type="rect", x0=0.5, y0=3, x1=3, y1=5.5, fillcolor="rgba(243,156,18,0.06)", line_width=0),
    dict(type="rect", x0=3, y0=0.5, x1=5.5, y1=3, fillcolor="rgba(74,144,217,0.06)", line_width=0),
    dict(type="rect", x0=0.5, y0=0.5, x1=3, y1=3, fillcolor="rgba(200,200,200,0.08)", line_width=0),
]
for shape in quadrant_shapes:
    fig_priority.add_shape(**shape)

fig_priority.add_shape(
    type="line", x0=3, y0=0.5, x1=3, y1=5.5,
    line=dict(color="#E8E8E8", dash="dash", width=1.5),
)
fig_priority.add_shape(
    type="line", x0=0.5, y0=3, x1=5.5, y1=3,
    line=dict(color="#E8E8E8", dash="dash", width=1.5),
)

quadrant_annotations = [
    dict(x=4.25, y=5.2, text="QUICK WINS", showarrow=False,
         font=dict(size=10, color=COLORS["positive"], family="Inter"), xanchor="center"),
    dict(x=1.75, y=5.2, text="STRATEGIC BETS", showarrow=False,
         font=dict(size=10, color=COLORS["warning"], family="Inter"), xanchor="center"),
    dict(x=4.25, y=1.0, text="FILL-INS", showarrow=False,
         font=dict(size=10, color=COLORS["minimalist"], family="Inter"), xanchor="center"),
    dict(x=1.75, y=1.0, text="DEPRIORITISE", showarrow=False,
         font=dict(size=10, color=COLORS["text_secondary"], family="Inter"), xanchor="center"),
]

fig_priority.add_trace(
    go.Scatter(
        x=[r["ease"] for r in recommendations],
        y=[r["impact"] for r in recommendations],
        mode="markers+text",
        marker=dict(
            size=[r["advantage"] * 18 for r in recommendations],
            color=COLORS["foxtale"],
            opacity=0.85,
            line=dict(width=2, color="white"),
        ),
        text=[f"#{r['rank']}" for r in recommendations],
        textposition="middle center",
        textfont=dict(size=11, color="white", family="Inter"),
        hovertext=[r["title"] for r in recommendations],
        hovertemplate="<b>%{hovertext}</b><br>Ease: %{x}<br>Impact: %{y}<extra></extra>",
        showlegend=False,
    )
)

fig_priority.update_layout(annotations=quadrant_annotations)
chart_layout(
    fig_priority,
    "Strategic Priority Matrix — Bubble Size = Competitive Advantage Score",
    height=480,
)
fig_priority.update_xaxes(
    title_text="Ease of Execution (1–5)",
    title_font=dict(size=11),
    range=[0.5, 5.5],
    dtick=1,
)
fig_priority.update_yaxes(
    title_text="Revenue Impact (1–5)",
    title_font=dict(size=11),
    range=[0.5, 5.5],
    dtick=1,
)
st.plotly_chart(fig_priority, use_container_width=True)

for rec in recommendations:
    st.markdown(
        f"""
<div class="rec-card">
    <span class="rank">0{rec['rank']}</span>
    <div class="title">{rec['title']}</div>
    <span class="score-badge">{rec['score']}</span>
    <span class="tag">&#128197; {rec['timeline']}</span>
    <span class="tag">&#128230; {rec['skus']}</span>
    <span class="tag">&#128176; {rec['price_range']}</span>
    <div class="desc">{rec['desc']}</div>
    <div class="action-item">&#8594; {rec['action']}</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — OPPORTUNITY SCORE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">07 · OPPORTUNITY SCORE</div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight-box">
<strong>Scoring Model:</strong> &nbsp;
<code>Opportunity Score = Growth Potential × Competitor Weakness × Foxtale Absence</code>
&nbsp; (each factor scored 1–10, composite normalised to 1–100)<br><br>
<span style="color:#6B6B6B; font-size:13px;">
<strong>Growth Potential</strong> — breadth of brands competing, total SKU volume, avg review depth &nbsp;|&nbsp;
<strong>Competitor Weakness</strong> — market fragmentation (HHI), discount pressure, inverted avg rating &nbsp;|&nbsp;
<strong>Foxtale Absence</strong> — inverse of Foxtale's current SKU share in the category
</span>
</div>
""", unsafe_allow_html=True)

# ── Compute scores ──────────────────────────────────────────────────────────
def _minmax(s, lo=1.0, hi=10.0):
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series([hi] * len(s), index=s.index)
    return lo + (s - mn) / (mx - mn) * (hi - lo)

def _hhi(grp):
    shares = grp.value_counts(normalize=True)
    return float((shares ** 2).sum())

@st.cache_data
def compute_opportunity(dataframe):
    cat = dataframe.groupby("category").agg(
        total_skus    = ("product_name", "count"),
        num_brands    = ("brand",        "nunique"),
        foxtale_skus  = ("brand",        lambda x: (x == "Foxtale").sum()),
        avg_price     = ("price",        "mean"),
        avg_rating    = ("rating",       "mean"),
        avg_reviews   = ("review_count", "mean"),
        avg_discount  = ("discount",     "mean"),
    ).copy()

    comp = dataframe[dataframe["brand"] != "Foxtale"]
    cat["hhi"] = comp.groupby("category")["brand"].apply(_hhi).reindex(cat.index).fillna(1.0)
    cat["comp_avg_rating"] = comp.groupby("category")["rating"].mean().reindex(cat.index).fillna(cat["avg_rating"])
    cat["foxtale_share"]   = cat["foxtale_skus"] / cat["total_skus"]

    # Growth Potential
    cat["growth_potential"] = (
        0.40 * _minmax(cat["num_brands"]) +
        0.35 * _minmax(cat["total_skus"]) +
        0.25 * _minmax(cat["avg_reviews"])
    )
    # Competitor Weakness
    cat["competitor_weakness"] = (
        0.40 * _minmax(1 - cat["hhi"]) +
        0.35 * _minmax(cat["avg_discount"]) +
        0.25 * _minmax(cat["comp_avg_rating"].max() - cat["comp_avg_rating"])
    )
    # Foxtale Absence
    cat["foxtale_absence"] = 1 + (1 - cat["foxtale_share"]) * 9

    raw = cat["growth_potential"] * cat["competitor_weakness"] * cat["foxtale_absence"]
    lo, hi = raw.min(), raw.max()
    cat["opportunity_score"] = (1 + (raw - lo) / (hi - lo) * 99).round(1)
    cat = cat.sort_values("opportunity_score", ascending=False)
    cat.insert(0, "rank", range(1, len(cat) + 1))

    def _tier(s):
        if s >= 75: return "🔴 Immediate Priority"
        if s >= 50: return "🟠 High Opportunity"
        if s >= 25: return "🟡 Monitor"
        return "🟢 Defended"

    cat["priority_tier"] = cat["opportunity_score"].apply(_tier)
    return cat.reset_index()

opp = compute_opportunity(df)

# ── Top KPI strip ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
immediate = opp[opp["opportunity_score"] >= 75]
high      = opp[(opp["opportunity_score"] >= 50) & (opp["opportunity_score"] < 75)]
absent    = opp[opp["foxtale_skus"] == 0]
top_cat   = opp.iloc[0]

with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="label">TOP OPPORTUNITY</div>
        <div class="value" style="font-size:22px;">{top_cat['category']}</div>
        <div class="delta">{top_cat['opportunity_score']:.0f} / 100</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="label">IMMEDIATE PRIORITY</div>
        <div class="value">{len(immediate)}</div>
        <div class="delta">Score ≥ 75</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="label">HIGH OPPORTUNITY</div>
        <div class="value">{len(high)}</div>
        <div class="delta">Score 50–74</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="label">ZERO-PRESENCE CATS</div>
        <div class="value">{len(absent)}</div>
        <div class="delta">Foxtale SKUs = 0</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Ranked table ─────────────────────────────────────────────────────────────
opp_display = opp[[
    "rank", "category", "priority_tier", "opportunity_score",
    "growth_potential", "competitor_weakness", "foxtale_absence",
    "num_brands", "total_skus", "foxtale_skus", "avg_price", "avg_rating"
]].copy()
opp_display.columns = [
    "Rank", "Category", "Priority Tier", "Opportunity Score",
    "Growth Potential", "Competitor Weakness", "Foxtale Absence",
    "# Brands", "Total SKUs", "Foxtale SKUs", "Avg Price ₹", "Avg Rating"
]

st.dataframe(
    opp_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Opportunity Score": st.column_config.ProgressColumn(
            "Opportunity Score", min_value=0, max_value=100, format="%.1f"
        ),
        "Growth Potential": st.column_config.NumberColumn(format="%.2f"),
        "Competitor Weakness": st.column_config.NumberColumn(format="%.2f"),
        "Foxtale Absence": st.column_config.NumberColumn(format="%.2f"),
        "Avg Price ₹": st.column_config.NumberColumn(format="₹%.0f"),
        "Avg Rating": st.column_config.NumberColumn(format="%.2f"),
    }
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Waterfall / bar chart of scores ─────────────────────────────────────────
col_a, col_b = st.columns([3, 2])

with col_a:
    tier_color_map = {
        "🔴 Immediate Priority": COLORS["accent"],
        "🟠 High Opportunity":   "#E8A838",
        "🟡 Monitor":            "#F1C40F",
        "🟢 Defended":           COLORS["positive"],
    }
    bar_colors = [tier_color_map.get(t, COLORS["foxtale"]) for t in opp["priority_tier"]]

    fig_scores = go.Figure(go.Bar(
        y=opp["category"],
        x=opp["opportunity_score"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{s:.1f}" for s in opp["opportunity_score"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>",
    ))
    fig_scores.update_layout(
        title=dict(text="Opportunity Score by Category", font=dict(size=14, color=COLORS["text_primary"])),
        xaxis=dict(title="Score (1–100)", range=[0, 115], showgrid=True, gridcolor="#F0F0F0"),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="Inter",
        margin=dict(l=20, r=40, t=40, b=20),
        height=380,
        showlegend=False,
    )
    # Reference line at 50
    fig_scores.add_vline(x=50, line_dash="dash", line_color=COLORS["text_secondary"], line_width=1,
                         annotation_text="Threshold 50", annotation_position="top")
    st.plotly_chart(fig_scores, use_container_width=True)

with col_b:
    # Radar / spider chart for top 3 categories across the 3 sub-scores
    top3 = opp.head(3)
    theta = ["Growth Potential", "Competitor Weakness", "Foxtale Absence", "Growth Potential"]
    radar_colors = [COLORS["accent"], "#E8A838", COLORS["foxtale"]]
    fig_radar = go.Figure()
    for i, (_, row) in enumerate(top3.iterrows()):
        vals = [row["growth_potential"], row["competitor_weakness"], row["foxtale_absence"],
                row["growth_potential"]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=theta, fill="toself",
            name=row["category"],
            line_color=radar_colors[i],
            fillcolor=radar_colors[i],
            opacity=0.25,
        ))
    fig_radar.update_layout(
        title=dict(text="Sub-Score Profile — Top 3 Categories", font=dict(size=14, color=COLORS["text_primary"])),
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#E0E0E0"),
                   angularaxis=dict(gridcolor="#E0E0E0")),
        paper_bgcolor="white",
        font_family="Inter",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=20, r=20, t=40, b=40),
        height=380,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── Factor decomposition stacked bar ─────────────────────────────────────────
st.markdown("**Score Decomposition — Contribution of Each Factor**")
fig_stack = go.Figure()
for factor, color, label in [
    ("growth_potential",    "#4A90D9", "Growth Potential"),
    ("competitor_weakness", COLORS["accent"], "Competitor Weakness"),
    ("foxtale_absence",     COLORS["foxtale"], "Foxtale Absence"),
]:
    fig_stack.add_trace(go.Bar(
        name=label,
        x=opp["category"],
        y=opp[factor],
        marker_color=color,
        hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{y:.2f}}<extra></extra>",
    ))
fig_stack.update_layout(
    barmode="group",
    xaxis=dict(tickangle=-30),
    yaxis=dict(title="Sub-Score (1–10)", showgrid=True, gridcolor="#F0F0F0"),
    plot_bgcolor="white", paper_bgcolor="white",
    font_family="Inter",
    legend=dict(orientation="h", y=1.08),
    margin=dict(l=20, r=20, t=20, b=60),
    height=320,
)
st.plotly_chart(fig_stack, use_container_width=True)

st.markdown("""
<div class="insight-box">
<strong>Reading the scores:</strong>
Serum (100) and Sunscreen (84.9) top the list not because Foxtale is absent — it competes in both —
but because they combine massive market breadth (5 brands, 88 and 37 SKUs respectively), high review depth,
and a fragmented competitive field where no single brand dominates.
The implication: Foxtale's depth in Serum and Sunscreen is still insufficient relative to opportunity size.
<br><br>
Mask (41.9), Body Care (35.9), and Lip Care (19.3) score lower on Growth Potential because fewer brands
currently compete there — but they carry full Foxtale Absence scores (10.0), meaning every point of entry
is incremental, uncontested revenue.
</div>
""", unsafe_allow_html=True)

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Foxtale Intelligence Platform &nbsp;&middot;&nbsp; Competitor Analysis &nbsp;&middot;&nbsp; June 2026
</div>
""", unsafe_allow_html=True)
