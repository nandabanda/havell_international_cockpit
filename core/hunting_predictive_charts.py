import pandas as pd
import plotly.express as px

def win_rate_chart(df):
    if df.empty:
        return None
    fig = px.bar(df, x="vertical", y="win_rate_pct",
                 title="Win Rate by Vertical (%)")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def slippage_chart(df):
    if df.empty:
        return None
    fig = px.bar(df.sort_values("slippage_risk_score", ascending=False).head(15),
                 x="opportunity_id",
                 y="slippage_risk_score",
                 title="Top Slippage Risk Deals")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig
