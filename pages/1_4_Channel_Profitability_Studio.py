import os
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

        .profit-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 12px 12px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.72);
        }

        .profit-title {
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
            font-size: 0.98rem;
        }

        .profit-meta {
            color: #64748b;
            font-size: 0.83rem;
            margin-bottom: 6px;
        }

        .profit-body {
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


def create_profitability_df():
    rows = [
        ["CH-001", "Al Futtaim Projects", "UAE", "Lighting", "Institutional", 18.4, 13.8, 4.6, 24.9, 5.6, 2.2, 88],
        ["CH-002", "Tata Projects", "India", "Switchgear", "EPC", 24.2, 18.3, 6.4, 26.2, 4.4, 1.8, 91],
        ["CH-003", "Adani Infra", "India", "Cables", "Infrastructure", 27.1, 21.2, 7.0, 25.8, 4.8, 2.0, 92],
        ["CH-004", "Jakson Solar", "India", "Solar Electricals", "Energy", 15.8, 12.0, 3.9, 24.7, 5.1, 2.4, 86],
        ["CH-005", "Shapoorji Pallonji", "Saudi Arabia", "Lighting", "Real Estate", 17.2, 13.1, 4.0, 23.0, 5.4, 2.1, 84],
        ["CH-006", "Gov Infra Board", "UAE", "Industrial Controls", "Public Sector", 19.1, 14.7, 4.5, 23.6, 5.0, 2.0, 83],
        ["CH-007", "Large Real Estate Group", "Saudi Arabia", "Wiring Devices", "Real Estate", 14.6, 11.0, 3.2, 21.9, 5.8, 2.6, 80],
        ["CH-008", "OEM Partner Cluster", "Indonesia", "Low Voltage", "OEM", 12.7, 9.4, 2.7, 21.3, 5.1, 2.3, 79],
        ["CH-009", "Regional Contractor Group", "Vietnam", "Cables", "Projects", 10.8, 8.0, 2.2, 20.4, 5.6, 2.7, 78],
        ["CH-010", "Smart Infra Consortium", "Singapore", "Automation", "Industrial", 16.2, 12.5, 4.1, 25.3, 4.2, 1.7, 89],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "channel_id", "partner", "market", "category", "channel_type",
            "gross_revenue_musd", "net_revenue_musd", "gross_margin_musd",
            "gm_pct", "trade_spend_pct", "service_cost_pct", "ai_score"
        ],
    )
    df["profit_musd"] = (
        df["gross_margin_musd"]
        - (df["net_revenue_musd"] * df["trade_spend_pct"] / 100)
        - (df["net_revenue_musd"] * df["service_cost_pct"] / 100)
    ).round(2)
    df["profit_pct"] = (df["profit_musd"] / df["net_revenue_musd"] * 100).round(1)
    df["discount_leakage_pct"] = np.round(np.random.uniform(1.2, 4.8, len(df)), 1)
    df["mix_quality_pct"] = np.round(np.random.uniform(72, 93, len(df)), 1)
    df["price_realization_pct"] = np.round(np.random.uniform(78, 94, len(df)), 1)
    df["confidence"] = df["ai_score"].apply(confidence_band)
    df["status"] = np.where(
        df["profit_pct"] < 15,
        "Profit Risk",
        np.where(df["trade_spend_pct"] > 5.4, "Spend Watch", "Healthy"),
    )
    df["owner"] = np.random.choice(
        ["Channel Lead", "Commercial Finance", "Institutional Sales", "Profitability Manager"],
        size=len(df),
    )
    return df


def build_profit_trend():
    weeks = [f"W{k}" for k in range(1, 13)]
    revenue = np.array([9.2, 9.4, 9.8, 10.1, 10.5, 10.3, 10.7, 11.1, 11.3, 11.5, 11.9, 12.2])
    margin = np.array([2.9, 3.0, 3.1, 3.3, 3.4, 3.3, 3.5, 3.7, 3.8, 3.9, 4.0, 4.2])
    profit = np.array([1.4, 1.5, 1.6, 1.7, 1.8, 1.7, 1.9, 2.0, 2.0, 2.1, 2.2, 2.3])
    return pd.DataFrame({"week": weeks, "Revenue": revenue, "Gross Margin": margin, "Profit": profit})


def build_channel_view(df):
    return (
        df.groupby(["channel_type"], as_index=False)
        .agg(
            Net_Revenue=("net_revenue_musd", "sum"),
            Gross_Margin=("gross_margin_musd", "sum"),
            Profit=("profit_musd", "sum"),
            Profit_Pct=("profit_pct", "mean"),
        )
        .sort_values("Profit", ascending=False)
    )


