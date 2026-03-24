import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

STAGE_ORDER = ["Target","Qualification","Technical","Proposal","Negotiation","Won","Lost"]

def funnel_value(df: pd.DataFrame, title="Acquisition Funnel (Value by Stage)"):
    if df is None or df.empty:
        return None
    tmp = df.copy()
    tmp["potential_annual_value_local"] = pd.to_numeric(tmp.get("potential_annual_value_local", 0.0), errors="coerce").fillna(0.0)
    agg = tmp.groupby("stage")["potential_annual_value_local"].sum().reindex(STAGE_ORDER).dropna().reset_index()
    if agg.empty:
        return None
    fig = go.Figure(go.Funnel(
        y=agg["stage"],
        x=agg["potential_annual_value_local"],
        textinfo="value+percent initial"
    ))
    fig.update_layout(
        title=title,
        margin=dict(l=10,r=10,t=48,b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def prob_vs_value(df: pd.DataFrame, title="Deal Quality: Probability vs Value"):
    if df is None or df.empty:
        return None
    d = df.copy()
    d["win_probability_pct"] = pd.to_numeric(d.get("win_probability_pct", 0.0), errors="coerce").fillna(0.0)
    d["potential_annual_value_local"] = pd.to_numeric(d.get("potential_annual_value_local", 0.0), errors="coerce").fillna(0.0)
    d["deal_quality_score_0_100"] = pd.to_numeric(d.get("deal_quality_score_0_100", 0.0), errors="coerce").fillna(0.0)

    fig = px.scatter(
        d,
        x="win_probability_pct",
        y="potential_annual_value_local",
        size="deal_quality_score_0_100",
        color="stage",
        hover_data=[c for c in ["opportunity_id","account_name","market","vertical","owner","sla_breached","days_since_last_activity"] if c in d.columns],
        title=title
    )
    fig.update_layout(
        margin=dict(l=10,r=10,t=48,b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="Stage"
    )
    return fig

def concentration(df: pd.DataFrame, col="market", title="Concentration Risk"):
    if df is None or df.empty or col not in df.columns:
        return None
    d = df.copy()
    d["expected_value_local"] = pd.to_numeric(d.get("expected_value_local", 0.0), errors="coerce").fillna(0.0)
    agg = d.groupby(col)["expected_value_local"].sum().sort_values(ascending=False).reset_index()
    fig = px.bar(agg, x=col, y="expected_value_local", title=title)
    fig.update_layout(
        margin=dict(l=10,r=10,t=48,b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def stage_conversion_table(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    d = df.copy()
    d["stage"] = d["stage"].astype(str)
    counts = d["stage"].value_counts()
    rows=[]
    for i in range(len(STAGE_ORDER)-2):  # stop before Won/Lost
        s = STAGE_ORDER[i]
        s_next = STAGE_ORDER[i+1]
        c1 = int(counts.get(s, 0))
        c2 = int(counts.get(s_next, 0))
        conv = (c2/c1*100.0) if c1>0 else 0.0
        rows.append({"From Stage": s, "To Stage": s_next, "Count (From)": c1, "Count (To)": c2, "Stage-to-Stage Conversion %": round(conv,1)})
    return pd.DataFrame(rows)
