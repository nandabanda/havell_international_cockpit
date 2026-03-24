import os
import random
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from core.nav_shell import render_premium_nav

OUT = "out"
os.makedirs(OUT, exist_ok=True)

render_premium_nav()


# =========================================================
# Styling
# =========================================================
def add_page_css():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 1.2rem;
            max-width: 96rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,244,236,0.96));
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 18px;
            padding: 12px 14px 10px 14px;
            box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        }

        .hero-shell {
            background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(244,239,230,0.97));
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 24px;
            padding: 20px 22px 18px 22px;
            box-shadow: 0 14px 32px rgba(15,23,42,0.06);
            margin-bottom: 14px;
        }

        .hero-kicker {
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: #64748b;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .hero-title {
            font-size: 1.75rem;
            font-weight: 850;
            color: #0f172a;
            margin-bottom: 6px;
            line-height: 1.15;
        }

        .hero-sub {
            color: #475569;
            font-size: 0.98rem;
            line-height: 1.45rem;
            max-width: 1000px;
        }

        .app-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,244,236,0.96));
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 22px;
            padding: 16px 18px;
            box-shadow: 0 12px 28px rgba(15,23,42,0.05);
        }

        .app-card-tight {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 12px 14px;
        }

        .section-kicker {
            font-size: 0.77rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: #64748b;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .section-title {
            font-size: 1.18rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
        }

        .section-sub {
            color: #475569;
            font-size: 0.9rem;
            margin-bottom: 8px;
        }

        .signal-chip {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-right: 8px;
            margin-bottom: 6px;
            border: 1px solid rgba(15,23,42,0.08);
            background: rgba(255,255,255,0.72);
            color: #0f172a;
        }

        .exception-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 12px 12px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.72);
        }

        .exception-title {
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
            font-size: 0.98rem;
        }

        .exception-meta {
            color: #64748b;
            font-size: 0.83rem;
            margin-bottom: 6px;
        }

        .exception-body {
            color: #334155;
            font-size: 0.9rem;
            line-height: 1.35rem;
        }

        .action-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 18px;
            padding: 14px;
            background: rgba(255,255,255,0.72);
            min-height: 220px;
        }

        .action-title {
            font-size: 1rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 8px;
        }

        .small-note {
            font-size: 0.82rem;
            color: #64748b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Helpers
# =========================================================
def fmt_money(x):
    try:
        return f"{float(x):,.1f}"
    except Exception:
        return "0.0"


def fmt_pct(x):
    try:
        return f"{float(x):.1f}%"
    except Exception:
        return "0.0%"


def confidence_band(score):
    if score >= 88:
        return "High"
    if score >= 76:
        return "Medium"
    return "Watch"


def create_mock_revenue_df():
    rows = [
        ["ACC-001", "L&T Construction", "UAE", "Projects", 18.2, 14.6, 8.4, 22.4, 4.9, 2.0, 79.8, 83.5, 86],
        ["ACC-002", "Tata Projects", "India", "Industrial", 22.8, 18.7, 10.5, 18.1, 3.8, 1.7, 82.0, 85.0, 91],
        ["ACC-003", "Adani Infra", "India", "Infrastructure", 26.5, 21.9, 12.2, 17.4, 4.1, 1.9, 80.2, 84.8, 92],
        ["ACC-004", "Jakson Solar", "India", "Energy", 14.2, 11.1, 6.4, 21.8, 5.4, 2.5, 78.4, 82.6, 87],
        ["ACC-005", "Shapoorji Pallonji", "Saudi Arabia", "Real Estate", 17.9, 14.1, 7.7, 21.2, 4.8, 2.3, 79.1, 83.2, 85],
        ["ACC-006", "Gov Infra Board", "UAE", "Public Sector", 19.8, 15.8, 8.2, 20.0, 4.3, 2.1, 80.8, 84.0, 84],
        ["ACC-007", "Large Real Estate Group", "Saudi Arabia", "Real Estate", 15.6, 12.5, 6.8, 19.9, 4.6, 2.0, 81.2, 83.8, 82],
        ["ACC-008", "OEM Partner Cluster", "Indonesia", "Industrial", 11.8, 9.4, 5.1, 20.3, 4.9, 2.2, 77.3, 81.6, 80],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "account_id", "account", "market", "segment",
            "gross_revenue_musd", "net_revenue_musd", "gross_margin_musd",
            "discount_pct", "trade_spend_pct", "rebate_pct",
            "realized_price_index", "target_price_index", "ai_score"
        ]
    )
    df["gm_pct"] = (df["gross_margin_musd"] / df["net_revenue_musd"] * 100).round(1)
    df["corridor_gap"] = (df["realized_price_index"] - df["target_price_index"]).round(1)
    df["confidence"] = df["ai_score"].apply(confidence_band)
    df["status"] = np.where(df["corridor_gap"] < -2.0, "Price Risk", np.where(df["discount_pct"] > 21.0, "Spend Watch", "Healthy"))
    df["owner"] = np.random.choice(["Revenue Lead", "Key Accounts", "Institutional Sales", "Commercial Finance"], size=len(df))
    return df


