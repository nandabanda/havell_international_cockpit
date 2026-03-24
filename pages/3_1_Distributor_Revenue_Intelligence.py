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
            padding-top: 1.05rem;
            padding-bottom: 1.15rem;
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
            font-size: 1.72rem;
            font-weight: 850;
            color: #0f172a;
            margin-bottom: 6px;
            line-height: 1.15;
        }

        .hero-sub {
            color: #475569;
            font-size: 0.98rem;
            line-height: 1.45rem;
            max-width: 980px;
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
            font-size: 1.16rem;
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

        .queue-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 12px 12px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.72);
        }

        .queue-title {
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
            font-size: 0.98rem;
        }

        .queue-meta {
            color: #64748b;
            font-size: 0.83rem;
            margin-bottom: 6px;
        }

        .queue-body {
            color: #334155;
            font-size: 0.9rem;
            line-height: 1.35rem;
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


def create_revenue_df():
    rows = [
        ["DIST-001", "Alpha Distributors", "Saudi Arabia", "Riyadh North", 21.4, 18.1, 4.2, 23.2, 4.6, 1.9, 90],
        ["DIST-002", "Jeddah Trading", "Saudi Arabia", "Jeddah West", 16.9, 14.0, 3.0, 21.5, 5.3, 2.4, 84],
        ["DIST-003", "Dubai Channel House", "UAE", "Dubai Outer", 14.6, 12.4, 3.1, 24.8, 4.1, 1.6, 88],
        ["DIST-004", "Abu Dhabi Supply Co", "UAE", "Abu Dhabi Fringe", 11.2, 9.3, 2.0, 21.1, 5.6, 2.5, 80],
        ["DIST-005", "Jakarta Prime", "Indonesia", "Jakarta East", 22.7, 19.1, 4.9, 25.7, 4.2, 1.8, 91],
        ["DIST-006", "Surabaya Network", "Indonesia", "Surabaya South", 12.8, 10.4, 2.2, 21.2, 5.9, 2.6, 78],
        ["DIST-007", "Ho Chi Minh Trade", "Vietnam", "Ho Chi Minh Periphery", 10.6, 8.6, 1.9, 21.6, 6.0, 2.7, 77],
        ["DIST-008", "Hanoi Market Link", "Vietnam", "Hanoi South", 9.8, 8.0, 1.8, 22.1, 5.5, 2.5, 79],
        ["DIST-009", "Singapore Channel Partners", "Singapore", "Industrial Belt", 7.4, 6.3, 1.8, 28.6, 3.8, 1.3, 89],
        ["DIST-010", "Mumbai Edge Distribution", "India", "Mumbai Peripheral", 24.1, 20.2, 5.2, 25.7, 4.4, 1.7, 92],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "distributor_id", "distributor", "country", "territory",
            "gross_revenue_musd", "net_revenue_musd", "profit_musd",
            "gm_pct", "trade_spend_pct", "rebate_pct", "ai_score"
        ],
    )
    df["realized_price_index"] = np.round(np.random.uniform(79, 95, len(df)), 1)
    df["target_price_index"] = np.round(np.random.uniform(83, 90, len(df)), 1)
    df["price_gap"] = (df["realized_price_index"] - df["target_price_index"]).round(1)
    df["growth_pct"] = np.round(np.random.uniform(9, 24, len(df)), 1)
    df["discount_leakage_pct"] = np.round(np.random.uniform(1.2, 4.9, len(df)), 1)
    df["confidence"] = df["ai_score"].apply(confidence_band)
    df["status"] = np.where(
        df["price_gap"] < -2.0,
        "Price Risk",
        np.where(df["trade_spend_pct"] > 5.4, "Spend Watch", "Healthy"),
    )
    df["owner"] = np.random.choice(
        ["Distributor Manager", "Regional Sales", "Commercial Finance", "RTM Lead"],
        size=len(df),
    )
    return df


def build_trend():
    periods = [f"M{k}" for k in range(1, 13)]
    gross = np.array([9.2, 9.4, 9.7, 10.0, 10.4, 10.6, 10.9, 11.2, 11.5, 11.9, 12.3, 12.7])
    net = np.array([7.7, 7.9, 8.2, 8.5, 8.8, 9.1, 9.3, 9.5, 9.8, 10.1, 10.4, 10.8])
    profit = np.array([1.7, 1.75, 1.86, 1.95, 2.02, 2.10, 2.18, 2.24, 2.30, 2.38, 2.48, 2.60])
    return pd.DataFrame({"period": periods, "Gross Revenue": gross, "Net Revenue": net, "Profit": profit})


