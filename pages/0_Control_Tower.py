import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

OUT = "out"


# =========================================================
# Helpers
# =========================================================
def load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def last_row(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}
    x = df.copy()
    if "week_id" in x.columns:
        x = x.sort_values("week_id")
    return x.iloc[-1].to_dict()


def safe_float(d: dict, key: str, default: float = 0.0) -> float:
    try:
        val = d.get(key, default)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return float(default)
        return float(val)
    except Exception:
        return float(default)


def fmt_money(x: float) -> str:
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return "0"


def fmt_pct(x: float) -> str:
    try:
        return f"{float(x):.1f}%"
    except Exception:
        return "0.0%"


def with_delta(current: float, previous: float) -> tuple[float, str]:
    delta = float(current) - float(previous)
    sign = "+" if delta >= 0 else ""
    return current, f"{sign}{delta:,.0f}"


def with_delta_pct(current: float, previous: float) -> tuple[str, str]:
    delta = float(current) - float(previous)
    sign = "+" if delta >= 0 else ""
    return fmt_pct(current), f"{sign}{delta:.1f}pp"


def get_prev_row(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}
    x = df.copy()
    if "week_id" in x.columns:
        x = x.sort_values("week_id")
    if len(x) < 2:
        return x.iloc[-1].to_dict()
    return x.iloc[-2].to_dict()


def add_app_css():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
            max-width: 96rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,244,236,0.96));
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 18px;
            padding: 12px 14px 10px 14px;
            box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        }

        .app-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,244,236,0.96));
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 22px;
            padding: 16px 18px;
            box-shadow: 0 12px 28px rgba(15,23,42,0.06);
        }

        .app-card-tight {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,244,236,0.96));
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 18px;
            padding: 12px 14px;
            box-shadow: 0 8px 18px rgba(15,23,42,0.05);
        }

        .section-kicker {
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: #64748b;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 2px;
        }

        .section-sub {
            color: #475569;
            font-size: 0.92rem;
            margin-bottom: 2px;
        }

        .status-chip {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid rgba(15,23,42,0.08);
            background: rgba(255,255,255,0.72);
            color: #0f172a;
            margin-right: 8px;
        }

        .queue-item {
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
        }

        .queue-meta {
            font-size: 0.83rem;
            color: #64748b;
            margin-bottom: 6px;
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


def compute_status(actual: float, target: float, good_when_lower: bool = False) -> str:
    if target <= 0:
        return "Watch"
    ratio = actual / target if target else 1.0
    if good_when_lower:
        if ratio <= 1.00:
            return "On Track"
        if ratio <= 1.10:
            return "Watch"
        return "At Risk"
    else:
        if ratio >= 1.00:
            return "On Track"
        if ratio >= 0.92:
            return "Watch"
        return "At Risk"


def status_chip(status: str) -> str:
    return f'<span class="status-chip">{status}</span>'


def make_targets(latest: dict) -> dict:
    revenue = safe_float(latest, "revenue")
    spend = safe_float(latest, "spend")
    gm = safe_float(latest, "gross_margin")
    profit = safe_float(latest, "profit")

    return {
        "revenue": revenue if revenue > 0 else 1.0,
        "spend": spend if spend > 0 else 1.0,
        "gm": gm if gm > 0 else 1.0,
        "profit": profit if profit > 0 else 1.0,
    }


def build_trend_chart(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()

    if df is None or df.empty:
        fig.update_layout(
            title=title,
            height=360,
            margin=dict(l=10, r=10, t=50, b=10),
        )
        return fig

    x = df["week_id"] if "week_id" in df.columns else list(range(len(df)))

    for col in ["revenue", "gross_margin", "profit"]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=df[col],
                    mode="lines+markers",
                    name=col.replace("_", " ").title(),
                )
            )

    fig.update_layout(
        title=title,
        height=360,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis_title="Week",
        yaxis_title="Value",
    )
    return fig


