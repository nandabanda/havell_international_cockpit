import os
import time
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
# Page config helpers
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

        .feed-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 12px 12px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.72);
        }

        .feed-title {
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
            font-size: 0.98rem;
        }

        .feed-meta {
            color: #64748b;
            font-size: 0.83rem;
            margin-bottom: 6px;
        }

        .feed-body {
            color: #334155;
            font-size: 0.9rem;
            line-height: 1.35rem;
        }

        .action-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 18px;
            padding: 14px;
            background: rgba(255,255,255,0.72);
            min-height: 210px;
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
def load_csv(name):
    p = os.path.join(OUT, name)
    if os.path.exists(p):
        try:
            return pd.read_csv(p)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_csv(df, name):
    df.to_csv(os.path.join(OUT, name), index=False)


def fmt_money(x):
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


def mock_discovery_feed(source_option, seed_key="default"):
    random.seed(seed_key)

    rows = []

    linkedin_entities = [
        ("Tata Projects", "Leadership hiring and project mobilisation posts"),
        ("L&T Construction", "Major EPC capability expansion"),
        ("Adani Infra", "Infra leadership activity and hiring"),
        ("Jakson Solar", "Solar manufacturing and EPC momentum"),
        ("Shapoorji Pallonji", "Execution scale-up and institutional visibility"),
    ]

    website_entities = [
        ("Company Website", "Press release on expansion / launch"),
        ("Investor Page", "New capacity or market entry update"),
        ("Careers Page", "Sharp rise in hiring for delivery roles"),
        ("Newsroom", "Project award or alliance announcement"),
    ]

    procurement_entities = [
        ("Government Tender", "Electrical / infra procurement notice"),
        ("Procurement Portal", "Commercial bid invitation published"),
        ("Institutional RFP", "Specification-led sourcing program detected"),
        ("Public Works", "Project tender with technical fit"),
    ]

    countries = ["UAE", "Saudi Arabia", "India", "Indonesia", "Vietnam", "Singapore"]
    sectors = ["Infrastructure", "Energy", "Industrial", "Real Estate", "Smart City"]

    if source_option == "LinkedIn":
        base_entities = linkedin_entities
        source_label = "LinkedIn Intelligence"
    elif source_option == "Web Crawling":
        base_entities = website_entities
        source_label = "Web Crawl Detection"
    elif source_option == "Country APIs":
        base_entities = [
            ("Market API", "Macro growth and infra allocation trend"),
            ("Trade API", "Import / project movement signal"),
            ("Country Signal", "Sector acceleration indicator"),
            ("Infra API", "Capital program visibility"),
        ]
        source_label = "Country API"
    elif source_option == "Procurement Portals":
        base_entities = procurement_entities
        source_label = "Procurement Portal"
    elif source_option == "OEM Signals":
        base_entities = [
            ("OEM Network", "Channel demand visibility"),
            ("Partner Signal", "Project-specification trigger"),
            ("Alliance Network", "Co-sell opportunity signal"),
            ("Dealer Network", "Downstream project activity"),
        ]
        source_label = "OEM Signal"
    else:
        base_entities = linkedin_entities + website_entities + procurement_entities
        source_label = "Multi-Source"

    for i in range(10):
        entity, signal = random.choice(base_entities)
        country = random.choice(countries)
        sector = random.choice(sectors)
        value = random.randint(20, 450)
        ai_score = random.randint(72, 96)
        rows.append(
            {
                "opportunity_id": f"OPP-{i+1:03d}",
                "Entity": entity,
                "Country": country,
                "Sector": sector,
                "Source": source_label,
                "Signal": signal,
                "Opportunity": f"{sector} opportunity in {country}",
                "Est Value ($M)": value,
                "AI Score": ai_score,
                "Confidence": confidence_band(ai_score),
                "Owner": random.choice(["Regional Sales", "Key Accounts", "BD Lead", "Channel Lead"]),
                "Status": random.choice(["Detected", "Qualified", "Ready for Pipeline"]),
            }
        )

    return pd.DataFrame(rows).sort_values("AI Score", ascending=False)


def build_source_mix(df):
    if df.empty:
        return pd.DataFrame(columns=["Source Bucket", "Count"])

    grouped = (
        df.groupby("Source", as_index=False)
        .size()
        .rename(columns={"size": "Count", "Source": "Source Bucket"})
        .sort_values("Count", ascending=False)
    )
    return grouped


