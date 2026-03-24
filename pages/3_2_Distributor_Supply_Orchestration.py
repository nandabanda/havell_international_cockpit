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


def fmt_num(x):
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return "0"


def confidence_band(score):
    if score >= 88:
        return "High"
    if score >= 76:
        return "Medium"
    return "Watch"


def create_supply_df():
    rows = [
        ["DIST-001", "Alpha Distributors", "Saudi Arabia", "Riyadh North", "DC Riyadh", "Transit", 94.2, 19, 1180, 1250, 89, "Healthy"],
        ["DIST-002", "Jeddah Trading", "Saudi Arabia", "Jeddah West", "DC Jeddah", "Distributor Yard", 90.4, 14, 940, 1040, 83, "Watch"],
        ["DIST-003", "Dubai Channel House", "UAE", "Dubai Outer", "DC Dubai", "In Transit", 95.7, 21, 980, 1025, 88, "Healthy"],
        ["DIST-004", "Abu Dhabi Supply Co", "UAE", "Abu Dhabi Fringe", "DC Abu Dhabi", "Distributor Yard", 89.2, 12, 760, 910, 80, "At Risk"],
        ["DIST-005", "Jakarta Prime", "Indonesia", "Jakarta East", "Plant Jakarta", "Regional Buffer", 96.4, 23, 1320, 1375, 91, "Healthy"],
        ["DIST-006", "Surabaya Network", "Indonesia", "Surabaya South", "Regional Plant", "Transit", 88.4, 11, 820, 980, 77, "At Risk"],
        ["DIST-007", "Ho Chi Minh Trade", "Vietnam", "Ho Chi Minh Periphery", "DC HCM", "Distributor Yard", 87.8, 10, 710, 880, 76, "At Risk"],
        ["DIST-008", "Hanoi Market Link", "Vietnam", "Hanoi South", "DC Hanoi", "Transit", 90.1, 13, 740, 820, 78, "Watch"],
        ["DIST-009", "Singapore Channel Partners", "Singapore", "Industrial Belt", "SG Hub", "Distributor Yard", 97.1, 25, 430, 448, 90, "Healthy"],
        ["DIST-010", "Mumbai Edge Distribution", "India", "Mumbai Peripheral", "Plant Mumbai", "Regional Buffer", 95.2, 20, 1410, 1480, 92, "Healthy"],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "distributor_id", "distributor", "country", "territory",
            "source_node", "dest_node", "fill_rate_pct", "inventory_doh",
            "supply_qty", "demand_qty", "ai_score", "status"
        ],
    )
    df["shortage_qty"] = (df["demand_qty"] - df["supply_qty"]).clip(lower=0)
    df["service_gap_pct"] = (100 - df["fill_rate_pct"]).round(1)
    df["confidence"] = df["ai_score"].apply(confidence_band)
    df["owner"] = np.random.choice(
        ["Supply Lead", "Distributor Manager", "Planning", "Commercial Ops"],
        size=len(df),
    )
    df["recovery_priority"] = np.where(
        (df["status"] == "At Risk") | (df["shortage_qty"] > 120),
        "High",
        np.where(df["status"] == "Watch", "Medium", "Low"),
    )
    return df


def build_trend():
    periods = [f"M{k}" for k in range(1, 13)]
    fill = np.array([89.4, 89.9, 90.3, 90.8, 91.2, 91.7, 92.1, 92.4, 92.8, 93.0, 93.5, 94.0])
    doh = np.array([12.2, 12.8, 13.1, 13.4, 13.9, 14.2, 14.6, 14.9, 15.3, 15.7, 16.0, 16.4])
    shortage = np.array([690, 650, 618, 590, 552, 510, 472, 438, 401, 370, 332, 298])
    return pd.DataFrame({"period": periods, "Fill Rate": fill, "Inventory DOH": doh, "Shortage Qty": shortage})


def build_country_summary(df):
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby("country", as_index=False)
        .agg(
            Fill_Rate=("fill_rate_pct", "mean"),
            DOH=("inventory_doh", "mean"),
            Shortage=("shortage_qty", "sum"),
            Demand=("demand_qty", "sum"),
        )
        .sort_values("Demand", ascending=False)
    )


