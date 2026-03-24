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
def save_csv(df, name):
    df.to_csv(os.path.join(OUT, name), index=False)


def load_csv(name):
    p = os.path.join(OUT, name)
    if os.path.exists(p):
        try:
            return pd.read_csv(p)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


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


def generate_projects(country):
    cities = {
        "India": ["Mumbai", "Delhi", "Bengaluru", "Hyderabad"],
        "UAE": ["Dubai", "Abu Dhabi"],
        "Saudi Arabia": ["Riyadh", "Jeddah"],
        "Indonesia": ["Jakarta", "Surabaya"],
        "Vietnam": ["Ho Chi Minh City", "Hanoi"],
        "Singapore": ["Singapore"],
    }

    cluster_types = [
        "Dense Urban",
        "Institutional Cluster",
        "General Trade",
        "Growth Fringe",
        "Mixed Retail",
    ]

    recommended_models = [
        "New Distributor",
        "Expand Existing",
        "Specialized Partner",
    ]

    rows = []
    for i in range(12):
        city = np.random.choice(cities.get(country, ["City A"]))
        outlet_potential = int(np.random.randint(120, 680))
        covered = int(outlet_potential * np.random.uniform(0.45, 0.82))
        whitespace = outlet_potential - covered
        ai_score = int(np.random.randint(74, 95))
        rows.append(
            {
                "project_id": f"MM-{country[:2].upper()}-{i+1}",
                "project_name": f"{city} Development Pocket {i+1}",
                "country": country,
                "city": city,
                "cluster_type": np.random.choice(cluster_types),
                "recommended_model": np.random.choice(recommended_models, p=[0.45, 0.4, 0.15]),
                "outlet_potential": outlet_potential,
                "covered_outlets": covered,
                "whitespace_outlets": whitespace,
                "coverage_pct": round(covered / outlet_potential * 100, 1),
                "value_headroom_musd": round(np.random.uniform(4.0, 22.0), 1),
                "confidence": round(np.random.uniform(0.62, 0.96), 2),
                "ai_score": ai_score,
                "priority": "High" if ai_score >= 88 else "Medium" if ai_score >= 80 else "Watch",
            }
        )
    return pd.DataFrame(rows)


def add_coordinates(df):
    coords = {
        "Mumbai": (19.07, 72.87),
        "Delhi": (28.61, 77.21),
        "Bengaluru": (12.97, 77.59),
        "Hyderabad": (17.38, 78.48),
        "Dubai": (25.20, 55.27),
        "Abu Dhabi": (24.45, 54.37),
        "Riyadh": (24.71, 46.67),
        "Jeddah": (21.49, 39.19),
        "Jakarta": (-6.20, 106.85),
        "Surabaya": (-7.25, 112.75),
        "Ho Chi Minh City": (10.82, 106.63),
        "Hanoi": (21.03, 105.85),
        "Singapore": (1.35, 103.82),
    }
    x = df.copy()
    x["lat"] = x["city"].map(lambda c: coords.get(c, (None, None))[0])
    x["lon"] = x["city"].map(lambda c: coords.get(c, (None, None))[1])
    return x


def build_pipeline(df):
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "activation_id": f"ACT-{r['project_id']}",
                "micromarket": r["project_name"],
                "country": r["country"],
                "model": r["recommended_model"],
                "headroom_musd": round(float(r["value_headroom_musd"]), 1),
                "priority": r["priority"],
                "owner": random.choice(["RTM Lead", "Regional Sales", "Distributor Development"]),
                "status": random.choice(["Queued", "Ready", "Review"]),
            }
        )
    return pd.DataFrame(rows)