def build_pipeline(df):
    if df.empty:
        return pd.DataFrame()

    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "opp_id": r["opportunity_id"],
                "account": r["Entity"],
                "project": r["Opportunity"],
                "country": r["Country"],
                "stage": random.choice(["Prospecting", "Qualified", "Solutioning"]),
                "value_musd": round(float(r["Est Value ($M)"]) * random.uniform(0.18, 0.42), 1),
                "confidence": r["Confidence"],
                "owner": r["Owner"],
                "priority": "High" if r["AI Score"] >= 88 else "Medium",
            }
        )
    return pd.DataFrame(rows)


def generate_projects(country):
    cities = {
        "India": ["Mumbai", "Delhi", "Bengaluru", "Hyderabad"],
        "UAE": ["Dubai", "Abu Dhabi"],
        "Saudi Arabia": ["Riyadh", "Jeddah"],
        "Indonesia": ["Jakarta", "Surabaya"],
        "Vietnam": ["Ho Chi Minh City", "Hanoi"],
        "Singapore": ["Singapore"],
    }

    rows = []
    city_list = cities.get(country, ["City A"])
    for i in range(12):
        city = np.random.choice(city_list)
        rows.append(
            {
                "project_id": f"PRJ-{country[:2].upper()}-{i+1}",
                "project_name": f"{city} Opportunity Cluster {i+1}",
                "country": country,
                "city": city,
                "segment": np.random.choice(["Commercial", "Residential", "Industrial", "Institutional"]),
                "stage": np.random.choice(["Planning", "Tender", "Construction", "Award"]),
                "est_value_musd": np.random.randint(10, 160),
                "confidence": round(np.random.uniform(0.62, 0.96), 2),
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

    df = df.copy()
    df["lat"] = df["city"].map(lambda x: coords.get(x, (None, None))[0])
    df["lon"] = df["city"].map(lambda x: coords.get(x, (None, None))[1])
    return df


def signal_trend_chart(df):
    if df.empty:
        return go.Figure()

    trend = (
        df.groupby(["Country"], as_index=False)["Est Value ($M)"]
        .sum()
        .sort_values("Est Value ($M)", ascending=False)
        .head(8)
    )
    fig = px.bar(
        trend,
        x="Country",
        y="Est Value ($M)",
        title="Detected Opportunity Value by Country",
    )
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=45, b=10))
    return fig


def source_mix_chart(df):
    sm = build_source_mix(df)
    fig = px.bar(sm, x="Source Bucket", y="Count", title="Source Mix")
    fig.update_layout(height=310, margin=dict(l=10, r=10, t=45, b=10))
    return fig


