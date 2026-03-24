import os
import random
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

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

        .deal-card {
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 16px;
            padding: 12px 12px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.72);
        }

        .deal-title {
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 4px;
            font-size: 0.98rem;
        }

        .deal-meta {
            color: #64748b;
            font-size: 0.83rem;
            margin-bottom: 6px;
        }

        .deal-body {
            color: #334155;
            font-size: 0.9rem;
            line-height: 1.35rem;
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


def confidence_band(score):
    if score >= 88:
        return "High"
    if score >= 76:
        return "Medium"
    return "Watch"


def create_mock_deals():
    rows = [
        ["DL-001", "L&T Construction", "Dubai Infra Package", "UAE", "Prospecting", 6.8, 84, "Institutional BD", "Need sponsor mapping"],
        ["DL-002", "Tata Projects", "Industrial Electrical Fitout", "India", "Qualified", 8.2, 89, "Regional Sales", "Strong fit, commercial prep"],
        ["DL-003", "Adani Infra", "Grid Expansion Program", "India", "Solutioning", 12.4, 92, "Key Accounts", "High-priority pursuit"],
        ["DL-004", "Jakson Solar", "Solar BOS & Electrical Scope", "India", "Qualified", 5.7, 86, "BD Lead", "Technical fit validated"],
        ["DL-005", "Shapoorji Pallonji", "Smart Building Opportunity", "Saudi Arabia", "Prospecting", 7.1, 78, "Channel Lead", "Need account contact"],
        ["DL-006", "OEM Partner Cluster", "Institutional Retrofit Program", "Indonesia", "Proposal", 4.6, 81, "Regional Sales", "Proposal shaping stage"],
        ["DL-007", "Gov Infra Board", "Public Works Tender", "UAE", "Qualified", 9.3, 87, "Institutional BD", "Tender intelligence active"],
        ["DL-008", "Large Real Estate Group", "Mixed-use Development", "Saudi Arabia", "Negotiation", 10.8, 91, "Key Accounts", "Decision path identified"],
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "deal_id", "account", "opportunity", "market", "stage", "value_musd",
            "ai_score", "owner", "next_step"
        ],
    )
    df["confidence"] = df["ai_score"].apply(confidence_band)
    df["win_probability"] = np.clip(df["ai_score"] - 18, 35, 92)
    df["days_open"] = np.random.randint(6, 74, size=len(df))
    return df


def create_meeting_queue(df):
    rows = []
    for _, r in df.head(6).iterrows():
        rows.append(
            {
                "Account": r["account"],
                "Opportunity": r["opportunity"],
                "Next Meeting": random.choice(["Tomorrow 11:00", "Thu 3:30 PM", "Fri 10:00 AM", "Next Mon 2:00 PM"]),
                "Purpose": random.choice(["Intro", "Qualification", "Technical fit", "Commercial review"]),
                "Owner": r["owner"],
                "Priority": "High" if r["ai_score"] >= 88 else "Medium",
            }
        )
    return pd.DataFrame(rows)


def create_outreach_queue(df):
    rows = []
    for _, r in df.head(6).iterrows():
        rows.append(
            {
                "Account": r["account"],
                "Persona": random.choice(["CEO Office", "Procurement", "Projects Head", "Sales Head", "Technical Lead"]),
                "Recommended Channel": random.choice(["LinkedIn", "Email", "Call", "Partner Intro"]),
                "Message Angle": random.choice([
                    "Growth visibility",
                    "Institutional opportunity support",
                    "Project intelligence",
                    "Commercial qualification",
                ]),
                "Owner": r["owner"],
            }
        )
    return pd.DataFrame(rows)


def build_stage_funnel(df):
    order = ["Prospecting", "Qualified", "Solutioning", "Proposal", "Negotiation"]
    x = (
        df.groupby("stage", as_index=False)["value_musd"]
        .sum()
        .rename(columns={"value_musd": "Value"})
    )
    x["stage"] = pd.Categorical(x["stage"], categories=order, ordered=True)
    x = x.sort_values("stage")
    return x


def build_owner_view(df):
    return (
        df.groupby("owner", as_index=False)
        .agg(
            Pipeline_Value=("value_musd", "sum"),
            Deals=("deal_id", "count"),
            Avg_AI_Score=("ai_score", "mean"),
        )
        .sort_values("Pipeline_Value", ascending=False)
    )