def build_partner_view(df):
    return (
        df.groupby(["partner", "market"], as_index=False)
        .agg(
            Net_Revenue=("net_revenue_musd", "sum"),
            Gross_Margin=("gross_margin_musd", "sum"),
            Profit=("profit_musd", "sum"),
            Profit_Pct=("profit_pct", "mean"),
            Trade_Spend=("trade_spend_pct", "mean"),
            Service_Cost=("service_cost_pct", "mean"),
            AI_Score=("ai_score", "mean"),
        )
        .sort_values("Profit", ascending=False)
    )


def build_profit_bridge(row):
    net_rev = float(row["net_revenue_musd"])
    gm = float(row["gross_margin_musd"])
    trade = net_rev * float(row["trade_spend_pct"]) / 100
    service = net_rev * float(row["service_cost_pct"]) / 100
    leakage = net_rev * float(row["discount_leakage_pct"]) / 100
    profit = float(row["profit_musd"])

    bridge = pd.DataFrame(
        {
            "Step": [
                "Net Revenue",
                "Gross Margin",
                "Trade Spend",
                "Service Cost",
                "Leakage",
                "Profit",
            ],
            "Value": [
                net_rev,
                gm,
                -trade,
                -service,
                -leakage,
                profit,
            ],
        }
    )
    return bridge


def build_risk_queue(df):
    q = df[(df["status"] != "Healthy") | (df["profit_pct"] < 15.5)].copy()
    q = q.sort_values(["ai_score", "profit_musd"], ascending=[False, False])
    return q