def build_country_summary(df):
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby("country", as_index=False)
        .agg(
            Gross_Revenue=("gross_revenue_musd", "sum"),
            Net_Revenue=("net_revenue_musd", "sum"),
            Profit=("profit_musd", "sum"),
            Avg_GM=("gm_pct", "mean"),
        )
        .sort_values("Net_Revenue", ascending=False)
    )


def build_bubble(df):
    return df.copy()


def build_risk_queue(df):
    q = df[(df["status"] != "Healthy") | (df["price_gap"] < -1.5)].copy()
    q = q.sort_values(["ai_score", "net_revenue_musd"], ascending=[False, False])
    return q


def render_queue_cards(df, top_n=4):
    for _, r in df.head(top_n).iterrows():
        st.markdown(
            f"""
            <div class="queue-card">
                <div class="queue-title">{r["distributor"]}</div>
                <div class="queue-meta">
                    {r["country"]} · {r["territory"]} · Status <b>{r["status"]}</b> · AI <b>{int(r["ai_score"])}</b> · Confidence <b>{r["confidence"]}</b>
                </div>
                <div class="queue-body">
                    <b>Gross Revenue:</b> ${fmt_money(r["gross_revenue_musd"])}M ·
                    <b>Net Revenue:</b> ${fmt_money(r["net_revenue_musd"])}M ·
                    <b>Profit:</b> ${fmt_money(r["profit_musd"])}M<br>
                    <b>GM%:</b> {fmt_pct(r["gm_pct"])} ·
                    <b>Trade Spend:</b> {fmt_pct(r["trade_spend_pct"])} ·
                    <b>Price Gap:</b> {r["price_gap"]:+.1f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_action_queue(df):
    rows = []
    for _, r in df.sort_values(["ai_score", "net_revenue_musd"], ascending=[False, False]).head(6).iterrows():
        if r["status"] == "Price Risk":
            action = "Review price realization and corridor leakage"
        elif r["status"] == "Spend Watch":
            action = "Tighten trade spend and rebate approvals"
        elif r["growth_pct"] < 12:
            action = "Push revenue activation with healthier mix"
        else:
            action = "Scale high-quality revenue with discipline"

        rows.append(
            {
                "Distributor": r["distributor"],
                "Country": r["country"],
                "Priority": "High" if r["status"] != "Healthy" else "Medium",
                "Action": action,
                "Owner": r["owner"],
            }
        )
    return pd.DataFrame(rows)


def agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Agent")
    st.caption("Simple revenue-quality summary and next actions.")

    if df.empty:
        st.info("No distributors in current view.")
    else:
        top = df.sort_values(["net_revenue_musd", "ai_score"], ascending=[False, False]).iloc[0]
        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Top distributor by net revenue</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["distributor"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    Net Revenue <b>${fmt_money(top["net_revenue_musd"])}M</b> · Profit <b>${fmt_money(top["profit_musd"])}M</b> · GM <b>{fmt_pct(top["gm_pct"])}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("**Recommended actions**")
        st.write("- Review top revenue pools and risk pools together")
        st.write("- Protect price realization before pushing more spend")
        st.write("- Use this page to bridge distributor sales and finance")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "dist_rev_df" not in st.session_state:
    st.session_state.dist_rev_df = create_revenue_df()

rev_df = st.session_state.dist_rev_df.copy()

# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Farming · Distributor Revenue Intelligence</div>
        <div class="hero-title">Revenue Quality Command Layer</div>
        <div class="hero-sub">
            Monitor distributor revenue with sharper control over realization, spend, margin and price discipline.
            Keep it commercial, visual and easy to demo.
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
st.markdown('<div class="section-title">Distributor Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Filters stay in-page so the left navigation remains clean and premium.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.05, 1.1, 1.1, 0.8])

with c1:
    country_filter = st.selectbox("Country", ["All"] + sorted(rev_df["country"].unique().tolist()), key="drev_country")
with c2:
    status_filter = st.selectbox("Status", ["All"] + sorted(rev_df["status"].unique().tolist()), key="drev_status")
with c3:
    focus_filter = st.selectbox("Focus", ["All", "Top Revenue", "Price Risk", "High Growth"], key="drev_focus")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="drev_refresh")

if country_filter != "All":
    rev_df = rev_df[rev_df["country"] == country_filter]
if status_filter != "All":
    rev_df = rev_df[rev_df["status"] == status_filter]
if focus_filter == "Top Revenue":
    rev_df = rev_df.sort_values("net_revenue_musd", ascending=False).head(6)
elif focus_filter == "Price Risk":
    rev_df = rev_df[rev_df["status"] == "Price Risk"]
elif focus_filter == "High Growth":
    rev_df = rev_df.sort_values("growth_pct", ascending=False).head(6)

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Revenue Snapshot</span>
        <span class="signal-chip">Realization Control</span>
        <span class="signal-chip">Spend Discipline</span>
        <span class="signal-chip">Risk Queue</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
gross = rev_df["gross_revenue_musd"].sum() if not rev_df.empty else 0
net = rev_df["net_revenue_musd"].sum() if not rev_df.empty else 0
profit = rev_df["profit_musd"].sum() if not rev_df.empty else 0
gm = (profit / net * 100) if net > 0 else 0
spend = rev_df["trade_spend_pct"].mean() if not rev_df.empty else 0
rebate = rev_df["rebate_pct"].mean() if not rev_df.empty else 0
price_gap = rev_df["price_gap"].mean() if not rev_df.empty else 0
risk_count = int((rev_df["status"] != "Healthy").sum()) if not rev_df.empty else 0

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
with k1:
    st.metric("Gross Revenue ($M)", fmt_money(gross))
with k2:
    st.metric("Net Revenue ($M)", fmt_money(net))
with k3:
    st.metric("Profit ($M)", fmt_money(profit))
with k4:
    st.metric("Profit %", fmt_pct(gm))
with k5:
    st.metric("Avg Trade Spend", fmt_pct(spend))
with k6:
    st.metric("Avg Rebate", fmt_pct(rebate))
with k7:
    st.metric("Avg Price Gap", f"{price_gap:+.1f}")
with k8:
    st.metric("Risk Distributors", risk_count)

st.markdown("")

# =========================================================
# Main layout
# =========================================================
left, middle, right = st.columns([1.35, 1.15, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Revenue Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Gross, Net and Profit Trend</div>', unsafe_allow_html=True)

    trend = build_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Gross Revenue"], mode="lines+markers", name="Gross Revenue"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Net Revenue"], mode="lines+markers", name="Net Revenue"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Profit"], mode="lines+markers", name="Profit"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=35, b=10))
    st.plotly_chart(fig, width="stretch", key="drev_trend")
    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Revenue Pool View</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distributor Revenue vs Margin</div>', unsafe_allow_html=True)

    if rev_df.empty:
        st.info("No distributors match the current filters.")
    else:
        bubble = build_bubble(rev_df)
        fig2 = px.scatter(
            bubble,
            x="trade_spend_pct",
            y="gm_pct",
            size="net_revenue_musd",
            color="country",
            hover_name="distributor",
            title="Trade Spend % vs GM% · Bubble = Net Revenue",
        )
        fig2.update_layout(height=340, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig2, width="stretch", key="drev_bubble")

        summary = build_country_summary(rev_df)
        st.dataframe(summary, width="stretch", height=180, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    agent_panel(rev_df)

st.markdown("")

# =========================================================
# Risk queue + selected distributor + actions
# =========================================================
b1, b2, b3 = st.columns([1.15, 1.0, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Risk Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Revenue Quality Issues</div>', unsafe_allow_html=True)

    if rev_df.empty:
        st.info("No risk items.")
    else:
        queue_df = build_risk_queue(rev_df)
        if queue_df.empty:
            st.success("No major revenue quality risks in current view.")
        else:
            render_queue_cards(queue_df, top_n=4)

    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Distributor Command</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Snapshot</div>', unsafe_allow_html=True)

    if rev_df.empty:
        st.info("No distributor selected.")
    else:
        selected = st.selectbox("Distributor", sorted(rev_df["distributor"].unique().tolist()), key="drev_selected")
        row = rev_df[rev_df["distributor"] == selected].iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight">
                <div class="small-note">Distributor Snapshot</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{row["distributor"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {row["country"]} · {row["territory"]} · Status <b>{row["status"]}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(f"- Gross Revenue: ${fmt_money(row['gross_revenue_musd'])}M")
        st.write(f"- Net Revenue: ${fmt_money(row['net_revenue_musd'])}M")
        st.write(f"- Profit: ${fmt_money(row['profit_musd'])}M")
        st.write(f"- GM%: {fmt_pct(row['gm_pct'])}")
        st.write(f"- Trade Spend: {fmt_pct(row['trade_spend_pct'])}")
        st.write(f"- Price Gap: {row['price_gap']:+.1f}")

    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Action Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next Best Moves</div>', unsafe_allow_html=True)

    actions = build_action_queue(rev_df)
    if actions.empty:
        st.info("No actions available.")
    else:
        st.dataframe(actions, width="stretch", height=250, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)