def render_feed_cards(df, top_n=5):
    for _, r in df.head(top_n).iterrows():
        st.markdown(
            f"""
            <div class="feed-card">
                <div class="feed-title">{r["Entity"]} · {r["Opportunity"]}</div>
                <div class="feed-meta">
                    {r["Source"]} · {r["Country"]} · {r["Sector"]} · AI Score <b>{r["AI Score"]}</b> · Confidence <b>{r["Confidence"]}</b>
                </div>
                <div class="feed-body">
                    <b>Signal:</b> {r["Signal"]}<br>
                    <b>Suggested next move:</b> Qualify account, identify stakeholder, and generate outreach from signal evidence.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def assistant_panel(feed_df, pipeline_df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Hunting Agent")
    st.caption("Turn external signals into structured pursuit actions.")

    if feed_df.empty:
        st.info("Generate opportunities to activate the agent.")
    else:
        top = feed_df.iloc[0]
        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Highest-value detected signal</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["Entity"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {top["Country"]} · {top["Sector"]} · ${fmt_money(top["Est Value ($M)"])}M potential · {top["Confidence"]} confidence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.selectbox(
            "Agent mode",
            ["CEO summary", "Pursuit strategy", "Outreach notes"],
            key="hunting_agent_mode",
        )

        if st.button("Generate agent output", width="stretch", key="hunting_agent_generate"):
            if mode == "CEO summary":
                lines = [
                    f"We detected {len(feed_df)} external opportunities from connected sources.",
                    f"The strongest current signal is {top['Entity']} in {top['Country']} with potential value of ${fmt_money(top['Est Value ($M)'])}M.",
                    "The cockpit converts weak external signals into a prioritised institutional pipeline with owner and next action.",
                ]
            elif mode == "Pursuit strategy":
                lines = [
                    f"Prioritise {top['Entity']} as the anchor account for immediate qualification.",
                    "Validate technical fit, identify decision-makers, and map likely procurement route.",
                    "Convert top 3 qualified signals into named pursuits with owner, outreach sequence and weekly review.",
                ]
            else:
                lines = [
                    f"Reference the detected signal around {top['Signal']}.",
                    "Open with relevance to current expansion or project activity rather than a generic sales pitch.",
                    "Position SYDIAI as an opportunity intelligence layer that can accelerate structured conversion.",
                ]

            st.markdown("#### Output")
            for line in lines:
                st.write(f"- {line}")

        st.markdown("#### Suggested prompts")
        st.write("- Summarize the top opportunities for leadership.")
        st.write("- Which 3 signals should become pipeline now?")
        st.write("- Generate a pursuit approach for the highest-value account.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "hunting_feed" not in st.session_state:
    st.session_state.hunting_feed = pd.DataFrame()

if "hunting_pipeline" not in st.session_state:
    st.session_state.hunting_pipeline = pd.DataFrame()

if "projects_radar" not in st.session_state:
    st.session_state.projects_radar = pd.DataFrame()


# =========================================================
# Hero
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Hunting Cockpit</div>
        <div class="hero-title">Opportunity Discovery Engine</div>
        <div class="hero-sub">
            Connect the cockpit to LinkedIn, websites, procurement sources, OEM signals and public market signals.
            Detect opportunities outside the CRM, qualify them with AI, generate outreach, and convert them into structured pipeline.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Discovery control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Connection Layer</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Simulate External Integrations</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">This is the strongest demo moment: connect to the outside world and show how signals become opportunities.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.1, 1.6, 1.25, 0.95])

with c1:
    source_option = st.selectbox(
        "Source",
        ["LinkedIn", "Web Crawling", "Country APIs", "Procurement Portals", "OEM Signals", "All Sources"],
        key="source_option",
    )

with c2:
    source_url = st.text_input(
        "Paste profile / website / source URL",
        value="https://www.linkedin.com/in/your-profile",
        key="source_url",
        placeholder="Paste LinkedIn profile, company page, website, portal or signal source",
    )

with c3:
    target_market = st.selectbox(
        "Target Market",
        ["India", "UAE", "Saudi Arabia", "Indonesia", "Vietnam", "Singapore"],
        key="target_market",
    )

with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    run_discovery = st.button("Generate Opportunities", width="stretch", key="run_discovery")

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">LinkedIn Profile / Company URL</span>
        <span class="signal-chip">Website / Press / Careers Crawl</span>
        <span class="signal-chip">Tender / Procurement Signals</span>
        <span class="signal-chip">Country / Market APIs</span>
        <span class="signal-chip">OEM / Partner Signals</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if run_discovery:
    with st.spinner("Scanning external signals and building qualified opportunities..."):
        time.sleep(1.6)
        feed_df = mock_discovery_feed(source_option, seed_key=f"{source_option}-{source_url}-{target_market}")
        feed_df["Target Market"] = target_market
        st.session_state.hunting_feed = feed_df

        projects_df = generate_projects(target_market)
        st.session_state.projects_radar = projects_df
        save_csv(projects_df, "projects_radar.csv")

        pipeline_df = build_pipeline(feed_df.head(6))
        st.session_state.hunting_pipeline = pipeline_df
        save_csv(pipeline_df, "hunting_pipeline.csv")

feed_df = st.session_state.hunting_feed.copy()
pipeline_df = st.session_state.hunting_pipeline.copy()
projects_df = st.session_state.projects_radar.copy()

# =========================================================
# KPI strip
# =========================================================
detected = int(len(feed_df)) if not feed_df.empty else 0
qualified = int((feed_df["AI Score"] >= 84).sum()) if not feed_df.empty else 0
active_sources = len(feed_df["Source"].unique()) if not feed_df.empty else 0
confidence = int(feed_df["AI Score"].mean()) if not feed_df.empty else 0
pipeline_value = float(pipeline_df["value_musd"].sum()) if not pipeline_df.empty else 0.0
ready_to_push = int((feed_df["Status"] == "Ready for Pipeline").sum()) if not feed_df.empty else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Signals Detected", detected)
with k2:
    st.metric("AI Qualified", qualified)
with k3:
    st.metric("Active Sources", active_sources)
with k4:
    st.metric("Discovery Confidence", f"{confidence}%")
with k5:
    st.metric("Pipeline Value ($M)", fmt_money(pipeline_value))
with k6:
    st.metric("Ready for Pipeline", ready_to_push)

st.markdown("")

# =========================================================
# Main command grid
# =========================================================
left, middle, right = st.columns([1.45, 1.1, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Opportunity Feed</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Live Institutional Opportunity Feed</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Signals become structured opportunities with source evidence, value, confidence and owner.</div>',
        unsafe_allow_html=True,
    )

    if feed_df.empty:
        st.info("Paste a source and click Generate Opportunities.")
    else:
        render_feed_cards(feed_df, top_n=5)

    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Signal Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Where Opportunity Is Coming From</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Use this to show that the cockpit is connected to the external world, not just internal CRM data.</div>',
        unsafe_allow_html=True,
    )

    if feed_df.empty:
        st.info("Generate opportunities to populate analytics.")
    else:
        st.plotly_chart(signal_trend_chart(feed_df), width="stretch", key="signal_trend_chart")
        st.plotly_chart(source_mix_chart(feed_df), width="stretch", key="source_mix_chart")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    assistant_panel(feed_df, pipeline_df)

st.markdown("")

# =========================================================
# Radar + map + pipeline
# =========================================================
r1, r2, r3 = st.columns([1.08, 1.3, 1.12])

with r1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Project Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Detected Market Clusters</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Simulated project radar by target market for institutional pursuit visibility.</div>',
        unsafe_allow_html=True,
    )

    if projects_df.empty:
        st.info("Generate opportunities to build project radar.")
    else:
        radar_view = projects_df[["project_name", "country", "city", "segment", "stage", "est_value_musd", "confidence"]].copy()
        radar_view.columns = ["Project", "Country", "City", "Segment", "Stage", "Value ($M)", "Confidence"]
        st.dataframe(radar_view, width="stretch", height=350, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with r2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Opportunity Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Geographic Signal View</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A visual way to show where project signals are clustering by city and value.</div>',
        unsafe_allow_html=True,
    )

    if projects_df.empty:
        st.info("Generate opportunities to populate the map.")
    else:
        map_df = add_coordinates(projects_df).dropna(subset=["lat", "lon"])
        if map_df.empty:
            st.warning("No map coordinates available for the selected market.")
        else:
            fig = px.scatter_mapbox(
                map_df,
                lat="lat",
                lon="lon",
                size="est_value_musd",
                hover_name="project_name",
                hover_data=["city", "segment", "stage", "confidence"],
                zoom=3,
            )
            fig.update_layout(
                mapbox_style="open-street-map",
                height=380,
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig, width="stretch", key="opportunity_map")

    st.markdown("</div>", unsafe_allow_html=True)

with r3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Pipeline Conversion</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Convert Signals to Pursuits</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Show how external signals are not left as insights — they are converted into actionable pipeline.</div>',
        unsafe_allow_html=True,
    )

    if pipeline_df.empty:
        st.info("Generate opportunities to create pipeline.")
    else:
        st.dataframe(pipeline_df, width="stretch", height=350, hide_index=True)

    st.button("Push Top Opportunities to Pipeline", width="stretch", key="push_pipeline")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Bottom action layer
# =========================================================
b1, b2, b3, b4 = st.columns([1, 1, 1, 1.1])

with b1:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">LinkedIn Demo Flow</div>', unsafe_allow_html=True)
    st.write("- Paste your LinkedIn URL or company page.")
    st.write("- Generate opportunity signals from public activity.")
    st.write("- Convert detected accounts into qualified pipeline.")
    st.caption("Best hero moment for demo.")
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Web Crawl Demo Flow</div>', unsafe_allow_html=True)
    st.write("- Paste a company website.")
    st.write("- Detect hiring, newsroom, projects or expansion signals.")
    st.write("- Turn them into institutional pursuit candidates.")
    st.caption("Shows external-world signal capture.")
    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Procurement Demo Flow</div>', unsafe_allow_html=True)
    st.write("- Simulate tenders, RFPs and government procurement.")
    st.write("- Qualify technical fit and value potential.")
    st.write("- Push only the strongest opportunities into pursuit.")
    st.caption("Great for industrial / infra sales story.")
    st.markdown("</div>", unsafe_allow_html=True)

with b4:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### Outreach Generator")
    st.caption("Generate a pursuit-ready opener from the detected signal.")

    contact_name = st.text_input("Contact name", "John", key="contact_name")
    company_name = st.text_input("Company", "ABC Construction", key="company_name")

    msg = f"""Hi {contact_name},

We noticed recent market signals related to {company_name} and wanted to connect.

Our opportunity intelligence approach helps teams convert external market signals into structured pipeline, sharper qualification, and faster commercial action.

Would you be open to a short discussion?

Regards"""
    st.text_area("Generated outreach", msg, height=220, key="generated_outreach")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Demo tip: start with LinkedIn, then switch to Web Crawling, and show that the same engine can detect, qualify and convert external signals into pipeline.")