def build_trend_dataset():
    weeks = [f"W{k}" for k in range(1, 13)]
    revenue = np.array([8.2, 8.7, 8.5, 9.1, 9.4, 9.0, 9.6, 10.1, 10.4, 10.2, 10.8, 11.1])
    margin = np.array([2.6, 2.8, 2.7, 3.0, 3.1, 3.0, 3.2, 3.3, 3.5, 3.4, 3.7, 3.8])
    spend = np.array([1.6, 1.7, 1.7, 1.8, 1.9, 1.8, 2.0, 2.0, 2.1, 2.0, 2.2, 2.2])
    return pd.DataFrame({"week": weeks, "Revenue": revenue, "Gross Margin": margin, "Trade Spend": spend})


def build_account_pool(df):
    x = (
        df.groupby(["account", "market"], as_index=False)
        .agg(
            Net_Revenue=("net_revenue_musd", "sum"),
            Gross_Margin=("gross_margin_musd", "sum"),
            GM_Pct=("gm_pct", "mean"),
            Discount_Pct=("discount_pct", "mean"),
            AI_Score=("ai_score", "mean"),
        )
        .sort_values("Net_Revenue", ascending=False)
    )
    return x


def build_corridor_exceptions(df):
    ex = df[(df["corridor_gap"] < -1.5) | (df["discount_pct"] > 21.0) | (df["trade_spend_pct"] > 5.0)].copy()
    ex = ex.sort_values(["ai_score", "net_revenue_musd"], ascending=[False, False])
    return ex


