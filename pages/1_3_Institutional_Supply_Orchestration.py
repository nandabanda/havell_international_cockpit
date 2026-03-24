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

        .stress-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 12px 12px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.72);
        }

        .stress-title {
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
            font-size: 0.98rem;
        }

        .stress-meta {
            color: #64748b;
            font-size: 0.83rem;
            margin-bottom: 6px;
        }

        .stress-body {
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


def fmt_num(x):
    try:
        return f"{float(x):,.1f}"
    except Exception:
        return "0.0"


def confidence_band(score):
    if score >= 88:
        return "High"
    if score >= 76:
        return "Medium"
    return "Watch"


def create_supply_df():
    rows = [
        ["SUP-001", "L&T Construction", "UAE", "Cable Kit A", "DC Dubai", "3PL Gulf", "In Transit", 96.0, 24, 180, 220, 91],
        ["SUP-002", "Tata Projects", "India", "Switchgear Set B", "Plant West", "Project Hub", "Allocated", 94.2, 18, 210, 245, 90],
        ["SUP-003", "Adani Infra", "India", "Panel Bundle X", "Plant North", "Regional DC", "At Risk", 88.7, 12, 260, 320, 92],
        ["SUP-004", "Jakson Solar", "India", "Solar Electrical Kit", "Plant West", "Project Yard", "Allocated", 95.5, 21, 160, 175, 87],
        ["SUP-005", "Shapoorji Pallonji", "Saudi Arabia", "Lighting Pack Z", "DC Riyadh", "Site Buffer", "At Risk", 89.8, 10, 140, 190, 84],
        ["SUP-006", "Gov Infra Board", "UAE", "Industrial Control Pack", "DC Abu Dhabi", "Project Hub", "Allocated", 93.1, 17, 155, 180, 83],
        ["SUP-007", "Large Real Estate Group", "Saudi Arabia", "Wiring Bundle M", "DC Riyadh", "Transit", "In Transit", 92.5, 15, 170, 205, 81],
        ["SUP-008", "OEM Partner Cluster", "Indonesia", "Low Voltage Kit", "Regional Plant", "Dealer Buffer", "Watch", 90.2, 13, 135, 165, 80],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "flow_id", "account", "market", "sku_bundle", "source_node", "dest_node", "supply_status",
            "fill_rate_pct", "doh", "supply_qty", "demand_qty", "ai_score"
        ],
    )
    df["shortage_qty"] = (df["demand_qty"] - df["supply_qty"]).clip(lower=0)
    df["service_gap_pct"] = (100 - df["fill_rate_pct"]).round(1)
    df["stress_level"] = np.where(
        (df["fill_rate_pct"] < 90) | (df["doh"] < 14) | (df["shortage_qty"] > 40),
        "High",
        np.where((df["fill_rate_pct"] < 93) | (df["doh"] < 18), "Medium", "Low"),
    )
    df["confidence"] = df["ai_score"].apply(confidence_band)
    df["owner"] = np.random.choice(
        ["Supply Lead", "Planning", "Project Operations", "Commercial Supply"],
        size=len(df),
    )
    return df


def build_supply_trend():
    weeks = [f"W{k}" for k in range(1, 13)]
    fill = np.array([90.8, 91.4, 92.1, 91.7, 92.8, 93.5, 93.0, 93.8, 94.1, 93.9, 94.7, 95.0])
    doh = np.array([12.4, 13.1, 13.6, 13.0, 14.2, 14.8, 14.1, 15.3, 15.1, 14.9, 15.8, 16.2])
    shortage = np.array([210, 198, 184, 192, 170, 158, 166, 145, 139, 142, 128, 116])
    return pd.DataFrame({"week": weeks, "Fill Rate": fill, "DOH": doh, "Shortage Qty": shortage})


def build_node_view(df):
    x = (
        df.groupby(["source_node", "dest_node"], as_index=False)
        .agg(
            Supply_Qty=("supply_qty", "sum"),
            Demand_Qty=("demand_qty", "sum"),
            Shortage_Qty=("shortage_qty", "sum"),
            Avg_Fill_Rate=("fill_rate_pct", "mean"),
        )
        .sort_values("Demand_Qty", ascending=False)
    )
    return x


def build_stress_queue(df):
    q = df[(df["stress_level"] != "Low") | (df["supply_status"].isin(["At Risk", "Watch"]))].copy()
    q = q.sort_values(["ai_score", "shortage_qty"], ascending=[False, False])
    return q


