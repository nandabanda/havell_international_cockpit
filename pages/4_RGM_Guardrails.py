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
        return f"{float(x):,.2f}"
    except Exception:
        return "0.00"


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


def create_rgm_df():
    rows = [
        ["ACC-001", "Alpha Distributors", "Saudi Arabia", "Riyadh North", "Beverages", 84.0, 87.0, 4.8, 2.1, 22.4, 88],
        ["ACC-002", "Jeddah Trading", "Saudi Arabia", "Jeddah West", "Snacks", 80.5, 86.5, 5.9, 2.8, 19.6, 81],
        ["ACC-003", "Dubai Channel House", "UAE", "Dubai Outer", "Beverages", 88.2, 88.0, 4.1, 1.7, 24.8, 87],
        ["ACC-004", "Abu Dhabi Supply Co", "UAE", "Abu Dhabi Fringe", "Home Care", 79.1, 85.0, 6.2, 2.9, 18.9, 78],
        ["ACC-005", "Jakarta Prime", "Indonesia", "Jakarta East", "Beverages", 89.0, 88.5, 4.0, 1.8, 25.1, 91],
        ["ACC-006", "Surabaya Network", "Indonesia", "Surabaya South", "Personal Care", 78.7, 84.0, 6.1, 2.7, 18.8, 77],
        ["ACC-007", "Ho Chi Minh Trade", "Vietnam", "HCM Periphery", "Beverages", 77.9, 83.5, 6.3, 2.8, 18.4, 76],
        ["ACC-008", "Hanoi Market Link", "Vietnam", "Hanoi South", "Snacks", 81.4, 84.5, 5.6, 2.5, 20.1, 79],
        ["ACC-009", "Singapore Channel Partners", "Singapore", "Industrial Belt", "Premium", 91.1, 89.0, 3.7, 1.4, 27.4, 90],
        ["ACC-010", "Mumbai Edge Distribution", "India", "Mumbai Peripheral", "Beverages", 89.3, 88.0, 4.2, 1.7, 25.7, 92],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "account_id", "account", "country", "territory", "category",
            "realized_price_index", "target_price_index",
            "trade_spend_pct", "rebate_pct", "gm_pct", "ai_score"
        ],
    )
    df["price_gap"] = (df["realized_price_index"] - df["target_price_index"]).round(1)
    df["margin_at_risk_musd"] = np.round(np.random.uniform(0.25, 2.6, len(df)), 2)
    df["discount_leakage_pct"] = np.round(np.random.uniform(1.0, 4.5, len(df)), 1)
    df["volume_quality_pct"] = np.round(np.random.uniform(72, 95, len(df)), 1)
    df["confidence"] = df["ai_score"].apply(confidence_band)

    def status(row):
        if row["price_gap"] < -2 or row["trade_spend_pct"] > 5.8:
            return "Outside Guardrail"
        if row["price_gap"] < 0 or row["trade_spend_pct"] > 5.0:
            return "Watch"
        return "In Guardrail"

    df["status"] = df.apply(status, axis=1)
    df["owner"] = np.random.choice(
        ["Commercial Finance", "RGM Lead", "Regional Sales", "Distributor Manager"],
        size=len(df),
    )
    return df


def build_trend():
    periods = [f"M{k}" for k in range(1, 13)]
    realization = np.array([83.2, 83.5, 83.8, 84.1, 84.3, 84.7, 85.0, 85.2, 85.5, 85.9, 86.2, 86.6])
    spend = np.array([5.9, 5.8, 5.8, 5.7, 5.6, 5.5, 5.4, 5.3, 5.2, 5.2, 5.1, 5.0])
    gm = np.array([20.2, 20.4, 20.7, 21.0, 21.2, 21.4, 21.7, 22.0, 22.2, 22.4, 22.7, 23.0])
    return pd.DataFrame({"period": periods, "Realization": realization, "Trade Spend": spend, "GM": gm})


def build_risk_queue(df):
    q = df[df["status"] != "In Guardrail"].copy()
    q = q.sort_values(["ai_score", "margin_at_risk_musd"], ascending=[False, False])
    return q