def render_exception_cards(df, top_n=5):
    for _, r in df.head(top_n).iterrows():
        gap_txt = f"{r['corridor_gap']:+.1f}"
        st.markdown(
            f"""
            <div class="exception-card">
                <div class="exception-title">{r["account"]} · {r["market"]}</div>
                <div class="exception-meta">
                    Segment <b>{r["segment"]}</b> · AI Score <b>{int(r["ai_score"])}</b> · Confidence <b>{r["confidence"]}</b> · Status <b>{r["status"]}</b>
                </div>
                <div class="exception-body">
                    <b>Net Revenue:</b> ${fmt_money(r["net_revenue_musd"])}M<br>
                    <b>GM%:</b> {fmt_pct(r["gm_pct"])} · <b>Discount:</b> {fmt_pct(r["discount_pct"])} · <b>Trade Spend:</b> {fmt_pct(r["trade_spend_pct"])}<br>
                    <b>Price Corridor Gap:</b> {gap_txt} points
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def revenue_agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Revenue Agent")
    st.caption("Translate revenue, price and spend signals into commercial actions.")

    if df.empty:
        st.info("No accounts in view.")
    else:
        top = df.sort_values(["net_revenue_musd", "ai_score"], ascending=[False, False]).iloc[0]
        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Largest revenue pool in current view</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    ${fmt_money(top["net_revenue_musd"])}M net revenue · GM {fmt_pct(top["gm_pct"])} · Price gap {top["corridor_gap"]:+.1f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.selectbox(
            "Agent mode",
            ["CEO summary", "Revenue action plan", "Price corridor note", "Commercial finance note"],
            key="rev_agent_mode",
        )

        if st.button("Generate revenue guidance", width="stretch", key="rev_agent_generate"):
            if mode == "CEO summary":
                lines = [
                    f"The strongest account by revenue in the current view is {top['account']} with ${fmt_money(top['net_revenue_musd'])}M net revenue.",
                    "This page monitors realized revenue quality — not just topline, but price realization, discount intensity and gross margin.",
                    "The operating objective is to protect revenue quality while growing institutional business.",
                ]
            elif mode == "Revenue action plan":
                lines = [
                    f"Focus first on {top['account']} because it combines scale with meaningful pricing and spend decisions.",
                    "Review corridor leakage, reduce unstructured discounting and protect high-quality mix.",
                    "Use account-level reviews to move from revenue growth to profitable revenue growth.",
                ]
            elif mode == "Price corridor note":
                lines = [
                    f"{top['account']} is currently showing a corridor gap of {top['corridor_gap']:+.1f} points.",
                    "The immediate priority is to understand whether this is strategic pricing, a mix issue or uncontrolled leakage.",
                    "Do not correct blindly; correct with account context and contract discipline.",
                ]
            else:
                lines = [
                    "Commercial finance should focus on realized price, spend quality and margin protection rather than topline alone.",
                    "The page helps isolate revenue pools where growth is coming with weak price discipline or excessive commercial leakage.",
                    "That allows better approval governance for discounts, rebates and trade investments.",
                ]

            st.markdown("#### Output")
            for line in lines:
                st.write(f"- {line}")

        st.markdown("#### Suggested prompts")
        st.write("- Summarize revenue quality in 3 bullets.")
        st.write("- Which accounts need pricing intervention?")
        st.write("- Where is discount leakage hurting margin?")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "inst_revenue_df" not in st.session_state:
    st.session_state.inst_revenue_df = create_mock_revenue_df()

rev_df = st.session_state.inst_revenue_df.copy()

# =========================================================
# Hero
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Hunting · Institutional Revenue Intelligence</div>
        <div class="hero-title">Revenue Quality Command Layer</div>
        <div class="hero-sub">
            Monitor institutional revenue with sharper control over price realization, discount intensity, trade spend, gross margin and corridor compliance.
            This is where topline gets translated into quality of earnings.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Revenue Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Account and Commercial Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Keep commercial controls inside the page so the left panel remains application navigation only.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.2, 0.9])

with c1:
    market_filter = st.selectbox("Market", ["All"] + sorted(rev_df["market"].unique().tolist()), key="rev_market_filter")
with c2:
    segment_filter = st.selectbox("Segment", ["All"] + sorted(rev_df["segment"].unique().tolist()), key="rev_segment_filter")
with c3:
    status_filter = st.selectbox("Commercial Status", ["All"] + sorted(rev_df["status"].unique().tolist()), key="rev_status_filter")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="rev_refresh")

if market_filter != "All":
    rev_df = rev_df[rev_df["market"] == market_filter]
if segment_filter != "All":
    rev_df = rev_df[rev_df["segment"] == segment_filter]
if status_filter != "All":
    rev_df = rev_df[rev_df["status"] == status_filter]

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Revenue Realization</span>
        <span class="signal-chip">Price Corridor Compliance</span>
        <span class="signal-chip">Discount Discipline</span>
        <span class="signal-chip">Trade Spend Quality</span>
        <span class="signal-chip">Gross Margin Protection</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
gross_revenue = rev_df["gross_revenue_musd"].sum() if not rev_df.empty else 0
net_revenue = rev_df["net_revenue_musd"].sum() if not rev_df.empty else 0
gm_value = rev_df["gross_margin_musd"].sum() if not rev_df.empty else 0
gm_pct = (gm_value / net_revenue * 100) if net_revenue > 0 else 0
avg_discount = rev_df["discount_pct"].mean() if not rev_df.empty else 0
avg_corridor_gap = rev_df["corridor_gap"].mean() if not rev_df.empty else 0
price_risk_accounts = int((rev_df["corridor_gap"] < -1.5).sum()) if not rev_df.empty else 0
spend_watch_accounts = int((rev_df["trade_spend_pct"] > 5.0).sum()) if not rev_df.empty else 0

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
with k1:
    st.metric("Gross Revenue ($M)", fmt_money(gross_revenue))
with k2:
    st.metric("Net Revenue ($M)", fmt_money(net_revenue))
with k3:
    st.metric("Gross Margin ($M)", fmt_money(gm_value))
with k4:
    st.metric("GM %", fmt_pct(gm_pct))
with k5:
    st.metric("Avg Discount", fmt_pct(avg_discount))
with k6:
    st.metric("Avg Corridor Gap", f"{avg_corridor_gap:+.1f}")
with k7:
    st.metric("Price Risk Accounts", price_risk_accounts)
with k8:
    st.metric("Spend Watch Accounts", spend_watch_accounts)

st.markdown("")

# =========================================================
# Main command area
# =========================================================
left, middle, right = st.columns([1.45, 1.1, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Revenue Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Realization and Margin View</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">This turns revenue into an operating signal: how much is realised, how much is leaked, and how margin is behaving.</div>',
        unsafe_allow_html=True,
    )

    trend_df = build_trend_dataset()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Revenue"], mode="lines+markers", name="Revenue"))
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Gross Margin"], mode="lines+markers", name="Gross Margin"))
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Trade Spend"], mode="lines+markers", name="Trade Spend"))
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=45, b=10), title="Weekly Revenue / Margin / Spend Trend")
    st.plotly_chart(fig, width="stretch", key="rev_trend")

    account_pool_df = build_account_pool(rev_df)
    st.dataframe(account_pool_df, width="stretch", height=210, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Account Revenue Pools</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Where Revenue Quality Lives</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Spot the biggest revenue pools and compare them by margin, discount intensity and pricing quality.</div>',
        unsafe_allow_html=True,
    )

    if rev_df.empty:
        st.info("No accounts match the filters.")
    else:
        bubble_df = rev_df.copy()
        fig2 = px.scatter(
            bubble_df,
            x="discount_pct",
            y="gm_pct",
            size="net_revenue_musd",
            color="market",
            hover_name="account",
            title="Discount vs GM% · Bubble = Net Revenue",
        )
        fig2.update_layout(height=350, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig2, width="stretch", key="rev_bubble")

        compare_df = rev_df[["account", "market", "net_revenue_musd", "gm_pct", "discount_pct", "trade_spend_pct", "corridor_gap", "status"]].copy()
        compare_df.columns = ["Account", "Market", "Net Revenue ($M)", "GM %", "Discount %", "Trade Spend %", "Corridor Gap", "Status"]
        st.dataframe(compare_df, width="stretch", height=210, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    revenue_agent_panel(rev_df)

st.markdown("")

# =========================================================
# Exceptions / approvals / selected account
# =========================================================
ex_df = build_corridor_exceptions(rev_df) if not rev_df.empty else pd.DataFrame()

b1, b2, b3 = st.columns([1.15, 1.05, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Commercial Exceptions</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Price / Spend Risk Queue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">These are the accounts leadership should review immediately for price corridor or spend discipline issues.</div>',
        unsafe_allow_html=True,
    )

    if ex_df.empty:
        st.success("No major price or spend exceptions in current view.")
    else:
        render_exception_cards(ex_df, top_n=4)

    st.button("Review exceptions", width="stretch", key="review_rev_exceptions")
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Approval Discipline</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Commercial Approval Queue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A simplified view of where discount / rebate / trade decisions need governance before value leaks further.</div>',
        unsafe_allow_html=True,
    )

    if rev_df.empty:
        st.info("No approval items.")
    else:
        approval_df = rev_df[["account", "market", "discount_pct", "trade_spend_pct", "rebate_pct", "gm_pct", "status", "owner"]].copy()
        approval_df.columns = ["Account", "Market", "Discount %", "Trade Spend %", "Rebate %", "GM %", "Status", "Owner"]
        st.dataframe(approval_df, width="stretch", height=320, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Account Command</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Revenue Pool</div>', unsafe_allow_html=True)

    if rev_df.empty:
        st.info("No account selected.")
    else:
        selected_account = st.selectbox("Account", sorted(rev_df["account"].unique().tolist()), key="selected_rev_account")
        row = rev_df[rev_df["account"] == selected_account].iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight">
                <div class="small-note">Account Snapshot</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{row["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {row["market"]} · {row["segment"]} · Net ${fmt_money(row["net_revenue_musd"])}M · GM {fmt_pct(row["gm_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Current revenue quality")
        st.write(f"- Discount: {fmt_pct(row['discount_pct'])}")
        st.write(f"- Trade Spend: {fmt_pct(row['trade_spend_pct'])}")
        st.write(f"- Rebate: {fmt_pct(row['rebate_pct'])}")
        st.write(f"- Corridor Gap: {row['corridor_gap']:+.1f}")

        st.markdown("#### Recommendation")
        if row["corridor_gap"] < -1.5:
            st.write("- Pricing intervention recommended. Validate mix, negotiated terms and leakage control.")
        elif row["discount_pct"] > 21:
            st.write("- Discount discipline review recommended before further approvals.")
        else:
            st.write("- Account is broadly healthy. Focus on controlled growth and margin protection.")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Bottom action layer
# =========================================================
c1, c2, c3, c4 = st.columns([1, 1, 1, 1.1])

with c1:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Price Realization</div>', unsafe_allow_html=True)
    st.write("- Identify accounts below corridor.")
    st.write("- Understand whether leakage comes from pricing, terms or mix.")
    st.write("- Correct revenue quality before chasing more topline.")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Spend Discipline</div>', unsafe_allow_html=True)
    st.write("- Review discount and trade spend intensity account by account.")
    st.write("- Push approvals through governance, not ad hoc exceptions.")
    st.write("- Protect contribution before approving incremental spend.")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Margin Protection</div>', unsafe_allow_html=True)
    st.write("- Track where growth is high but margin quality is weak.")
    st.write("- Prioritise high-value revenue pools for GM protection.")
    st.write("- Use this page as a commercial finance operating bridge.")
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### Approval Note Generator")
    st.caption("Generate a short commercial note for a pricing / spend review.")

    account_name = st.text_input("Account", rev_df.iloc[0]["account"] if not rev_df.empty else "ABC Account", key="rev_note_account")
    note = f"""Subject: Commercial review for {account_name}

This account should be reviewed for revenue quality, including realized pricing, discount intensity, trade spend and gross margin protection.

Recommended next step:
1. Validate corridor compliance
2. Review discount / rebate rationale
3. Confirm expected margin outcome before approval
"""
    st.text_area("Generated note", note, height=220, key="rev_generated_note")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Demo tip: show this page after Business Development Studio to prove that pipeline quality is being translated into commercial revenue quality and margin discipline.")