def render_deal_cards(df, top_n=5):
    for _, r in df.head(top_n).iterrows():
        st.markdown(
            f"""
            <div class="deal-card">
                <div class="deal-title">{r["account"]} · {r["opportunity"]}</div>
                <div class="deal-meta">
                    {r["market"]} · Stage <b>{r["stage"]}</b> · Value <b>${fmt_money(r["value_musd"])}M</b> · AI Score <b>{int(r["ai_score"])}</b> · Confidence <b>{r["confidence"]}</b>
                </div>
                <div class="deal-body">
                    <b>Owner:</b> {r["owner"]}<br>
                    <b>Next Step:</b> {r["next_step"]}<br>
                    <b>Win Probability:</b> {int(r["win_probability"])}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def assistant_panel(deals_df):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Deal Coach")
    st.caption("Prioritise, qualify and push the right pursuits forward.")

    if deals_df.empty:
        st.info("No deals available.")
    else:
        top = deals_df.sort_values(["ai_score", "value_musd"], ascending=[False, False]).iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight" style="margin-bottom:10px;">
                <div class="small-note">Highest-priority pursuit</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{top["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {top["market"]} · {top["stage"]} · ${fmt_money(top["value_musd"])}M · AI {int(top["ai_score"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.selectbox(
            "Coach mode",
            ["CEO summary", "Deal strategy", "Meeting prep", "Outreach opener"],
            key="bd_coach_mode",
        )

        if st.button("Generate guidance", width="stretch", key="bd_coach_generate"):
            if mode == "CEO summary":
                lines = [
                    f"The strongest current pursuit is {top['account']} at ${fmt_money(top['value_musd'])}M potential.",
                    "The studio combines account visibility, stage discipline, meeting rhythm and next-step orchestration.",
                    "The goal is not only pipeline growth, but better-quality pursuit progression.",
                ]
            elif mode == "Deal strategy":
                lines = [
                    f"Prioritise {top['account']} because value, AI score and win probability are all strong.",
                    "Lock stakeholder map, validate commercial entry point and prepare stage-exit criteria.",
                    "Move from generic follow-up to structured pursuit management with named owner and date.",
                ]
            elif mode == "Meeting prep":
                lines = [
                    f"Prepare the meeting around {top['opportunity']}, not generic corporate capability.",
                    "Open with current project relevance, then move to scope fit and commercial path.",
                    "End with one explicit next step: sponsor introduction, technical workshop or pricing review.",
                ]
            else:
                lines = [
                    f"Hi team — we’re tracking signals around {top['account']} and believe there may be a relevant opportunity linked to {top['opportunity']}.",
                    "We would value a short discussion to understand current priorities and see if there is a fit.",
                    "Our approach helps convert fragmented market signals into structured institutional opportunities.",
                ]

            st.markdown("#### Output")
            for line in lines:
                st.write(f"- {line}")

        st.markdown("#### Suggested prompts")
        st.write("- What are the top 3 pursuits I should review today?")
        st.write("- Prepare me for the next account meeting.")
        st.write("- Write a sharper opener for this opportunity.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init
# =========================================================
add_page_css()

if "bd_deals" not in st.session_state:
    st.session_state.bd_deals = create_mock_deals()

deals_df = st.session_state.bd_deals.copy()

# Optional filters
market_list = ["All"] + sorted(deals_df["market"].dropna().unique().tolist())
stage_list = ["All", "Prospecting", "Qualified", "Solutioning", "Proposal", "Negotiation"]

# =========================================================
# Hero
# =========================================================
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Hunting · Business Development Studio</div>
        <div class="hero-title">Institutional Deal Command Layer</div>
        <div class="hero-sub">
            Manage pursuit-quality pipeline, account progression, meeting rhythm and outreach orchestration in one sharp operating view.
            This is where opportunity detection becomes active business development.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Control bar
# =========================================================
st.markdown('<div class="app-card">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">Deal Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Pipeline Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Keep filters in-page so the left panel remains a true application navigation shell.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.2, 0.9])

with c1:
    market_filter = st.selectbox("Market", market_list, key="bd_market_filter")
with c2:
    stage_filter = st.selectbox("Stage", stage_list, key="bd_stage_filter")
with c3:
    owner_filter = st.selectbox(
        "Owner",
        ["All"] + sorted(deals_df["owner"].unique().tolist()),
        key="bd_owner_filter",
    )
with c4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    refresh_pipeline = st.button("Refresh View", width="stretch", key="bd_refresh")

if market_filter != "All":
    deals_df = deals_df[deals_df["market"] == market_filter]
if stage_filter != "All":
    deals_df = deals_df[deals_df["stage"] == stage_filter]
if owner_filter != "All":
    deals_df = deals_df[deals_df["owner"] == owner_filter]

st.markdown(
    """
    <div style="margin-top:8px;">
        <span class="signal-chip">Priority Pursuits</span>
        <span class="signal-chip">Meeting Rhythm</span>
        <span class="signal-chip">Outreach Queue</span>
        <span class="signal-chip">Stage Progression</span>
        <span class="signal-chip">Deal Quality Control</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KPI strip
# =========================================================
total_pipeline = deals_df["value_musd"].sum() if not deals_df.empty else 0
avg_ai = deals_df["ai_score"].mean() if not deals_df.empty else 0
high_priority = (deals_df["ai_score"] >= 88).sum() if not deals_df.empty else 0
late_stage = deals_df["stage"].isin(["Proposal", "Negotiation"]).sum() if not deals_df.empty else 0
weighted_pipeline = (deals_df["value_musd"] * deals_df["win_probability"] / 100).sum() if not deals_df.empty else 0
meetings_due = min(6, len(deals_df))

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Open Deals", len(deals_df))
with k2:
    st.metric("Pipeline ($M)", fmt_money(total_pipeline))
with k3:
    st.metric("Weighted Pipeline ($M)", fmt_money(weighted_pipeline))
with k4:
    st.metric("Avg AI Score", f"{avg_ai:.0f}")
with k5:
    st.metric("High-Priority Deals", int(high_priority))
with k6:
    st.metric("Meetings Due", int(meetings_due))

st.markdown("")

# =========================================================
# Main command area
# =========================================================
left, middle, right = st.columns([1.45, 1.1, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Opportunity Board</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top Pursuits</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A clean, readable priority board showing which deals matter most and what happens next.</div>',
        unsafe_allow_html=True,
    )

    if deals_df.empty:
        st.info("No deals match the current filters.")
    else:
        display_df = deals_df.sort_values(["ai_score", "value_musd"], ascending=[False, False])
        render_deal_cards(display_df, top_n=5)

    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Stage Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Pipeline Shape</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Shows whether business development is still early-stage heavy or progressing toward closure.</div>',
        unsafe_allow_html=True,
    )

    if deals_df.empty:
        st.info("No deals available for analytics.")
    else:
        funnel_df = build_stage_funnel(deals_df)
        fig = px.bar(funnel_df, x="stage", y="Value", title="Pipeline by Stage")
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig, width="stretch", key="bd_stage_funnel")

        owner_df = build_owner_view(deals_df)
        st.dataframe(owner_df, width="stretch", height=220, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    assistant_panel(deals_df)

st.markdown("")

# =========================================================
# Meeting queue / outreach / account view
# =========================================================
meeting_df = create_meeting_queue(deals_df) if not deals_df.empty else pd.DataFrame()
outreach_df = create_outreach_queue(deals_df) if not deals_df.empty else pd.DataFrame()

b1, b2, b3 = st.columns([1.12, 1.12, 1.0])

with b1:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Meeting Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next Conversations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Use this to show that the page is not passive reporting — it drives daily business development activity.</div>',
        unsafe_allow_html=True,
    )

    if meeting_df.empty:
        st.info("No meetings queued.")
    else:
        st.dataframe(meeting_df, width="stretch", height=310, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Outreach Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next Best Contact Motion</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Turn detected opportunities into concrete outreach actions by channel, persona and message angle.</div>',
        unsafe_allow_html=True,
    )

    if outreach_df.empty:
        st.info("No outreach recommendations.")
    else:
        st.dataframe(outreach_df, width="stretch", height=310, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Account Command</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Account</div>', unsafe_allow_html=True)

    if deals_df.empty:
        st.info("No active account.")
    else:
        selected_account = st.selectbox(
            "Account",
            sorted(deals_df["account"].unique().tolist()),
            key="selected_account_bd",
        )
        account_df = deals_df[deals_df["account"] == selected_account].copy()
        row = account_df.iloc[0]

        st.markdown(
            f"""
            <div class="app-card-tight">
                <div class="small-note">Account Snapshot</div>
                <div style="font-size:1rem; font-weight:800; color:#0f172a; margin-top:4px;">{row["account"]}</div>
                <div class="small-note" style="margin-top:8px;">
                    {row["market"]} · {row["stage"]} · ${fmt_money(row["value_musd"])}M · Win {int(row["win_probability"])}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Current opportunity")
        st.write(f"- {row['opportunity']}")
        st.markdown("#### Immediate next step")
        st.write(f"- {row['next_step']}")
        st.markdown("#### Recommendation")
        st.write("- Lock sponsor path, define stage-exit criteria, and schedule the next decisive interaction.")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Bottom action layer
# =========================================================
c1, c2, c3, c4 = st.columns([1, 1, 1, 1.1])

with c1:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Pursuit Prioritisation</div>', unsafe_allow_html=True)
    st.write("- Rank deals by value, AI score and win probability.")
    st.write("- Focus leadership attention on the 3–5 pursuits that matter.")
    st.write("- Remove noise from early, low-quality pipeline.")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Meeting Discipline</div>', unsafe_allow_html=True)
    st.write("- Make the page operational for the team, not just presentational.")
    st.write("- Show upcoming conversations and their purpose.")
    st.write("- Link every meeting to a concrete next step.")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Stage Governance</div>', unsafe_allow_html=True)
    st.write("- Monitor stage progression from prospecting to negotiation.")
    st.write("- Identify pipeline stuck in early stages.")
    st.write("- Force stage quality, not just stage count.")
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### Outreach Draft")
    st.caption("A quick outreach starter from the selected account context.")

    default_account = deals_df.iloc[0]["account"] if not deals_df.empty else "ABC Group"
    contact_name = st.text_input("Contact name", "John", key="bd_contact_name")
    company_name = st.text_input("Company", default_account, key="bd_company_name")

    msg = f"""Hi {contact_name},

I wanted to reach out because we are seeing relevant institutional opportunity signals around {company_name}.

We help commercial teams structure market signals, qualify opportunities faster, and improve pursuit conversion through sharper business development orchestration.

Would you be open to a short discussion?

Regards"""
    st.text_area("Generated message", msg, height=220, key="bd_generated_message")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Demo tip: show this page after Hunting Cockpit to prove that external signals do not stop at discovery — they become governed business development actions.")