import pandas as pd
import plotly.express as px

STAGE_ORDER = ["Target","Qualification","Technical","Proposal","Negotiation","Won","Lost"]

def closure_forecast_bar(df_forecast: pd.DataFrame):
    if df_forecast is None or df_forecast.empty:
        return None
    fig = px.bar(df_forecast, x="close_bucket", y="weighted_pipeline_local",
                 title="Weighted Pipeline Closing Window (0–30 / 31–60 / 61–90 / 90+)")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=48,b=10))
    return fig

def reasons_bar(df_reasons: pd.DataFrame):
    if df_reasons is None or df_reasons.empty:
        return None
    d = df_reasons.copy()
    d["label"] = d["event_type"].astype(str) + " — " + d["reason_code"].astype(str)
    fig = px.bar(d, x="label", y="count", title="Top Stall / Exit Reasons (last 90 days)")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=48,b=10))
    return fig

def owner_stage_heatmap(df_heat: pd.DataFrame):
    if df_heat is None or df_heat.empty:
        return None
    piv = df_heat.pivot_table(index="owner", columns="stage", values="aging_pressure_days", aggfunc="mean")
    # Keep stage order
    piv = piv.reindex(columns=[s for s in STAGE_ORDER if s in piv.columns])
    fig = px.imshow(piv, aspect="auto", title="Owner × Stage Aging Pressure (days)")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=48,b=10))
    return fig
