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


def create_farming_df():
    rows = [
        ["DIST-001", "Alpha Distributors", "Saudi Arabia", "Riyadh North", 18.4, 4.2, 22.8, 91.2, 17.0, 88, "Healthy"],
        ["DIST-002", "Jeddah Trading", "Saudi Arabia", "Jeddah West", 14.6, 3.1, 21.2, 89.4, 14.0, 84, "Watch"],
        ["DIST-003", "Dubai Channel House", "UAE", "Dubai Outer", 12.8, 2.9, 22.7, 92.4, 18.0, 87, "Healthy"],
        ["DIST-004", "Abu Dhabi Supply Co", "UAE", "Abu Dhabi Fringe", 10.2, 2.1, 20.6, 88.6, 13.0, 81, "Watch"],
        ["DIST-005", "Jakarta Prime", "Indonesia", "Jakarta East", 19.7, 4.8, 24.4, 93.1, 21.0, 90, "Healthy"],
        ["DIST-006", "Surabaya Network", "Indonesia", "Surabaya South", 11.4, 2.3, 20.2, 87.8, 11.0, 78, "At Risk"],
        ["DIST-007", "Ho Chi Minh Trade", "Vietnam", "Ho Chi Minh Periphery", 9.6, 1.9, 19.8, 86.9, 10.0, 77, "At Risk"],
        ["DIST-008", "Hanoi Market Link", "Vietnam", "Hanoi South", 8.8, 1.7, 19.3, 88.1, 12.0, 79, "Watch"],
        ["DIST-009", "Singapore Channel Partners", "Singapore", "Industrial Belt", 6.5, 1.6, 24.6, 94.2, 23.0, 89, "Healthy"],
        ["DIST-010", "Mumbai Edge Distribution", "India", "Mumbai Peripheral", 21.2, 5.0, 23.6, 92.6, 19.0, 91, "Healthy"],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "distributor_id", "distributor", "country", "territory",
            "revenue_musd", "profit_musd", "gm_pct", "service_pct",
            "growth_pct", "ai_score", "status"
        ],
    )
    df["confidence"] = df["ai_score"].apply(confidence_band)
    df["inventory_doh"] = np.random.randint(10, 28, len(df))
    df["collection_pct"] = np.round(np.random.uniform(86, 98, len(df)), 1)
    df["active_outlets"] = np.random.randint(320, 1800, len(df))
    df["fill_rate_pct"] = np.round(np.random.uniform(87, 97, len(df)), 1)
    df["owner"] = np.random.choice(
        ["Regional Sales", "Distributor Manager", "RTM Lead", "Commercial Ops"],
        size=len(df),
    )
    return df


def build_trend():
    periods = [f"M{k}" for k in range(1, 13)]
    revenue = np.array([8.6, 8.9, 9.2, 9.4, 9.7, 10.1, 10.4, 10.6, 10.9, 11.3, 11.6, 12.0])
    profit = np.array([1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.35, 2.4, 2.5, 2.6, 2.75, 2.9])
    service = np.array([89.1, 89.6, 90.0, 90.4, 90.9, 91.5, 91.8, 92.1, 92.6, 93.0, 93.3, 93.8])
    return pd.DataFrame({"period": periods, "Revenue": revenue, "Profit": profit, "Service": service})


def build_stack_summary(df):
    if df.empty:
        return pd.DataFrame()

    develop = df.groupby("country", as_index=False)["active_outlets"].sum().rename(columns={"active_outlets": "Develop"})
    service = df.groupby("country", as_index=False)["service_pct"].mean().rename(columns={"service_pct": "Service"})
    inventory = df.groupby("country", as_index=False)["inventory_doh"].mean().rename(columns={"inventory_doh": "Inventory"})
    profit = df.groupby("country", as_index=False)["profit_musd"].sum().rename(columns={"profit_musd": "Profit"})

    x = develop.merge(service, on="country").merge(inventory, on="country").merge(profit, on="country")
    return x


def build_health_radar(row):
    return {
        "Growth": min(max(float(row["growth_pct"]), 0), 100),
        "Service": min(max(float(row["service_pct"]), 0), 100),
        "Inventory": min(max(float(row["inventory_doh"]) * 4, 0), 100),
        "Profit": min(max(float(row["gm_pct"]) * 3.5, 0), 100),
        "Collections": min(max(float(row["collection_pct"]), 0), 100),
    }