def build_variance_table(latest: dict, prev: dict, targets: dict, scope_name: str) -> pd.DataFrame:
    metrics = [
        ("Revenue", safe_float(latest, "revenue"), safe_float(prev, "revenue"), targets["revenue"], False),
        ("Spend", safe_float(latest, "spend"), safe_float(prev, "spend"), targets["spend"], True),
        ("Gross Margin", safe_float(latest, "gross_margin"), safe_float(prev, "gross_margin"), targets["gm"], False),
        ("Profit", safe_float(latest, "profit"), safe_float(prev, "profit"), targets["profit"], False),
        ("GM %", safe_float(latest, "gm_pct"), safe_float(prev, "gm_pct"), safe_float(latest, "gm_pct"), False),
    ]

    rows = []
    for metric, actual, previous, target, lower_better in metrics:
        status = compute_status(actual, target, good_when_lower=lower_better) if metric != "GM %" else "Watch"
        rows.append(
            {
                "Scope": scope_name,
                "Metric": metric,
                "Actual": fmt_pct(actual) if metric == "GM %" else fmt_money(actual),
                "Vs Last": (with_delta_pct(actual, previous)[1] if metric == "GM %" else with_delta(actual, previous)[1]),
                "Target": fmt_pct(target) if metric == "GM %" else fmt_money(target),
                "Status": status,
            }
        )
    return pd.DataFrame(rows)


def generate_queue_items(t_last: dict, h_last: dict, f_last: dict, t_targets: dict, h_targets: dict, f_targets: dict):
    items = []

    if safe_float(t_last, "profit") < t_targets["profit"]:
        items.append({
            "title": "Profit below command threshold",
            "severity": "High",
            "owner": "Control Tower",
            "action": "Review spend discipline and margin leakage across Hunting and Farming.",
            "confidence": "High",
        })

    if safe_float(h_last, "revenue") < h_targets["revenue"]:
        items.append({
            "title": "Hunting revenue below target",
            "severity": "Medium",
            "owner": "Hunting Lead",
            "action": "Escalate top opportunity slippages and accelerate closure for late-stage pipeline.",
            "confidence": "Medium",
        })

    if safe_float(f_last, "gross_margin") < f_targets["gm"]:
        items.append({
            "title": "Farming margin compression",
            "severity": "High",
            "owner": "Farming Lead",
            "action": "Review price corridors, mix quality and distributor-level profitability exceptions.",
            "confidence": "High",
        })

    if safe_float(t_last, "spend") > t_targets["spend"] * 1.05:
        items.append({
            "title": "Spend running above budget",
            "severity": "Medium",
            "owner": "Finance / Commercial",
            "action": "Freeze low-ROI discretionary spend and approve only protected-growth interventions.",
            "confidence": "High",
        })

    if not items:
        items.append({
            "title": "System stable — no major command exceptions",
            "severity": "Low",
            "owner": "Control Tower",
            "action": "Continue monitoring and focus on proactive pipeline and margin improvements.",
            "confidence": "Medium",
        })

    return items[:4]


def action_list(scope: str):
    if scope == "Hunting":
        return [
            "Push top late-stage opportunities to closure with named owner tracking.",
            "Review institutional pricing exceptions before margin leakage compounds.",
            "Escalate delayed approvals blocking project conversion.",
        ]
    if scope == "Farming":
        return [
            "Review distributor profit pool outliers and recover margin leakage.",
            "Resolve supply and replenishment friction for stressed accounts.",
            "Tighten mix and price discipline on low-quality growth pockets.",
        ]
    return [
        "Prioritize cross-engine issues with direct P&L impact.",
        "Close pending governance decisions in one queue.",
        "Lock next-week actions with accountable owner and timeline.",
    ]