def render_stress_cards(df, top_n=5):
    for _, r in df.head(top_n).iterrows():
        st.markdown(
            f"""
            <div class="stress-card">
                <div class="stress-title">{r["account"]} · {r["sku_bundle"]}</div>
                <div class="stress-meta">
                    {r["market"]} · Status <b>{r["supply_status"]}</b> · Stress <b>{r["stress_level"]}</b> · AI <b>{int(r["ai_score"])}</b> · Confidence <b>{r["confidence"]}</b>
                </div>
                <div class="stress-body">
                    <b>Flow:</b> {r["source_node"]} → {r["dest_node"]}<br>
                    <b>Fill Rate:</b> {fmt_pct(r["fill_rate_pct"])} · <b>DOH:</b> {fmt_num(r["doh"])} · <b>Shortage:</b> {fmt_num(r["shortage_qty"])} units
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def resolution_actions(df):
    rows = []
    if df.empty:
        return pd.DataFrame(columns=["Account", "Action", "Priority", "Owner", "Reason"])

    for _, r in df.head(6).iterrows():
        if r["doh"] < 14:
            action = "Expedite replenishment / reallocate buffer stock"
            reason = "Low days of cover"
        elif r["shortage_qty"] > 40:
            action = "Rebalance inventory across nodes"
            reason = "Shortage pressure"
        elif r["fill_rate_pct"] < 90:
            action = "Prioritise service recovery and shipment release"
            reason = "Service level risk"
        else:
            action = "Monitor and hold contingency capacity"
            reason = "Moderate stress"

        rows.append(
            {
                "Account": r["account"],
                "Action": action,
                "Priority": "High" if r["stress_level"] == "High" else "Medium",
                "Owner": r["owner"],
                "Reason": reason,
            }
        )

    return pd.DataFrame(rows)


def supply_agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Supply Agent")
    st.caption("Turn service and stock pressure into actionable resolution decisions.")

    if df.empty:
        st.info("No supply flows in current view.")
    else:
        top = df.sort_values(["shortage_qty", "ai_score"], ascending=[False, False]).iloc[0]
        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Most critical flow in current view</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {top["market"]} · {top["sku_bundle"]} · Shortage {fmt_num(top["shortage_qty"])} · Fill {fmt_pct(top["fill_rate_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.selectbox(
            "Agent mode",
            ["CEO summary", "Resolution plan", "Supply risk note", "Cross-functional action note"],
            key="supply_agent_mode",
        )

        if st.button("Generate supply guidance", width="stretch", key="supply_agent_generate"):
            if mode == "CEO summary":
                lines = [
                    f"The most critical current supply flow is {top['account']} with shortage of {fmt_num(top['shortage_qty'])} units.",
                    "This page monitors service quality, days of cover, shortage pressure and node-level execution in one operating view.",
                    "The objective is not only visibility, but faster and more controlled service recovery.",
                ]
            elif mode == "Resolution plan":
                lines = [
                    f"Prioritise {top['account']} because it is combining low service with material shortage risk.",
                    "Check alternative source node, release constrained stock, and protect the most commercially critical bundles first.",
                    "Assign owner, lock action and follow the service recovery through the next cycle.",
                ]
            elif mode == "Supply risk note":
                lines = [
                    f"{top['account']} is showing service pressure on {top['sku_bundle']} with fill rate at {fmt_pct(top['fill_rate_pct'])}.",
                    "The current risk is customer service failure or delay to institutional execution.",
                    "Intervention should focus on recovery path, not only root-cause reporting.",
                ]
            else:
                lines = [
                    "Supply orchestration needs commercial, planning and project operations aligned on the same stress queue.",
                    "The page converts fragmented stock and service signals into one shared action system.",
                    "This allows the organisation to move from reactive firefighting to governed service recovery.",
                ]

            st.markdown("#### Output")
            for line in lines:
                st.write(f"- {line}")

        st.markdown("#### Suggested prompts")
        st.write("- Summarize the top 3 supply risks.")
        st.write("- Which flows need intervention first?")
        st.write("- Generate a cross-functional service recovery note.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "inst_supply_df" not in st.session_state:
    st.session_state.inst_supply_df = create_supply_df()

supply_df = st.session_state.inst_supply_df.copy()

# =========================================================
# Hero
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Hunting · Institutional Supply Orchestration</div>
        <div class="hero-title">Supply Service Command Layer</div>
        <div class="hero-sub">
            Track institutional supply flows across source nodes, project buffers, transit and delivery risk.
            This is where service, stock health and shortage recovery are governed in one operating cockpit.
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
st.markdown('<div class="section-title">Flow and Service Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Keep supply controls inside the page so the left panel stays a clean application navigation shell.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.2, 0.9])

with c1:
    market_filter = st.selectbox("Market", ["All"] + sorted(supply_df["market"].unique().tolist()), key="sup_market_filter")
with c2:
    status_filter = st.selectbox("Supply Status", ["All"] + sorted(supply_df["supply_status"].unique().tolist()), key="sup_status_filter")
with c3:
    stress_filter = st.selectbox("Stress Level", ["All"] + sorted(supply_df["stress_level"].unique().tolist()), key="sup_stress_filter")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="sup_refresh")

if market_filter != "All":
    supply_df = supply_df[supply_df["market"] == market_filter]
if status_filter != "All":
    supply_df = supply_df[supply_df["supply_status"] == status_filter]
if stress_filter != "All":
    supply_df = supply_df[supply_df["stress_level"] == stress_filter]

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Fill Rate Visibility</span>
        <span class="signal-chip">DOH Monitoring</span>
        <span class="signal-chip">Shortage Command</span>
        <span class="signal-chip">Node-to-Node Flow Control</span>
        <span class="signal-chip">Service Recovery Queue</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
avg_fill = supply_df["fill_rate_pct"].mean() if not supply_df.empty else 0
avg_doh = supply_df["doh"].mean() if not supply_df.empty else 0
total_supply = supply_df["supply_qty"].sum() if not supply_df.empty else 0
total_demand = supply_df["demand_qty"].sum() if not supply_df.empty else 0
total_shortage = supply_df["shortage_qty"].sum() if not supply_df.empty else 0
at_risk_flows = int((supply_df["stress_level"] == "High").sum()) if not supply_df.empty else 0
service_watch = int((supply_df["fill_rate_pct"] < 93).sum()) if not supply_df.empty else 0
critical_accounts = supply_df[supply_df["shortage_qty"] > 40]["account"].nunique() if not supply_df.empty else 0

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
with k1:
    st.metric("Avg Fill Rate", fmt_pct(avg_fill))
with k2:
    st.metric("Avg DOH", fmt_num(avg_doh))
with k3:
    st.metric("Supply Qty", fmt_num(total_supply))
with k4:
    st.metric("Demand Qty", fmt_num(total_demand))
with k5:
    st.metric("Shortage Qty", fmt_num(total_shortage))
with k6:
    st.metric("High-Stress Flows", at_risk_flows)
with k7:
    st.metric("Service Watch", service_watch)
with k8:
    st.metric("Critical Accounts", int(critical_accounts))

st.markdown("")

# =========================================================
# Main command area
# =========================================================
left, middle, right = st.columns([1.45, 1.1, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Service Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Fill, Cover and Shortage View</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A single view of whether institutional supply is healthy, tightening or moving into service recovery mode.</div>',
        unsafe_allow_html=True,
    )

    trend_df = build_supply_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Fill Rate"], mode="lines+markers", name="Fill Rate"))
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["DOH"], mode="lines+markers", name="DOH"))
    fig.add_trace(go.Scatter(x=trend_df["week"], y=trend_df["Shortage Qty"], mode="lines+markers", name="Shortage Qty"))
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=45, b=10), title="Weekly Fill / DOH / Shortage Trend")
    st.plotly_chart(fig, width="stretch", key="sup_trend")

    node_df = build_node_view(supply_df)
    st.dataframe(node_df, width="stretch", height=210, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Flow Pressure</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Supply Risk by Account</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Compare accounts by service quality, shortage pressure and days of cover to identify the flows that need action.</div>',
        unsafe_allow_html=True,
    )

    if supply_df.empty:
        st.info("No flows match the filters.")
    else:
        bubble_df = supply_df.copy()
        fig2 = px.scatter(
            bubble_df,
            x="doh",
            y="fill_rate_pct",
            size="shortage_qty",
            color="market",
            hover_name="account",
            title="DOH vs Fill Rate · Bubble = Shortage Qty",
        )
        fig2.update_layout(height=350, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig2, width="stretch", key="sup_bubble")

        compare_df = supply_df[["account", "market", "sku_bundle", "supply_status", "fill_rate_pct", "doh", "shortage_qty", "stress_level"]].copy()
        compare_df.columns = ["Account", "Market", "SKU Bundle", "Status", "Fill Rate %", "DOH", "Shortage Qty", "Stress"]
        st.dataframe(compare_df, width="stretch", height=210, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    supply_agent_panel(supply_df)

st.markdown("")

# =========================================================
# Stress queue / actions / selected flow
# =========================================================
stress_df = build_stress_queue(supply_df) if not supply_df.empty else pd.DataFrame()
resolution_df = resolution_actions(stress_df)

b1, b2, b3 = st.columns([1.15, 1.05, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Stress Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What Needs Immediate Recovery</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">These are the flows where service, stock or shortage conditions require focused intervention now.</div>',
        unsafe_allow_html=True,
    )

    if stress_df.empty:
        st.success("No meaningful supply stress in current view.")
    else:
        render_stress_cards(stress_df, top_n=4)

    st.button("Review stress queue", width="stretch", key="review_supply_queue")
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Resolution Actions</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next Best Supply Moves</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A decision-oriented action queue for planning, project operations and supply leadership.</div>',
        unsafe_allow_html=True,
    )

    if resolution_df.empty:
        st.info("No resolution actions.")
    else:
        st.dataframe(resolution_df, width="stretch", height=320, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Flow Command</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Supply Flow</div>', unsafe_allow_html=True)

    if supply_df.empty:
        st.info("No flow selected.")
    else:
        selected_account = st.selectbox("Account", sorted(supply_df["account"].unique().tolist()), key="selected_supply_account")
        row = supply_df[supply_df["account"] == selected_account].iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight">
                <div class="small-note">Flow Snapshot</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{row["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {row["market"]} · {row["sku_bundle"]} · Fill {fmt_pct(row["fill_rate_pct"])} · DOH {fmt_num(row["doh"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Current flow")
        st.write(f"- {row['source_node']} → {row['dest_node']}")
        st.markdown("#### Current condition")
        st.write(f"- Status: {row['supply_status']}")
        st.write(f"- Shortage Qty: {fmt_num(row['shortage_qty'])}")
        st.write(f"- Stress Level: {row['stress_level']}")
        st.markdown("#### Recommendation")
        if row["stress_level"] == "High":
            st.write("- Immediate intervention recommended: recover service and rebalance constrained stock.")
        elif row["stress_level"] == "Medium":
            st.write("- Monitor closely and hold contingency recovery options.")
        else:
            st.write("- Flow is stable. Keep monitoring for early stress movement.")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Bottom action layer
# =========================================================
c1, c2, c3, c4 = st.columns([1, 1, 1, 1.1])

with c1:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Service Protection</div>', unsafe_allow_html=True)
    st.write("- Track fill rate deterioration before the account feels it.")
    st.write("- Focus on the highest-commercial-impact flows first.")
    st.write("- Use the page to protect institutional service levels proactively.")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Shortage Recovery</div>', unsafe_allow_html=True)
    st.write("- Identify flows where shortage is becoming material.")
    st.write("- Reallocate, expedite or buffer based on stress level.")
    st.write("- Keep recovery visible to both commercial and supply teams.")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Cross-Node Orchestration</div>', unsafe_allow_html=True)
    st.write("- Move from one-node thinking to end-to-end flow thinking.")
    st.write("- Use the page to compare source, destination and transit risk.")
    st.write("- Turn multi-point complexity into one action system.")
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### Recovery Note Generator")
    st.caption("Generate a short note for a supply recovery discussion.")

    account_name = st.text_input("Account", supply_df.iloc[0]["account"] if not supply_df.empty else "ABC Account", key="sup_note_account")
    note = f"""Subject: Supply recovery review for {account_name}

This account should be reviewed for current fill rate, days of cover, shortage exposure and recovery path across source and destination nodes.

Recommended next step:
1. Validate current stock and in-transit position
2. Confirm shortage mitigation path
3. Assign owner and closure date for service recovery
"""
    st.text_area("Generated note", note, height=220, key="sup_generated_note")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Demo tip: show this page after Revenue Intelligence to prove that institutional growth is backed by service reliability, not just commercial ambition.")