def build_bubble(df):
    return df.copy()


def build_risk_queue(df):
    q = df[(df["status"] != "Healthy") | (df["inventory_doh"] < 14)].copy()
    q = q.sort_values(["ai_score", "shortage_qty"], ascending=[False, False])
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
                    <b>Fill Rate:</b> {fmt_pct(r["fill_rate_pct"])} ·
                    <b>DOH:</b> {fmt_num(r["inventory_doh"])} ·
                    <b>Shortage:</b> {fmt_num(r["shortage_qty"])} units<br>
                    <b>Flow:</b> {r["source_node"]} → {r["dest_node"]} ·
                    <b>Priority:</b> {r["recovery_priority"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_action_queue(df):
    rows = []
    for _, r in df.sort_values(["ai_score", "shortage_qty"], ascending=[False, False]).head(6).iterrows():
        if r["status"] == "At Risk":
            action = "Immediate stock recovery and route intervention"
        elif r["inventory_doh"] < 14:
            action = "Replenishment acceleration and buffer review"
        elif r["shortage_qty"] > 80:
            action = "Reallocate stock and protect key outlets"
        else:
            action = "Maintain flow and monitor service"

        rows.append(
            {
                "Distributor": r["distributor"],
                "Country": r["country"],
                "Priority": r["recovery_priority"],
                "Action": action,
                "Owner": r["owner"],
            }
        )
    return pd.DataFrame(rows)


def agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Agent")
    st.caption("Simple distributor supply summary and next actions.")

    if df.empty:
        st.info("No distributors in current view.")
    else:
        top = df.sort_values(["demand_qty", "ai_score"], ascending=[False, False]).iloc[0]
        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Largest active distributor flow</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["distributor"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    Fill <b>{fmt_pct(top["fill_rate_pct"])}</b> · DOH <b>{fmt_num(top["inventory_doh"])}</b> · Shortage <b>{fmt_num(top["shortage_qty"])}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("**Recommended actions**")
        st.write("- Review at-risk distributors first")
        st.write("- Protect fill rate before stock-outs hit the field")
        st.write("- Use action queue to assign recovery owners")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "dist_supply_df" not in st.session_state:
    st.session_state.dist_supply_df = create_supply_df()

sup_df = st.session_state.dist_supply_df.copy()

# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Farming · Distributor Supply Orchestration</div>
        <div class="hero-title">Supply Service Command Layer</div>
        <div class="hero-sub">
            Monitor distributor service, stock health and shortage recovery through one simple operating view.
            Keep it practical, visual and action-oriented for demo.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Supply Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Distributor Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Filters stay in-page so the left navigation remains clean and premium.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.05, 1.1, 1.1, 0.8])

with c1:
    country_filter = st.selectbox("Country", ["All"] + sorted(sup_df["country"].unique().tolist()), key="dsup_country")
with c2:
    status_filter = st.selectbox("Status", ["All"] + sorted(sup_df["status"].unique().tolist()), key="dsup_status")
with c3:
    focus_filter = st.selectbox("Focus", ["All", "At Risk", "Low DOH", "High Demand"], key="dsup_focus")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="dsup_refresh")

if country_filter != "All":
    sup_df = sup_df[sup_df["country"] == country_filter]
if status_filter != "All":
    sup_df = sup_df[sup_df["status"] == status_filter]
if focus_filter == "At Risk":
    sup_df = sup_df[sup_df["status"] == "At Risk"]
elif focus_filter == "Low DOH":
    sup_df = sup_df[sup_df["inventory_doh"] < 14]
elif focus_filter == "High Demand":
    sup_df = sup_df.sort_values("demand_qty", ascending=False).head(6)

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Service Snapshot</span>
        <span class="signal-chip">Stock Health</span>
        <span class="signal-chip">Shortage Control</span>
        <span class="signal-chip">Recovery Queue</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