def radar_chart(scores):
    labels = list(scores.keys())
    vals = list(scores.values())
    vals = vals + [vals[0]]
    labels = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals, theta=labels, fill="toself", name="Health"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=330,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


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
                    <b>Revenue:</b> ${fmt_money(r["revenue_musd"])}M ·
                    <b>Profit:</b> ${fmt_money(r["profit_musd"])}M ·
                    <b>Service:</b> {fmt_pct(r["service_pct"])}<br>
                    <b>Growth:</b> {fmt_pct(r["growth_pct"])} ·
                    <b>Inventory DOH:</b> {fmt_num(r["inventory_doh"])} ·
                    <b>Fill Rate:</b> {fmt_pct(r["fill_rate_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_action_queue(df):
    rows = []
    for _, r in df.sort_values(["ai_score", "revenue_musd"], ascending=[False, False]).head(6).iterrows():
        if r["status"] == "At Risk":
            action = "Immediate distributor recovery review"
        elif r["service_pct"] < 90:
            action = "Service correction and stock review"
        elif r["growth_pct"] < 13:
            action = "Growth activation and outlet expansion"
        else:
            action = "Scale current model and protect performance"

        rows.append(
            {
                "Distributor": r["distributor"],
                "Country": r["country"],
                "Priority": "High" if r["status"] == "At Risk" else "Medium",
                "Action": action,
                "Owner": r["owner"],
            }
        )
    return pd.DataFrame(rows)


def agent_panel(df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Agent")
    st.caption("Simple distributor performance summary and next actions.")

    if df.empty:
        st.info("No distributors in current view.")
    else:
        top = df.sort_values(["revenue_musd", "ai_score"], ascending=[False, False]).iloc[0]
        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Top distributor in view</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["distributor"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    Revenue <b>${fmt_money(top["revenue_musd"])}M</b> · Profit <b>${fmt_money(top["profit_musd"])}M</b> · Service <b>{fmt_pct(top["service_pct"])}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("**Recommended actions**")
        st.write("- Review top and at-risk distributors together")
        st.write("- Use the stack overview to identify weak pillar")
        st.write("- Move from reporting into owner-led actions")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "farming_df" not in st.session_state:
    st.session_state.farming_df = create_farming_df()

farm_df = st.session_state.farming_df.copy()

# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Farming · Cockpit</div>
        <div class="hero-title">Distributor Performance Command Centre</div>
        <div class="hero-sub">
            A single operating view across distributor growth, service, inventory and profit.
            Keep it simple, premium and action-oriented.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Cockpit Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Distributor Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Filters stay inside the page so the left panel remains a clean navigation shell.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.05, 1.1, 1.1, 0.8])

with c1:
    country_filter = st.selectbox("Country", ["All"] + sorted(farm_df["country"].unique().tolist()), key="farm_country")
with c2:
    status_filter = st.selectbox("Status", ["All"] + sorted(farm_df["status"].unique().tolist()), key="farm_status")
with c3:
    focus_filter = st.selectbox("Focus", ["All", "Top Revenue", "At Risk", "High Growth"], key="farm_focus")
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("Refresh View", width="stretch", key="farm_refresh")

if country_filter != "All":
    farm_df = farm_df[farm_df["country"] == country_filter]
if status_filter != "All":
    farm_df = farm_df[farm_df["status"] == status_filter]
if focus_filter == "Top Revenue":
    farm_df = farm_df.sort_values("revenue_musd", ascending=False).head(6)
elif focus_filter == "At Risk":
    farm_df = farm_df[farm_df["status"] == "At Risk"]
elif focus_filter == "High Growth":
    farm_df = farm_df.sort_values("growth_pct", ascending=False).head(6)

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Executive Snapshot</span>
        <span class="signal-chip">Commercial Stack</span>
        <span class="signal-chip">Health Radar</span>
        <span class="signal-chip">Action Queue</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
revenue = farm_df["revenue_musd"].sum() if not farm_df.empty else 0
profit = farm_df["profit_musd"].sum() if not farm_df.empty else 0
gm = (profit / revenue * 100) if revenue > 0 else 0
service = farm_df["service_pct"].mean() if not farm_df.empty else 0
growth = farm_df["growth_pct"].mean() if not farm_df.empty else 0
doh = farm_df["inventory_doh"].mean() if not farm_df.empty else 0
at_risk = int((farm_df["status"] == "At Risk").sum()) if not farm_df.empty else 0

k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
with k1:
    st.metric("Revenue ($M)", fmt_money(revenue))
with k2:
    st.metric("Profit ($M)", fmt_money(profit))
with k3:
    st.metric("Profit %", fmt_pct(gm))
with k4:
    st.metric("Service %", fmt_pct(service))
with k5:
    st.metric("Growth %", fmt_pct(growth))
with k6:
    st.metric("Inventory DOH", fmt_num(doh))
with k7:
    st.metric("At-Risk Distributors", at_risk)

st.markdown("")

# =========================================================
# Main layout
# =========================================================
left, middle, right = st.columns([1.35, 1.15, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Executive Performance Snapshot</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Revenue, Profit and Service Trend</div>', unsafe_allow_html=True)

    trend = build_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Revenue"], mode="lines+markers", name="Revenue"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Profit"], mode="lines+markers", name="Profit"))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["Service"], mode="lines+markers", name="Service"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=35, b=10))
    st.plotly_chart(fig, width="stretch", key="farm_trend")
    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Commercial Stack Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Develop · Service · Inventory · Profit</div>', unsafe_allow_html=True)

    stack_df = build_stack_summary(farm_df)
    if stack_df.empty:
        st.info("No data available.")
    else:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Develop", x=stack_df["country"], y=stack_df["Develop"]))
        fig2.add_trace(go.Bar(name="Service", x=stack_df["country"], y=stack_df["Service"]))
        fig2.add_trace(go.Bar(name="Inventory", x=stack_df["country"], y=stack_df["Inventory"]))
        fig2.add_trace(go.Bar(name="Profit", x=stack_df["country"], y=stack_df["Profit"]))
        fig2.update_layout(barmode="group", height=340, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig2, width="stretch", key="farm_stack")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    agent_panel(farm_df)