def render_queue_cards(df, top_n=4):
    for _, r in df.head(top_n).iterrows():
        issue = "Price below corridor" if r["price_gap"] < 0 else "Spend outside safe band"
        st.markdown(
            f"""
            <div class="queue-card">
                <div class="queue-title">{r["account"]}</div>
                <div class="queue-meta">
                    {r["country"]} · {r["territory"]} · {r["category"]} · Status <b>{r["status"]}</b> · AI <b>{int(r["ai_score"])}</b>
                </div>
                <div class="queue-body">
                    <b>Issue:</b> {issue}<br>
                    <b>Price Gap:</b> {r["price_gap"]:+.1f} ·
                    <b>Trade Spend:</b> {fmt_pct(r["trade_spend_pct"])} ·
                    <b>Margin at Risk:</b> ${fmt_money(r["margin_at_risk_musd"])}M
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_action_queue(df):
    rows = []
    for _, r in df.sort_values(["ai_score", "margin_at_risk_musd"], ascending=[False, False]).head(6).iterrows():
        if r["price_gap"] < -2:
            action = "Correct price corridor and review customer terms"
        elif r["trade_spend_pct"] > 5.8:
            action = "Freeze discretionary spend and review approvals"
        elif r["price_gap"] < 0:
            action = "Tighten realization and monitor"
        else:
            action = "Maintain within guardrail"

        rows.append(
            {
                "Account": r["account"],
                "Country": r["country"],
                "Priority": "High" if r["status"] == "Outside Guardrail" else "Medium",
                "Action": action,
                "Owner": r["owner"],
            }
        )
    return pd.DataFrame(rows)


def build_waterfall_components(df):
    total_risk = float(df["margin_at_risk_musd"].sum()) if not df.empty else 0.0
    price_erosion = round(total_risk * 0.36, 2)
    spend_erosion = round(total_risk * 0.28, 2)
    rebate_erosion = round(total_risk * 0.16, 2)
    leakage_erosion = round(total_risk * 0.20, 2)
    protected = round(total_risk * 0.22, 2)

    bridge = pd.DataFrame(
        {
            "Step": [
                "Gross Margin Pool",
                "Price Erosion",
                "Trade Spend Drift",
                "Rebate Pressure",
                "Leakage",
                "Protected Margin",
            ],
            "Value": [
                total_risk + protected,
                -price_erosion,
                -spend_erosion,
                -rebate_erosion,
                -leakage_erosion,
                protected,
            ],
        }
    )
    return bridge


def agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Agent")
    st.caption("Governance summary with distinct analytics orientation.")

    if df.empty:
        st.info("No accounts in current view.")
    else:
        out_count = int((df["status"] == "Outside Guardrail").sum())
        risk_value = df["margin_at_risk_musd"].sum()
        top = df.sort_values(["margin_at_risk_musd", "ai_score"], ascending=[False, False]).iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Top issue in view</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    Outside Guardrail <b>{out_count}</b> · Margin at Risk <b>${fmt_money(risk_value)}M</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("**How to read this page**")
        st.write("- Scatter: who is outside safe pricing/spend zone")
        st.write("- Treemap: where risk sits")
        st.write("- Waterfall: what is eroding value")
        st.write("- Queue: what needs action now")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "rgm_guardrail_df" not in st.session_state:
    st.session_state.rgm_guardrail_df = create_rgm_df()

rgm_df = st.session_state.rgm_guardrail_df.copy()

# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Governance · RGM Guardrails</div>
        <div class="hero-title">Commercial Guardrail Analytics</div>
        <div class="hero-sub">
            This page should feel distinct: keep the richer analytical graphs — scatter, treemap and waterfall —
            so governance feels like a real diagnostic layer, not just another cockpit.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Guardrail Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Commercial Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Simple controls, richer visuals.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.05, 1.1, 1.1, 0.8])

with c1:
    country_filter = st.selectbox("Country", ["All"] + sorted(rgm_df["country"].unique().tolist()), key="rgm_country")
with c2:
    status_filter = st.selectbox("Status", ["All"] + sorted(rgm_df["status"].unique().tolist()), key="rgm_status")
with c3:
    focus_filter = st.selectbox("Focus", ["All", "Outside Guardrail", "Watch", "High Margin Risk"], key="rgm_focus")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="rgm_refresh")

if country_filter != "All":
    rgm_df = rgm_df[rgm_df["country"] == country_filter]
if status_filter != "All":
    rgm_df = rgm_df[rgm_df["status"] == status_filter]
if focus_filter == "Outside Guardrail":
    rgm_df = rgm_df[rgm_df["status"] == "Outside Guardrail"]
elif focus_filter == "Watch":
    rgm_df = rgm_df[rgm_df["status"] == "Watch"]
elif focus_filter == "High Margin Risk":
    rgm_df = rgm_df.sort_values("margin_at_risk_musd", ascending=False).head(6)

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Scatter</span>
        <span class="signal-chip">Treemap</span>
        <span class="signal-chip">Waterfall</span>
        <span class="signal-chip">Issue Queue</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
in_guardrail = int((rgm_df["status"] == "In Guardrail").sum()) if not rgm_df.empty else 0
outside_guardrail = int((rgm_df["status"] == "Outside Guardrail").sum()) if not rgm_df.empty else 0
watch = int((rgm_df["status"] == "Watch").sum()) if not rgm_df.empty else 0
avg_realization = rgm_df["realized_price_index"].mean() if not rgm_df.empty else 0
avg_spend = rgm_df["trade_spend_pct"].mean() if not rgm_df.empty else 0
avg_gm = rgm_df["gm_pct"].mean() if not rgm_df.empty else 0
margin_risk = rgm_df["margin_at_risk_musd"].sum() if not rgm_df.empty else 0
approvals_pending = outside_guardrail + watch

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
with k1:
    st.metric("In Guardrail", in_guardrail)
with k2:
    st.metric("Outside Guardrail", outside_guardrail)
with k3:
    st.metric("Watch", watch)
with k4:
    st.metric("Avg Realization", fmt_pct(avg_realization))
with k5:
    st.metric("Avg Trade Spend", fmt_pct(avg_spend))
with k6:
    st.metric("Avg GM", fmt_pct(avg_gm))
with k7:
    st.metric("Margin at Risk ($M)", fmt_money(margin_risk))
with k8:
    st.metric("Approvals Pending", approvals_pending)

st.markdown("")

# =========================================================
# Top analytics row
# =========================================================
left, middle, right = st.columns([1.25, 1.05, 0.9])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Guardrail Scatter</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Realization vs Trade Spend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Who is inside or outside the safe zone?</div>', unsafe_allow_html=True)

    if rgm_df.empty:
        st.info("No accounts match the current filters.")
    else:
        fig = px.scatter(
            rgm_df,
            x="trade_spend_pct",
            y="realized_price_index",
            size="margin_at_risk_musd",
            color="status",
            hover_name="account",
            hover_data=["country", "category", "price_gap", "gm_pct"],
            title="Trade Spend % vs Realization · Bubble = Margin at Risk",
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig, width="stretch", key="rgm_scatter")
    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Risk Treemap</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Where Margin Risk Sits</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Country → Category → Account</div>', unsafe_allow_html=True)

    if rgm_df.empty:
        st.info("No accounts available.")
    else:
        tree_df = rgm_df.copy()
        fig2 = px.treemap(
            tree_df,
            path=["country", "category", "account"],
            values="margin_at_risk_musd",
            color="margin_at_risk_musd",
            hover_data=["status", "trade_spend_pct", "price_gap"],
        )
        fig2.update_layout(height=380, margin=dict(l=5, r=5, t=20, b=5))
        st.plotly_chart(fig2, width="stretch", key="rgm_treemap")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    agent_panel(rgm_df)

st.markdown("")

# =========================================================
# Bottom analytics row
# =========================================================
b1, b2, b3 = st.columns([1.1, 1.0, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Realization, Spend and GM Trend</div>', unsafe_allow_html=True)

    trend = build_trend()
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=trend["period"], y=trend["Realization"], mode="lines+markers", name="Realization"))
    fig3.add_trace(go.Scatter(x=trend["period"], y=trend["Trade Spend"], mode="lines+markers", name="Trade Spend"))
    fig3.add_trace(go.Scatter(x=trend["period"], y=trend["GM"], mode="lines+markers", name="GM"))
    fig3.update_layout(height=330, margin=dict(l=10, r=10, t=35, b=10))
    st.plotly_chart(fig3, width="stretch", key="rgm_trend")
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Waterfall</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What Is Eroding Value</div>', unsafe_allow_html=True)

    if rgm_df.empty:
        st.info("No data available.")
    else:
        bridge_df = build_waterfall_components(rgm_df)
        fig4 = go.Figure(
            go.Waterfall(
                name="RGM Waterfall",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                x=bridge_df["Step"],
                y=bridge_df["Value"],
                connector={"line": {"width": 1}},
            )
        )
        fig4.update_layout(height=330, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig4, width="stretch", key="rgm_waterfall")
    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Issue Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Accounts Requiring Review</div>', unsafe_allow_html=True)

    if rgm_df.empty:
        st.info("No issue items.")
    else:
        queue_df = build_risk_queue(rgm_df)
        if queue_df.empty:
            st.success("All visible accounts are within guardrail.")
        else:
            render_queue_cards(queue_df, top_n=3)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Bottom action row
# =========================================================
c1, c2 = st.columns([1.0, 1.0])

with c1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Selected Account</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Commercial Snapshot</div>', unsafe_allow_html=True)

    if rgm_df.empty:
        st.info("No account selected.")
    else:
        selected = st.selectbox("Account", sorted(rgm_df["account"].unique().tolist()), key="rgm_selected")
        row = rgm_df[rgm_df["account"] == selected].iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight">
                <div class="small-note">Account Snapshot</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{row["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {row["country"]} · {row["territory"]} · {row["category"]} · Status <b>{row["status"]}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(f"- Realization: {fmt_pct(row['realized_price_index'])}")
        st.write(f"- Target: {fmt_pct(row['target_price_index'])}")
        st.write(f"- Price Gap: {row['price_gap']:+.1f}")
        st.write(f"- Trade Spend: {fmt_pct(row['trade_spend_pct'])}")
        st.write(f"- Rebate: {fmt_pct(row['rebate_pct'])}")
        st.write(f"- GM: {fmt_pct(row['gm_pct'])}")
        st.write(f"- Margin at Risk: ${fmt_money(row['margin_at_risk_musd'])}M")

    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Action Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next Best Moves</div>', unsafe_allow_html=True)

    actions = build_action_queue(rgm_df)
    if actions.empty:
        st.info("No actions available.")
    else:
        st.dataframe(actions, width="stretch", height=240, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)