fill = sup_df["fill_rate_pct"].mean() if not sup_df.empty else 0
doh = sup_df["inventory_doh"].mean() if not sup_df.empty else 0
supply = sup_df["supply_qty"].sum() if not sup_df.empty else 0
demand = sup_df["demand_qty"].sum() if not sup_df.empty else 0
shortage = sup_df["shortage_qty"].sum() if not sup_df.empty else 0
risk_count = int((sup_df["status"] == "At Risk").sum()) if not sup_df.empty else 0
watch_count = int((sup_df["status"] == "Watch").sum()) if not sup_df.empty else 0
service_gap = (100 - fill) if fill > 0 else 0

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
with k1:
    st.metric("Avg Fill Rate", fmt_pct(fill))
with k2:
    st.metric("Avg DOH", fmt_num(doh))
with k3:
    st.metric("Supply Qty", fmt_num(supply))
with k4:
    st.metric("Demand Qty", fmt_num(demand))
with k5:
    st.metric("Shortage Qty", fmt_num(shortage))
with k6:
    st.metric("Service Gap", fmt_pct(service_gap))
with k7:
    st.metric("At-Risk Distributors", risk_count)
with k8:
    st.metric("Watch Distributors", watch_count)

st.markdown("")

# =========================================================
# Main layout
# =========================================================
left, middle, right = st.columns([1.35, 1.15, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Supply Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Fill, DOH and Shortage Trend</div>', unsafe_allow_html=True)

    trend = build_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Fill Rate"], mode="lines+markers", name="Fill Rate"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Inventory DOH"], mode="lines+markers", name="Inventory DOH"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Shortage Qty"], mode="lines+markers", name="Shortage Qty"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=35, b=10))
    st.plotly_chart(fig, width="stretch", key="dsup_trend")
    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Supply Pressure View</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">DOH vs Fill Rate</div>', unsafe_allow_html=True)

    if sup_df.empty:
        st.info("No distributors match the current filters.")
    else:
        bubble = build_bubble(sup_df)
        fig2 = px.scatter(
            bubble,
            x="inventory_doh",
            y="fill_rate_pct",
            size="shortage_qty",
            color="country",
            hover_name="distributor",
            title="DOH vs Fill Rate · Bubble = Shortage Qty",
        )
        fig2.update_layout(height=340, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig2, width="stretch", key="dsup_bubble")

        summary = build_country_summary(sup_df)
        st.dataframe(summary, width="stretch", height=180, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    agent_panel(sup_df)

st.markdown("")

# =========================================================
# Risk queue + selected distributor + actions
# =========================================================
b1, b2, b3 = st.columns([1.15, 1.0, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Recovery Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Supply Issues Requiring Action</div>', unsafe_allow_html=True)

    if sup_df.empty:
        st.info("No recovery items.")
    else:
        queue_df = build_risk_queue(sup_df)
        if queue_df.empty:
            st.success("No major supply issues in current view.")
        else:
            render_queue_cards(queue_df, top_n=4)

    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Distributor Command</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Snapshot</div>', unsafe_allow_html=True)

    if sup_df.empty:
        st.info("No distributor selected.")
    else:
        selected = st.selectbox("Distributor", sorted(sup_df["distributor"].unique().tolist()), key="dsup_selected")
        row = sup_df[sup_df["distributor"] == selected].iloc[0]

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
        st.write(f"- Fill Rate: {fmt_pct(row['fill_rate_pct'])}")
        st.write(f"- Inventory DOH: {fmt_num(row['inventory_doh'])}")
        st.write(f"- Supply Qty: {fmt_num(row['supply_qty'])}")
        st.write(f"- Demand Qty: {fmt_num(row['demand_qty'])}")
        st.write(f"- Shortage Qty: {fmt_num(row['shortage_qty'])}")
        st.write(f"- Flow: {row['source_node']} → {row['dest_node']}")

    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Action Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next Best Moves</div>', unsafe_allow_html=True)

    actions = build_action_queue(sup_df)
    if actions.empty:
        st.info("No actions available.")
    else:
        st.dataframe(actions, width="stretch", height=250, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)