def assistant_panel(t_last: dict, h_last: dict, f_last: dict):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("### SYDIAI Command")
    st.caption("Executive prompts, summaries and action framing.")

    focus = st.segmented_control(
        "Focus",
        ["Overall", "Hunting", "Farming"],
        default="Overall",
        key="assistant_focus",
    )

    ctx = t_last if focus == "Overall" else h_last if focus == "Hunting" else f_last

    st.markdown(
        f"""
        <div class="app-card-tight" style="margin-bottom:10px;">
            <div class="small-note">Current Snapshot</div>
            <div style="font-weight:800; font-size:1.0rem; color:#0f172a; margin-top:4px;">{focus}</div>
            <div class="small-note" style="margin-top:8px;">
                Revenue <b>{fmt_money(safe_float(ctx, "revenue"))}</b> ·
                Profit <b>{fmt_money(safe_float(ctx, "profit"))}</b> ·
                GM <b>{fmt_pct(safe_float(ctx, "gm_pct"))}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Mode",
        ["CEO summary", "Risks & actions", "30-second narrative"],
        key="assistant_mode",
    )

    prompt = st.text_area(
        "Prompt",
        value="Give me the most important talking points for this screen.",
        height=120,
        key="assistant_prompt",
    )

    if st.button("Generate output", width="stretch", key="assistant_generate"):
        if mode == "CEO summary":
            out = [
                f"{focus} is currently tracking Revenue {fmt_money(safe_float(ctx, 'revenue'))}, Profit {fmt_money(safe_float(ctx, 'profit'))}, and GM {fmt_pct(safe_float(ctx, 'gm_pct'))}.",
                "The page is structured as a control application: signal strip, performance trend, variance matrix, and decision queue.",
                "Leaders can move directly from performance reading to action ownership without leaving the cockpit.",
            ]
        elif mode == "Risks & actions":
            out = [
                "Risk: margin dilution from uncontrolled spend or poor mix quality.",
                "Risk: delayed conversions in Hunting or delayed replenishment corrections in Farming.",
                "Action: prioritize open queue items and lock owners against each exception this week.",
            ]
        else:
            out = [
                "This control tower gives leadership a unified command view across overall business, Hunting and Farming.",
                "It highlights what changed, where performance is drifting, and which decisions need attention now.",
                "From here, teams can move directly into deeper engine pages while preserving one governance layer.",
            ]

        st.markdown("#### Output")
        for line in out:
            st.write(f"- {line}")

    st.markdown("#### Suggested prompts")
    st.write("- Summarize this page for the CEO in 3 bullets.")
    st.write("- What are the top 2 risks and next actions?")
    st.write("- Give me a 30-second narrative for the demo.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Data
# =========================================================
T = load_csv("control_kpi_total.csv")
H = load_csv("control_kpi_hunting.csv")
F = load_csv("control_kpi_farming.csv")

if T.empty:
    st.error("KPI cubes missing. Run: python3 tools/control_kpi_builder.py")
    st.stop()

for df in (T, H, F):
    if not df.empty and "week_id" in df.columns:
        df.sort_values("week_id", inplace=True)

t_last = last_row(T)
h_last = last_row(H)
f_last = last_row(F)

t_prev = get_prev_row(T)
h_prev = get_prev_row(H) if not H.empty else {}
f_prev = get_prev_row(F) if not F.empty else {}

T_targets = make_targets(t_last)
H_targets = make_targets(h_last)
F_targets = make_targets(f_last)

add_app_css()

# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="app-card" style="margin-bottom:14px;">
        <div class="section-kicker">Control Tower</div>
        <div class="section-title">Command Centre</div>
        <div class="section-sub">
            A unified operational command view across enterprise performance, hunting momentum,
            farming health and governance actions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Executive signal strip
# =========================================================
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)

rev_val, rev_delta = with_delta(safe_float(t_last, "revenue"), safe_float(t_prev, "revenue"))
gm_val, gm_delta = with_delta(safe_float(t_last, "gross_margin"), safe_float(t_prev, "gross_margin"))
profit_val, profit_delta = with_delta(safe_float(t_last, "profit"), safe_float(t_prev, "profit"))
spend_val, spend_delta = with_delta(safe_float(t_last, "spend"), safe_float(t_prev, "spend"))
hunt_status = compute_status(safe_float(h_last, "revenue"), H_targets["revenue"])
farm_status = compute_status(safe_float(f_last, "profit"), F_targets["profit"])
open_queue = len(generate_queue_items(t_last, h_last, f_last, T_targets, H_targets, F_targets))
decisions_pending = max(1, open_queue - 1)

with c1:
    st.metric("Revenue", fmt_money(rev_val), rev_delta)
with c2:
    st.metric("Gross Margin", fmt_money(gm_val), gm_delta)
with c3:
    st.metric("Profit", fmt_money(profit_val), profit_delta)
with c4:
    st.metric("Spend", fmt_money(spend_val), spend_delta)
with c5:
    st.metric("Hunting Health", hunt_status, "")
with c6:
    st.metric("Farming Health", farm_status, "")
with c7:
    st.metric("Open Exceptions", f"{open_queue}", "")
with c8:
    st.metric("Pending Decisions", f"{decisions_pending}", "")

st.markdown("")

# =========================================================
# Main command area
# =========================================================
left, middle, right = st.columns([1.65, 1.1, 0.95])

with left:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Performance View</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Command Trend</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Switch between Overall, Hunting and Farming without leaving the page.</div>',
        unsafe_allow_html=True,
    )

    scope = st.segmented_control(
        "Scope",
        ["Overall", "Hunting", "Farming"],
        default="Overall",
        key="control_scope",
    )

    if scope == "Overall":
        view_df = T
        view_last = t_last
        view_prev = t_prev
        view_targets = T_targets
    elif scope == "Hunting":
        view_df = H
        view_last = h_last
        view_prev = h_prev
        view_targets = H_targets
    else:
        view_df = F
        view_last = f_last
        view_prev = f_prev
        view_targets = F_targets

    fig = build_trend_chart(view_df.tail(16), f"{scope} Performance Trend")
    st.plotly_chart(fig, width="stretch", key="command_trend_chart")

    st.markdown("</div>", unsafe_allow_html=True)

with middle:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Variance Matrix</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Plan vs Actual</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A crisp comparison against target and latest movement.</div>',
        unsafe_allow_html=True,
    )

    var_df = build_variance_table(view_last, view_prev, view_targets, scope)
    st.dataframe(var_df, width="stretch", hide_index=True)

    st.markdown(
        f"""
        <div style="margin-top:10px;">
            {status_chip(compute_status(safe_float(view_last, "revenue"), view_targets["revenue"]))}
            {status_chip(compute_status(safe_float(view_last, "spend"), view_targets["spend"], good_when_lower=True))}
            {status_chip(compute_status(safe_float(view_last, "profit"), view_targets["profit"]))}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Decision Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What Needs Attention</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Prioritized exceptions with clear owner and next action.</div>',
        unsafe_allow_html=True,
    )

    queue_items = generate_queue_items(t_last, h_last, f_last, T_targets, H_targets, F_targets)
    for item in queue_items:
        st.markdown(
            f"""
            <div class="queue-item">
                <div class="queue-title">{item["title"]}</div>
                <div class="queue-meta">
                    Severity: <b>{item["severity"]}</b> · Owner: <b>{item["owner"]}</b> · Confidence: <b>{item["confidence"]}</b>
                </div>
                <div style="font-size:0.9rem; color:#334155;">{item["action"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.button("Review queue", width="stretch", key="review_queue_btn")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# Action layer + assistant
# =========================================================
bottom_left, bottom_mid, bottom_right, assistant_col = st.columns([1, 1, 1, 1.05])

with bottom_left:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Hunting Actions</div>', unsafe_allow_html=True)
    for item in action_list("Hunting"):
        st.write(f"- {item}")
    st.caption("Use this block to move from signal to closure actions.")
    st.markdown("</div>", unsafe_allow_html=True)

with bottom_mid:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Farming Actions</div>', unsafe_allow_html=True)
    for item in action_list("Farming"):
        st.write(f"- {item}")
    st.caption("Use this block to focus on service, profitability and correction loops.")
    st.markdown("</div>", unsafe_allow_html=True)

with bottom_right:
    st.markdown('<div class="action-card">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">Governance Actions</div>', unsafe_allow_html=True)
    for item in action_list("Governance"):
        st.write(f"- {item}")
    st.caption("Use this block to assign owner, decision and timeline.")
    st.markdown("</div>", unsafe_allow_html=True)

with assistant_col:
    assistant_panel(t_last, h_last, f_last)

st.caption("Refresh KPI cubes before demo if needed: python3 tools/control_kpi_builder.py")