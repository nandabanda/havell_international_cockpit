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


def create_supply_sync_df():
    rows = [
        ["FL-001", "Plant Mumbai", "DC West", "India", "Beverages", 1450, 1580, 130, 91.8, 14, 89],
        ["FL-002", "Plant Jakarta", "DC East", "Indonesia", "Beverages", 1320, 1480, 160, 89.4, 12, 84],
        ["FL-003", "DC Riyadh", "Distributor Hub 1", "Saudi Arabia", "Snacks", 980, 1110, 130, 88.8, 11, 82],
        ["FL-004", "DC Dubai", "Distributor Hub 2", "UAE", "Home Care", 910, 970, 60, 93.6, 16, 87],
        ["FL-005", "Plant HCM", "DC South", "Vietnam", "Beverages", 840, 970, 130, 87.2, 10, 79],
        ["FL-006", "DC Singapore", "Specialty Hub", "Singapore", "Premium", 420, 445, 25, 96.1, 22, 90],
        ["FL-007", "Plant Riyadh", "DC North", "Saudi Arabia", "Beverages", 1260, 1355, 95, 92.3, 15, 86],
        ["FL-008", "Plant Abu Dhabi", "DC Central", "UAE", "Beverages", 760, 860, 100, 88.4, 11, 80],
        ["FL-009", "Plant Surabaya", "DC Java", "Indonesia", "Personal Care", 680, 790, 110, 86.7, 9, 77],
        ["FL-010", "Plant Hanoi", "DC North", "Vietnam", "Snacks", 720, 815, 95, 88.9, 12, 81],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "flow_id", "source_node", "dest_node", "country", "category",
            "supply_qty", "demand_qty", "shortage_qty", "fill_rate_pct", "doh", "ai_score"
        ],
    )
    df["stress_index"] = np.round(
        (100 - df["fill_rate_pct"]) * 0.5 + df["shortage_qty"] * 0.08 + np.maximum(0, 14 - df["doh"]) * 2.5,
        1,
    )
    df["margin_impact_musd"] = np.round(np.random.uniform(0.15, 1.9, len(df)), 2)
    df["confidence"] = df["ai_score"].apply(confidence_band)

    def status(row):
        if row["fill_rate_pct"] < 89 or row["doh"] < 11 or row["shortage_qty"] > 120:
            return "Critical"
        if row["fill_rate_pct"] < 92 or row["doh"] < 14 or row["shortage_qty"] > 80:
            return "Watch"
        return "Stable"

    df["status"] = df.apply(status, axis=1)
    df["owner"] = np.random.choice(
        ["Supply Lead", "Planning Lead", "Network Ops", "Commercial Supply"],
        size=len(df),
    )
    return df


def build_trend():
    periods = [f"W{k}" for k in range(1, 13)]
    fill = np.array([89.1, 89.4, 89.7, 90.0, 90.4, 90.8, 91.2, 91.6, 92.0, 92.3, 92.7, 93.0])
    shortage = np.array([980, 942, 910, 872, 836, 790, 742, 698, 660, 622, 588, 552])
    doh = np.array([11.2, 11.5, 11.8, 12.1, 12.4, 12.8, 13.1, 13.4, 13.7, 14.0, 14.3, 14.6])
    return pd.DataFrame({"period": periods, "Fill Rate": fill, "Shortage Qty": shortage, "DOH": doh})


def build_risk_queue(df):
    q = df[df["status"] != "Stable"].copy()
    q = q.sort_values(["ai_score", "stress_index"], ascending=[False, False])
    return q