def render_profit_cards(df, top_n=5):
    for _, r in df.head(top_n).iterrows():
        st.markdown(
            f"""
            <div class="profit-card">
                <div class="profit-title">{r["partner"]} · {r["category"]}</div>
                <div class="profit-meta">
                    {r["market"]} · {r["channel_type"]} · AI <b>{int(r["ai_score"])}</b> · Confidence <b>{r["confidence"]}</b> · Status <b>{r["status"]}</b>
                </div>
                <div class="profit-body">
                    <b>Net Revenue:</b> ${fmt_money(r["net_revenue_musd"])}M ·
                    <b>GM:</b> ${fmt_money(r["gross_margin_musd"])}M ·
                    <b>Profit:</b> ${fmt_money(r["profit_musd"])}M<br>
                    <b>Profit %:</b> {fmt_pct(r["profit_pct"])} ·
                    <b>Trade Spend:</b> {fmt_pct(r["trade_spend_pct"])} ·
                    <b>Service Cost:</b> {fmt_pct(r["service_cost_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def profitability_agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Profitability Agent")
    st.caption("Turn channel economics into commercial actions and recovery decisions.")

    if df.empty:
        st.info("No partners in current view.")
    else:
        top = df.sort_values(["profit_musd", "ai_score"], ascending=[False, False]).iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Highest profit pool in current view</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["partner"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    ${fmt_money(top["profit_musd"])}M profit · {top["market"]} · {top["channel_type"]} · Profit {fmt_pct(top["profit_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.selectbox(
            "Agent mode",
            ["CEO summary", "Profit recovery plan", "Channel economics note", "Partner review note"],
            key="profit_agent_mode",
        )

        if st.button("Generate profitability guidance", width="stretch", key="profit_agent_generate"):
            if mode == "CEO summary":
                lines = [
                    f"The strongest current profit pool is {top['partner']} with ${fmt_money(top['profit_musd'])}M profit contribution.",
                    "This page shows where revenue becomes profit, and where spend, service or leakage are eroding channel returns.",
                    "The goal is to manage channel growth with profitability discipline, not topline alone.",
                ]
            elif mode == "Profit recovery plan":
                lines = [
                    f"Prioritize a profitability review for partners showing low profit %, high spend or poor price realization.",
                    "Recover profit through trade spend discipline, leakage control and better mix-quality decisions.",
                    "Use the risk queue to focus only on partners where intervention will create meaningful value.",
                ]
            elif mode == "Channel economics note":
                lines = [
                    "Channel economics should be reviewed through revenue, gross margin, spend, service cost and final profit.",
                    "The page makes it easy to compare channel types and partner pools side by side.",
                    "This supports more disciplined commercial investment and partner prioritisation.",
                ]
            else:
                lines = [
                    f"{top['partner']} is currently one of the most attractive profit pools in the view.",
                    "The next review should validate sustainability of profit after spend, service and leakage factors.",
                    "Where needed, shift from volume-seeking behavior to profitable growth governance.",
                ]

            st.markdown("#### Output")
            for line in lines:
                st.write(f"- {line}")

        st.markdown("#### Suggested prompts")
        st.write("- Which partners are most profitable?")
        st.write("- Where are we losing profit through spend or leakage?")
        st.write("- Summarize the channel economics in 3 bullets.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "channel_profit_df" not in st.session_state:
    st.session_state.channel_profit_df = create_profitability_df()

profit_df = st.session_state.channel_profit_df.copy()

# =========================================================
# Hero
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Hunting · Channel Profitability Studio</div>
        <div class="hero-title">Partner Economics Command Layer</div>
        <div class="hero-sub">
            Monitor how partner, category and channel choices translate into profit after trade spend, service cost and leakage.
            This is where commercial growth is evaluated through contribution quality, not revenue alone.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Profitability Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Channel and Partner Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Keep controls inside the page so the left panel remains clean application navigation.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.2, 0.9])

with c1:
    market_filter = st.selectbox("Market", ["All"] + sorted(profit_df["market"].unique().tolist()), key="cp_market_filter")
with c2:
    channel_filter = st.selectbox("Channel Type", ["All"] + sorted(profit_df["channel_type"].unique().tolist()), key="cp_channel_filter")
with c3:
    status_filter = st.selectbox("Profitability Status", ["All"] + sorted(profit_df["status"].unique().tolist()), key="cp_status_filter")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="cp_refresh")

if market_filter != "All":
    profit_df = profit_df[profit_df["market"] == market_filter]
if channel_filter != "All":
    profit_df = profit_df[profit_df["channel_type"] == channel_filter]
if status_filter != "All":
    profit_df = profit_df[profit_df["status"] == status_filter]

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Partner Contribution</span>
        <span class="signal-chip">Profit Pool View</span>
        <span class="signal-chip">Trade Spend Discipline</span>
        <span class="signal-chip">Service Cost Visibility</span>
        <span class="signal-chip">Leakage Recovery</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
gross_revenue = profit_df["gross_revenue_musd"].sum() if not profit_df.empty else 0
net_revenue = profit_df["net_revenue_musd"].sum() if not profit_df.empty else 0
gm_value = profit_df["gross_margin_musd"].sum() if not profit_df.empty else 0
profit_value = profit_df["profit_musd"].sum() if not profit_df.empty else 0
profit_pct = (profit_value / net_revenue * 100) if net_revenue > 0 else 0
avg_trade_spend = profit_df["trade_spend_pct"].mean() if not profit_df.empty else 0
avg_service_cost = profit_df["service_cost_pct"].mean() if not profit_df.empty else 0
risk_partners = int((profit_df["status"] != "Healthy").sum()) if not profit_df.empty else 0

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
with k1:
    st.metric("Gross Revenue ($M)", fmt_money(gross_revenue))
with k2:
    st.metric("Net Revenue ($M)", fmt_money(net_revenue))
with k3:
    st.metric("Gross Margin ($M)", fmt_money(gm_value))
with k4:
    st.metric("Profit ($M)", fmt_money(profit_value))
with k5:
    st.metric("Profit %", fmt_pct(profit_pct))
with k6:
    st.metric("Avg Trade Spend", fmt_pct(avg_trade_spend))
with k7:
    st.metric("Avg Service Cost", fmt_pct(avg_service_cost))
with k8:
    st.metric("Risk Partners", risk_partners)

st.markdown("")

# =========================================================
# Main command area
# =========================================================
left, middle, right = st.columns([1.45, 1.1, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Profit Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Revenue, Margin and Profit Trend</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Retained as a strong visual anchor — this shows whether growth is actually translating into profit.</div>',
        unsafe_allow_html=True,
    )

    trend_df = build_profit_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Revenue"], mode="lines+markers", name="Revenue"))
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Gross Margin"], mode="lines+markers", name="Gross Margin"))
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Profit"], mode="lines+markers", name="Profit"))
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=45, b=10), title="Weekly Revenue / Margin / Profit")
    st.plotly_chart(fig, width="stretch", key="cp_trend")

    channel_view_df = build_channel_view(profit_df)
    st.dataframe(channel_view_df, width="stretch", height=210, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Partner Profit Pools</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Contribution Map</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Retained graphically — this is the visual heart of the page. Bubble = profit pool, axes = spend vs profit quality.</div>',
        unsafe_allow_html=True,
    )

    if profit_df.empty:
        st.info("No partners match the filters.")
    else:
        fig2 = px.scatter(
            profit_df,
            x="trade_spend_pct",
            y="profit_pct",
            size="profit_musd",
            color="market",
            hover_name="partner",
            title="Trade Spend % vs Profit % · Bubble = Profit Pool",
        )
        fig2.update_layout(height=350, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig2, width="stretch", key="cp_bubble")

        partner_view_df = build_partner_view(profit_df)
        st.dataframe(partner_view_df, width="stretch", height=210, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    profitability_agent_panel(profit_df)

st.markdown("")

# =========================================================
# Profit bridge / risk queue / selected partner
# =========================================================
risk_df = build_risk_queue(profit_df) if not profit_df.empty else pd.DataFrame()

b1, b2, b3 = st.columns([1.15, 1.05, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Profit Bridge</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What Builds or Erodes Profit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A waterfall-style explanation of how partner revenue gets translated into profit after commercial and service costs.</div>',
        unsafe_allow_html=True,
    )

    if profit_df.empty:
        st.info("No partner selected.")
    else:
        selected_bridge_partner = st.selectbox(
            "Partner for bridge",
            sorted(profit_df["partner"].unique().tolist()),
            key="selected_bridge_partner",
        )
        row = profit_df[profit_df["partner"] == selected_bridge_partner].iloc[0]
        bridge_df = build_profit_bridge(row)

        fig3 = go.Figure(
            go.Waterfall(
                name="Profit Bridge",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                x=bridge_df["Step"],
                y=bridge_df["Value"],
                connector={"line": {"width": 1}},
            )
        )
        fig3.update_layout(height=360, margin=dict(l=10, r=10, t=45, b=10), title="Partner Profit Bridge")
        st.plotly_chart(fig3, width="stretch", key="cp_bridge")

    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Risk Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Profit Recovery Priorities</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">These are the partners where profit is under pressure and intervention should create the most value.</div>',
        unsafe_allow_html=True,
    )

    if risk_df.empty:
        st.success("No major profitability risks in current view.")
    else:
        render_profit_cards(risk_df, top_n=4)

    st.button("Review recovery queue", width="stretch", key="review_profit_queue")
    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Partner Command</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Partner</div>', unsafe_allow_html=True)

    if profit_df.empty:
        st.info("No partner selected.")
    else:
        selected_partner = st.selectbox(
            "Partner",
            sorted(profit_df["partner"].unique().tolist()),
            key="selected_partner_cp",
        )
        row = profit_df[profit_df["partner"] == selected_partner].iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight">
                <div class="small-note">Partner Snapshot</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{row["partner"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {row["market"]} · {row["category"]} · Profit ${fmt_money(row["profit_musd"])}M · Profit {fmt_pct(row["profit_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Current economics")
        st.write(f"- Net Revenue: ${fmt_money(row['net_revenue_musd'])}M")
        st.write(f"- Trade Spend: {fmt_pct(row['trade_spend_pct'])}")
        st.write(f"- Service Cost: {fmt_pct(row['service_cost_pct'])}")
        st.write(f"- Leakage: {fmt_pct(row['discount_leakage_pct'])}")
        st.write(f"- Mix Quality: {fmt_pct(row['mix_quality_pct'])}")

        st.markdown("#### Recommendation")
        if row["profit_pct"] < 15:
            st.write("- Profit recovery recommended: review spend, leakage and partner economics before pushing more volume.")
        elif row["trade_spend_pct"] > 5.4:
            st.write("- Trade spend discipline review recommended to protect contribution quality.")
        else:
            st.write("- Partner is healthy. Focus on scalable profitable growth.")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Bottom action layer
# =========================================================
c1, c2, c3, c4 = st.columns([1, 1, 1, 1.1])

with c1:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Profit Pool Prioritisation</div>', unsafe_allow_html=True)
    st.write("- Focus on the partners and categories creating the most profit.")
    st.write("- Separate scale from true contribution quality.")
    st.write("- Use the bubble map to drive leadership attention.")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Leakage Recovery</div>', unsafe_allow_html=True)
    st.write("- Identify where discounts, spend or service cost are eroding returns.")
    st.write("- Use the bridge to show exactly what is taking profit away.")
    st.write("- Recover value through targeted commercial correction.")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Channel Economics Governance</div>', unsafe_allow_html=True)
    st.write("- Compare EPC, Institutional, OEM and other channel types.")
    st.write("- Shift discussion from revenue volume to channel quality.")
    st.write("- Use the page as a commercial finance bridge for action.")
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### Partner Review Note")
    st.caption("Generate a short profitability note for partner review.")

    partner_name = st.text_input("Partner", profit_df.iloc[0]["partner"] if not profit_df.empty else "ABC Partner", key="cp_note_partner")
    note = f"""Subject: Profitability review for {partner_name}

This partner should be reviewed for contribution quality across revenue, gross margin, trade spend, service cost and final profit outcome.

Recommended next step:
1. Validate current profit bridge
2. Review spend / leakage / service cost drivers
3. Define correction actions for profitable growth
"""
    st.text_area("Generated note", note, height=220, key="cp_generated_note")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Demo tip: show this page after Supply Orchestration to prove that channel and partner growth is being managed through contribution quality, not just volume.")