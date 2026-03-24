#!/usr/bin/env python3
import os, json
import pandas as pd
import numpy as np
from datetime import datetime

def confidence_interval(p, n):
    if n == 0:
        return (0, 0)
    se = np.sqrt((p*(1-p))/n)
    return (max(0, p-1.96*se), min(1, p+1.96*se))

def main():
    opp_path = "out/hunting_enriched.csv"
    if not os.path.exists(opp_path):
        raise SystemExit("Run hunting_enrich first")

    df = pd.read_csv(opp_path)
    df["stage"] = df["stage"].astype(str)
    df["expected_value_local"] = pd.to_numeric(df.get("expected_value_local", 0), errors="coerce").fillna(0)

    # ---- 1) Win Rate by Vertical & Market
    won = df[df["stage"] == "Won"]
    total_by_vertical = df.groupby("vertical")["opportunity_id"].count()
    won_by_vertical = won.groupby("vertical")["opportunity_id"].count()

    win_vertical = []
    for v in total_by_vertical.index:
        total = total_by_vertical.get(v, 0)
        won_count = won_by_vertical.get(v, 0)
        rate = won_count / total if total > 0 else 0
        ci_low, ci_high = confidence_interval(rate, total)
        win_vertical.append({
            "vertical": v,
            "total_deals": int(total),
            "won_deals": int(won_count),
            "win_rate_pct": round(rate*100,1),
            "confidence_low_pct": round(ci_low*100,1),
            "confidence_high_pct": round(ci_high*100,1)
        })

    win_df = pd.DataFrame(win_vertical)
    win_df.to_csv("out/hunting_win_rates.csv", index=False)

    # ---- 2) Slippage Risk Scoring
    today = pd.Timestamp(datetime.now().date())
    df["expected_close_date"] = pd.to_datetime(df.get("expected_close_date"), errors="coerce")
    df["days_to_close"] = (df["expected_close_date"] - today).dt.days

    df["days_since_last_activity"] = pd.to_numeric(df.get("days_since_last_activity", 0), errors="coerce").fillna(0)
    df["win_probability_pct"] = pd.to_numeric(df.get("win_probability_pct", 0), errors="coerce").fillna(0)

    # Rule-based slippage risk
    df["slippage_risk_score"] = (
        (df["days_since_last_activity"] > 21).astype(int)*30 +
        (df["days_to_close"] < 15).astype(int)*25 +
        (df["win_probability_pct"] < 40).astype(int)*25 +
        (df["stage"].isin(["Proposal","Negotiation"])).astype(int)*20
    )

    df["slippage_risk_score"] = df["slippage_risk_score"].clip(0,100)

    df[[
        "opportunity_id","account_name","stage",
        "expected_value_local","slippage_risk_score"
    ]].to_csv("out/hunting_slippage_scores.csv", index=False)

    # ---- 3) Portfolio Risk Signals
    total_pipeline = df["expected_value_local"].sum()
    high_risk_value = df[df["slippage_risk_score"] > 60]["expected_value_local"].sum()
    concentration = df.groupby("market")["expected_value_local"].sum()
    top_market_pct = (concentration.max()/total_pipeline*100) if total_pipeline > 0 else 0

    predictive = {
        "total_pipeline_local": float(total_pipeline),
        "high_risk_pipeline_pct": round((high_risk_value/total_pipeline*100),1) if total_pipeline>0 else 0,
        "top_market_concentration_pct": round(top_market_pct,1)
    }

    with open("out/hunting_predictive_metrics.json","w") as f:
        json.dump(predictive, f, indent=2)

    print("OK: wrote hunting_predictive_metrics.json")
    print("OK: wrote hunting_win_rates.csv")
    print("OK: wrote hunting_slippage_scores.csv")

if __name__ == "__main__":
    main()