def render_queue_cards(df, top_n=4):
    for _, r in df.head(top_n).iterrows():
        st.markdown(
            f"""
            <div class="queue-card">
                <div class="queue-title">{r["source_node"]} → {r["dest_node"]}</div>
                <div class="queue-meta">
                    {r["country"]} · {r["category"]} · Status <b>{r["status"]}</b> · AI <b>{int(r["ai_score"])}</b> · Confidence <b>{r["confidence"]}</b>
                </div>
                <div class="queue-body">
                    <b>Fill Rate:</b> {fmt_pct(r["fill_rate_pct"])} ·
                    <b>DOH:</b> {fmt_num(r["doh"])} ·
                    <b>Shortage:</b> {fmt_num(r["shortage_qty"])}<br>
                    <b>Stress Index:</b> {r["stress_index"]:.1f} ·
                    <b>Margin Impact:</b> ${fmt_money(r["margin_impact_musd"])}M
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_action_queue(df):
    rows = []
    for _, r in df.sort_values(["ai_score", "stress_index"], ascending=[False, False]).head(6).iterrows():
        if r["status"] == "Critical":
            action = "Immediate reallocation / expedite supply"
        elif r["shortage_qty"] > 100:
            action = "Rebalance flow and protect high-priority demand"
        elif r["doh"] < 12:
            action = "Increase cover and accelerate replenishment"
        else:
            action = "Monitor and maintain network stability"

        rows.append(
            {
                "Flow": f"{r['source_node']} → {r['dest_node']}",
                "Country": r["country"],
                "Priority": "High" if r["status"] == "Critical" else "Medium",
                "Action": action,
                "Owner": r["owner"],
            }
        )
    return pd.DataFrame(rows)


def build_waterfall(df):
    total = float(df["margin_impact_musd"].sum()) if not df.empty else 0.0
    shortage = round(total * 0.42, 2)
    service = round(total * 0.24, 2)
    inventory = round(total * 0.18, 2)
    flow = round(total * 0.16, 2)
    protected = round(total * 0.25, 2)

    return pd.DataFrame(
        {
            "Step": [
                "At-Risk Value",
                "Shortage Loss",
                "Service Erosion",
                "Inventory Pressure",
                "Flow Friction",
                "Protected Value",
            ],
            "Value": [
                total + protected,
                -shortage,
                -service,
                -inventory,
                -flow,
                protected,
            ],
        }
    )


def agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Agent")
    st.caption("Weekly supply decision framing.")

    if df.empty:
        st.info("No flows in current view.")
    else:
        critical = int((df["status"] == "Critical").sum())
        risk = float(df["margin_impact_musd"].sum())
        top = df.sort_values(["stress_index", "ai_score"], ascending=[False, False]).iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Top stressed flow</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["source_node"]} → {top["dest_node"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    Critical Flows <b>{critical}</b> · Margin Impact <b>${fmt_money(risk)}M</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("**How to read this page**")
        st.write("- Trend: are we stabilizing or worsening?")
        st.write("- Treemap: where pressure sits in the network")
        st.write("- Waterfall: what is destroying value")
        st.write("- Queue: what must be approved now")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "supply_sync_df" not in st.session_state:
    st.session_state.supply_sync_df = create_supply_sync_df()

sync_df = st.session_state.supply_sync_df.copy()

# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Governance · Supply Sync</div>
        <div class="hero-title">Weekly Decision Engine</div>
        <div class="hero-sub">
            Keep this page distinct from the others: use richer network-style analytics to show where supply stress sits,
            what it is costing, and what leadership needs to approve now.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Supply Sync Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Flow Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Simple controls, richer analytics.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.05, 1.1, 1.1, 0.8])

with c1:
    country_filter = st.selectbox("Country", ["All"] + sorted(sync_df["country"].unique().tolist()), key="ss_country")
with c2:
    status_filter = st.selectbox("Status", ["All"] + sorted(sync_df["status"].unique().tolist()), key="ss_status")
with c3:
    focus_filter = st.selectbox("Focus", ["All", "Critical", "Watch", "High Stress"], key="ss_focus")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="ss_refresh")

if country_filter != "All":
    sync_df = sync_df[sync_df["country"] == country_filter]
if status_filter != "All":
    sync_df = sync_df[sync_df["status"] == status_filter]
if focus_filter == "Critical":
    sync_df = sync_df[sync_df["status"] == "Critical"]
elif focus_filter == "Watch":
    sync_df = sync_df[sync_df["status"] == "Watch"]
elif focus_filter == "High Stress":
    sync_df = sync_df.sort_values("stress_index", ascending=False).head(6)

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Trend</span>
        <span class="signal-chip">Treemap</span>
        <span class="signal-chip">Waterfall</span>
        <span class="signal-chip">Decision Queue</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
stable = int((sync_df["status"] == "Stable").sum()) if not sync_df.empty else 0
critical = int((sync_df["status"] == "Critical").sum()) if not sync_df.empty else 0
watch = int((sync_df["status"] == "Watch").sum()) if not sync_df.empty else 0
avg_fill = sync_df["fill_rate_pct"].mean() if not sync_df.empty else 0
avg_doh = sync_df["doh"].mean() if not sync_df.empty else 0
shortage = sync_df["shortage_qty"].sum() if not sync_df.empty else 0
margin_impact = sync_df["margin_impact_musd"].sum() if not sync_df.empty else 0
pending = critical + watch

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
with k1:
    st.metric("Stable Flows", stable)
with k2:
    st.metric("Critical Flows", critical)
with k3:
    st.metric("Watch Flows", watch)
with k4:
    st.metric("Avg Fill Rate", fmt_pct(avg_fill))
with k5:
    st.metric("Avg DOH", fmt_num(avg_doh))
with k6:
    st.metric("Shortage Qty", fmt_num(shortage))
with k7:
    st.metric("Margin Impact ($M)", fmt_money(margin_impact))
with k8:
    st.metric("Pending Decisions", pending)

st.markdown("")

# =========================================================
# Top analytics row
# =========================================================
left, middle, right = st.columns([1.25, 1.05, 0.9])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Fill, Shortage and DOH Trend</div>', unsafe_allow_html=True)

    trend = build_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Fill Rate"], mode="lines+markers", name="Fill Rate"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Shortage Qty"], mode="lines+markers", name="Shortage Qty"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["DOH"], mode="lines+markers", name="DOH"))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=35, b=10))
    st.plotly_chart(fig, width="stretch", key="ss_trend")
    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Stress Treemap</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Where Pressure Sits</div>', unsafe_allow_html=True)

    if sync_df.empty:
        st.info("No flows available.")
    else:
        fig2 = px.treemap(
            sync_df,
            path=["country", "category", "dest_node"],
            values="stress_index",
            color="margin_impact_musd",
            hover_data=["status", "fill_rate_pct", "shortage_qty"],
        )
        fig2.update_layout(height=380, margin=dict(l=5, r=5, t=20, b=5))
        st.plotly_chart(fig2, width="stretch", key="ss_treemap")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    agent_panel(sync_df)

st.markdown("")

# =========================================================
# Bottom analytics row
# =========================================================
b1, b2, b3 = st.columns([1.1, 1.0, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Network View</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Stress by Flow</div>', unsafe_allow_html=True)

    if sync_df.empty:
        st.info("No flows available.")
    else:
        fig3 = px.scatter(
            sync_df,
            x="doh",
            y="fill_rate_pct",
            size="shortage_qty",
            color="status",
            hover_name="dest_node",
            hover_data=["source_node", "country", "stress_index"],
            title="DOH vs Fill Rate · Bubble = Shortage Qty",
        )
        fig3.update_layout(height=330, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig3, width="stretch", key="ss_scatter")
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Waterfall</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What Is Destroying Value</div>', unsafe_allow_html=True)

    if sync_df.empty:
        st.info("No data available.")
    else:
        bridge_df = build_waterfall(sync_df)
        fig4 = go.Figure(
            go.Waterfall(
                name="Supply Waterfall",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                x=bridge_df["Step"],
                y=bridge_df["Value"],
                connector={"line": {"width": 1}},
            )
        )
        fig4.update_layout(height=330, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig4, width="stretch", key="ss_waterfall")
    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Decision Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Flows Requiring Action</div>', unsafe_allow_html=True)

    if sync_df.empty:
        st.info("No issue items.")
    else:
        queue_df = build_risk_queue(sync_df)
        if queue_df.empty:
            st.success("All visible flows are stable.")
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
    st.markdown('<div class="section-kicker">Selected Flow</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Flow Snapshot</div>', unsafe_allow_html=True)

    if sync_df.empty:
        st.info("No flow selected.")
    else:
        sync_df = sync_df.copy()
        sync_df["flow_label"] = sync_df["source_node"] + " → " + sync_df["dest_node"]
        selected = st.selectbox("Flow", sorted(sync_df["flow_label"].unique().tolist()), key="ss_selected")
        row = sync_df[sync_df["flow_label"] == selected].iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight">
                <div class="small-note">Flow Snapshot</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{row["flow_label"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {row["country"]} · {row["category"]} · Status <b>{row["status"]}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(f"- Fill Rate: {fmt_pct(row['fill_rate_pct'])}")
        st.write(f"- DOH: {fmt_num(row['doh'])}")
        st.write(f"- Supply Qty: {fmt_num(row['supply_qty'])}")
        st.write(f"- Demand Qty: {fmt_num(row['demand_qty'])}")
        st.write(f"- Shortage Qty: {fmt_num(row['shortage_qty'])}")
        st.write(f"- Margin Impact: ${fmt_money(row['margin_impact_musd'])}M")

    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Action Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next Best Moves</div>', unsafe_allow_html=True)

    actions = build_action_queue(sync_df.drop(columns=["flow_label"]) if "flow_label" in sync_df.columns else sync_df)
    if actions.empty:
        st.info("No actions available.")
    else:
        st.dataframe(actions, width="stretch", height=240, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)