st.markdown("")

# =========================================================
# Radar + queue + selected distributor
# =========================================================
b1, b2, b3 = st.columns([1.0, 1.15, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Health Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Distributor</div>', unsafe_allow_html=True)

    if farm_df.empty:
        st.info("No distributor available.")
    else:
        selected = st.selectbox("Distributor", sorted(farm_df["distributor"].unique().tolist()), key="farm_selected")
        row = farm_df[farm_df["distributor"] == selected].iloc[0]
        scores = build_health_radar(row)
        st.plotly_chart(radar_chart(scores), width="stretch", key="farm_radar")
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Action Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top Distributor Priorities</div>', unsafe_allow_html=True)

    if farm_df.empty:
        st.info("No priority items.")
    else:
        queue_df = farm_df.sort_values(["ai_score", "revenue_musd"], ascending=[False, False]).copy()
        render_queue_cards(queue_df, top_n=4)

    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Distributor Command</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Snapshot</div>', unsafe_allow_html=True)

    if farm_df.empty:
        st.info("No distributor selected.")
    else:
        row = farm_df[farm_df["distributor"] == selected].iloc[0]
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
        st.write(f"- Revenue: ${fmt_money(row['revenue_musd'])}M")
        st.write(f"- Profit: ${fmt_money(row['profit_musd'])}M")
        st.write(f"- Service: {fmt_pct(row['service_pct'])}")
        st.write(f"- Growth: {fmt_pct(row['growth_pct'])}")
        st.write(f"- Collection: {fmt_pct(row['collection_pct'])}")
        st.write(f"- Active Outlets: {fmt_num(row['active_outlets'])}")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Bottom actions
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Execution Layer</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Recommended Next Moves</div>', unsafe_allow_html=True)

actions = build_action_queue(farm_df)
if actions.empty:
    st.info("No actions available.")
else:
    st.dataframe(actions, width="stretch", height=220, hide_index=True)

st.markdown("</div>", unsafe_allow_html=True)