def render_queue_cards(df, top_n=4):
    for _, r in df.head(top_n).iterrows():
        st.markdown(
            f"""
            <div class="queue-card">
                <div class="queue-title">{r["project_name"]}</div>
                <div class="queue-meta">
                    {r["country"]} · {r["cluster_type"]} · Model <b>{r["recommended_model"]}</b> · AI <b>{int(r["ai_score"])}</b> · Priority <b>{r["priority"]}</b>
                </div>
                <div class="queue-body">
                    <b>Outlet Potential:</b> {int(r["outlet_potential"])} ·
                    <b>Covered:</b> {int(r["covered_outlets"])} ·
                    <b>Whitespace:</b> {int(r["whitespace_outlets"])}<br>
                    <b>Coverage:</b> {fmt_pct(r["coverage_pct"])} ·
                    <b>Value Headroom:</b> ${fmt_money(r["value_headroom_musd"])}M
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_country_summary(df):
    if df.empty:
        return pd.DataFrame()
    x = (
        df.groupby("country", as_index=False)
        .agg(
            Pockets=("project_id", "count"),
            Outlet_Potential=("outlet_potential", "sum"),
            White_Space=("whitespace_outlets", "sum"),
            Value_Headroom=("value_headroom_musd", "sum"),
        )
        .sort_values("Value_Headroom", ascending=False)
    )
    return x


def agent_panel(projects):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Agent")
    st.caption("Simple distributor development summary and next actions.")

    if projects.empty:
        st.info("Generate micromarket pockets to activate the agent.")
    else:
        total = len(projects)
        value = projects["value_headroom_musd"].sum()
        top_city = (
            projects.groupby("city", as_index=False)["value_headroom_musd"]
            .sum()
            .sort_values("value_headroom_musd", ascending=False)
            .iloc[0]["city"]
        )

        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Current development summary</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top_city}</div>
                <div class="small-note" style="margin-top:8px;">
                    Pockets <b>{total}</b> · Value Headroom <b>${fmt_money(value)}M</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("**Recommended actions**")
        st.write("- Prioritize the top micromarkets first")
        st.write("- Decide: new distributor vs expand existing")
        st.write("- Assign owner and activation date")
        st.write("- Push shortlisted pockets into activation queue")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "dd_projects" not in st.session_state:
    st.session_state.dd_projects = pd.DataFrame()

if "dd_pipeline" not in st.session_state:
    st.session_state.dd_pipeline = pd.DataFrame()


# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Farming · Distributor Development</div>
        <div class="hero-title">Micromarket Development Studio</div>
        <div class="hero-sub">
            Keep this page simple: identify whitespace pockets, see them on a map, review the top development opportunities,
            and push them into an activation queue.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Development Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Generate Development Pockets</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">A lighter version of the page with the earlier radar + map feel retained.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns([1.05, 1.2, 0.8])

with c1:
    country = st.selectbox(
        "Market",
        ["India", "UAE", "Saudi Arabia", "Indonesia", "Vietnam", "Singapore"],
        key="dd_country",
    )

with c2:
    focus = st.selectbox(
        "Focus",
        ["All Pockets", "High Priority Only", "New Distributor", "Expand Existing"],
        key="dd_focus",
    )

with c3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    gen_projects = st.button("Generate Pockets", width="stretch", key="dd_generate")

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Project Radar</span>
        <span class="signal-chip">Opportunity Map</span>
        <span class="signal-chip">Activation Queue</span>
        <span class="signal-chip">Outreach Note</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if gen_projects or st.session_state.dd_projects.empty:
    projects = generate_projects(country)
    save_csv(projects, "distributor_dev_projects.csv")
    st.session_state.dd_projects = projects
else:
    projects = st.session_state.dd_projects.copy()

if not projects.empty:
    if focus == "High Priority Only":
        projects = projects[projects["priority"] == "High"]
    elif focus == "New Distributor":
        projects = projects[projects["recommended_model"] == "New Distributor"]
    elif focus == "Expand Existing":
        projects = projects[projects["recommended_model"] == "Expand Existing"]

# =========================================================
# KPI strip
# =========================================================
detected = int(len(projects)) if not projects.empty else 0
whitespace = int(projects["whitespace_outlets"].sum()) if not projects.empty else 0
headroom = float(projects["value_headroom_musd"].sum()) if not projects.empty else 0
qualified = int((projects["ai_score"] >= 84).sum()) if not projects.empty else 0
coverage = (
    projects["covered_outlets"].sum() / projects["outlet_potential"].sum() * 100
    if not projects.empty and projects["outlet_potential"].sum() > 0 else 0
)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Pockets Detected", detected)
with k2:
    st.metric("AI Qualified", qualified)
with k3:
    st.metric("Whitespace Outlets", whitespace)
with k4:
    st.metric("Value Headroom ($M)", fmt_money(headroom))
with k5:
    st.metric("Current Coverage", fmt_pct(coverage))

st.markdown("")

# =========================================================
# Radar + map + agent
# =========================================================
col1, col2, col3 = st.columns([1.05, 1.2, 0.95])

with col1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Project Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Development Pockets</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Keep the simple radar table from the earlier page.</div>',
        unsafe_allow_html=True,
    )

    if projects.empty:
        st.info("No pockets available.")
    else:
        radar_view = projects[
            [
                "project_name",
                "city",
                "cluster_type",
                "recommended_model",
                "outlet_potential",
                "whitespace_outlets",
                "value_headroom_musd",
                "priority",
            ]
        ].copy()
        radar_view.columns = [
            "Pocket",
            "City",
            "Cluster",
            "Model",
            "Potential",
            "Whitespace",
            "Headroom ($M)",
            "Priority",
        ]
        st.dataframe(radar_view, width="stretch", height=340, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Opportunity Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Geographic Development View</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Bring back the earlier map feel, but cleaner.</div>',
        unsafe_allow_html=True,
    )

    if projects.empty:
        st.info("Generate pockets to populate the map.")
    else:
        map_df = add_coordinates(projects).dropna(subset=["lat", "lon"])
        if map_df.empty:
            st.warning("No coordinates available for selected market.")
        else:
            fig = px.scatter_mapbox(
                map_df,
                lat="lat",
                lon="lon",
                size="value_headroom_musd",
                color="priority",
                hover_name="project_name",
                hover_data=["city", "recommended_model", "whitespace_outlets", "coverage_pct"],
                zoom=3,
            )
            fig.update_layout(
                mapbox_style="open-street-map",
                height=380,
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig, width="stretch", key="dd_map")

    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    agent_panel(projects)

st.markdown("")

# =========================================================
# Simple chart + queue
# =========================================================
left, right = st.columns([1.12, 1.0])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Country Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Whitespace vs Headroom</div>', unsafe_allow_html=True)

    if projects.empty:
        st.info("No data available.")
    else:
        summary = build_country_summary(projects)
        fig2 = px.bar(
            summary,
            x="country",
            y="Value_Headroom",
            title="Value Headroom by Country",
        )
        fig2.update_layout(height=310, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig2, width="stretch", key="dd_country_bar")
        st.dataframe(summary, width="stretch", height=180, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Development Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top Activation Candidates</div>', unsafe_allow_html=True)

    if projects.empty:
        st.info("No queue items.")
    else:
        queue_df = projects.sort_values(["ai_score", "value_headroom_musd"], ascending=[False, False]).copy()
        render_queue_cards(queue_df, top_n=4)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Activation queue + outreach
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Activation Queue</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Push Pockets into Execution</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Simple and practical: turn shortlisted development pockets into an activation queue.</div>',
    unsafe_allow_html=True,
)

if not projects.empty:
    if st.button("Create Activation Queue", key="dd_create_pipeline"):
        pipe = build_pipeline(projects.head(6))
        save_csv(pipe, "distributor_dev_activation_queue.csv")
        st.session_state.dd_pipeline = pipe

pipe = st.session_state.dd_pipeline.copy()
if pipe.empty:
    pipe = load_csv("distributor_dev_activation_queue.csv")

if not pipe.empty:
    st.dataframe(pipe, width="stretch", height=220, hide_index=True)
else:
    st.info("No activation queue yet. Generate pockets and click Create Activation Queue.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">SYDIAI Outreach Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Distributor Development Note</div>', unsafe_allow_html=True)

name = st.text_input("Contact name", "John", key="dd_contact_name")
company = st.text_input("Distributor / Partner", "ABC Distributors", key="dd_company_name")

msg = f"""Hi {name},

We have identified a high-potential development pocket and wanted to connect.

Our platform helps teams identify whitespace, evaluate distributor models, and activate territories with sharper commercial discipline.

Would you be open to a short discussion?

Regards
"""

st.text_area("Generated message", msg, height=160, key="dd_generated_message")
st.markdown("</div>", unsafe_allow_html=True)