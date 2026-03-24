#!/usr/bin/env python3
import os, json
import pandas as pd
import numpy as np
from datetime import datetime

def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    if s.notna().sum() < 3:
        return s.fillna(s.median() if s.notna().any() else 0)
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)

def clamp01(x):
    return float(max(0.0, min(1.0, x)))

def to01_from_z(z: pd.Series) -> pd.Series:
    # Smooth mapping of z-score to 0-1 using logistic
    z = pd.to_numeric(z, errors="coerce").fillna(0.0)
    return 1 / (1 + np.exp(-z))

def safe_read(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

def build_demo_if_missing():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists("data/micromarket_master.csv") and os.path.exists("data/micromarket_master_TEMPLATE.csv"):
        pd.read_csv("data/micromarket_master_TEMPLATE.csv").to_csv("data/micromarket_master.csv", index=False)
    if not os.path.exists("data/distributors_existing.csv") and os.path.exists("data/distributors_existing_TEMPLATE.csv"):
        pd.read_csv("data/distributors_existing_TEMPLATE.csv").to_csv("data/distributors_existing.csv", index=False)
    if not os.path.exists("data/micromarket_sales_PROXY.csv") and os.path.exists("data/micromarket_sales_PROXY_TEMPLATE.csv"):
        pd.read_csv("data/micromarket_sales_PROXY_TEMPLATE.csv").to_csv("data/micromarket_sales_PROXY.csv", index=False)

def main(demo_if_missing: bool = True):
    if demo_if_missing:
        build_demo_if_missing()

    mm = safe_read("data/micromarket_master.csv")
    dist = safe_read("data/distributors_existing.csv")
    sales = safe_read("data/micromarket_sales_PROXY.csv")

    if mm.empty:
        raise SystemExit("Missing data/micromarket_master.csv")

    # ---- Coverage proxy from existing distributors
    coverage = pd.DataFrame()
    if not dist.empty and "assigned_micro_market_id" in dist.columns:
        dist["coverage_strength_0_1"] = pd.to_numeric(dist.get("coverage_strength_0_1", 0.0), errors="coerce").fillna(0.0)
        coverage = (
            dist.groupby("assigned_micro_market_id")["coverage_strength_0_1"]
            .mean()
            .reset_index()
            .rename(columns={"assigned_micro_market_id":"micro_market_id", "coverage_strength_0_1":"coverage_index_0_1"})
        )
    else:
        coverage = pd.DataFrame({"micro_market_id": mm["micro_market_id"].unique(), "coverage_index_0_1": 0.0})

    mmx = mm.merge(coverage, on="micro_market_id", how="left")
    mmx["coverage_index_0_1"] = pd.to_numeric(mmx.get("coverage_index_0_1", 0.0), errors="coerce").fillna(0.0).clip(0,1)

    # ---- Sales proxy rollup (optional)
    if not sales.empty and "micro_market_id" in sales.columns:
        sales["month"] = pd.to_datetime(sales["month"], errors="coerce")
        sales["sell_in_value"] = pd.to_numeric(sales.get("sell_in_value", 0.0), errors="coerce").fillna(0.0)
        sales["sell_out_value"] = pd.to_numeric(sales.get("sell_out_value", 0.0), errors="coerce").fillna(0.0)
        last2 = sales.sort_values("month").groupby("micro_market_id").tail(2)
        sagg = last2.groupby("micro_market_id")[["sell_in_value","sell_out_value"]].mean().reset_index()
        sagg = sagg.rename(columns={"sell_in_value":"sell_in_proxy", "sell_out_value":"sell_out_proxy"})
    else:
        sagg = pd.DataFrame({"micro_market_id": mmx["micro_market_id"].unique(), "sell_in_proxy": 0.0, "sell_out_proxy": 0.0})

    mmx = mmx.merge(sagg, on="micro_market_id", how="left")
    mmx["sell_in_proxy"] = pd.to_numeric(mmx.get("sell_in_proxy", 0.0), errors="coerce").fillna(0.0)
    mmx["sell_out_proxy"] = pd.to_numeric(mmx.get("sell_out_proxy", 0.0), errors="coerce").fillna(0.0)

    # ---- Build normalized factors (0-1)
    # Demand & growth
    demand01 = to01_from_z(zscore(mmx.get("demand_proxy_index", 0)))
    growth01 = to01_from_z(zscore(mmx.get("growth_proxy_index", 0)))

    # Infrastructure & construction velocity
    infra01 = to01_from_z(zscore(mmx.get("infrastructure_spend_index", 0)))
    cons01  = to01_from_z(zscore(mmx.get("construction_velocity_index", 0)))

    # Affluence and retail density
    aff01 = to01_from_z(zscore(mmx.get("affluence_index", 0)))
    ret01 = to01_from_z(zscore(mmx.get("retail_density_index", 0)))

    # Competition (higher competition reduces attractiveness)
    comp01 = to01_from_z(zscore(mmx.get("competitive_intensity_index", 0)))
    comp_penalty = 1 - comp01

    # Logistics access supports serviceability
    log01 = to01_from_z(zscore(mmx.get("logistics_access_index", 0)))

    # Existing coverage is a negative for whitespace (but not for attractiveness)
    cov01 = mmx["coverage_index_0_1"].clip(0,1)

    # ---- Attractiveness score (0–100)
    # Weights tuned for international GTM expansion (editable later)
    score01 = (
        0.24*demand01 +
        0.18*growth01 +
        0.12*infra01 +
        0.10*cons01 +
        0.10*aff01 +
        0.08*ret01 +
        0.10*log01 +
        0.08*comp_penalty
    ).clip(0,1)

    mmx["attractiveness_score_0_100"] = (score01*100).round(1)

    # ---- White-space score (high potential, low coverage)
    whitespace01 = (0.65*score01 + 0.35*demand01) * (1 - cov01).clip(0,1)
    mmx["whitespace_score_0_100"] = (whitespace01*100).round(1)

    # ---- Recommended distributor density (simple first pass)
    # Density increases with demand + logistics ease + retail density
    density01 = (0.45*demand01 + 0.35*ret01 + 0.20*log01).clip(0,1)
    # map to a count range 0–3 (can be scaled by country later)
    mmx["recommended_distributor_count"] = (density01*3).round().astype(int)

    # ---- Coverage gap (how many more distributors needed)
    # approximate current distributor count per micro-market
    current_count = pd.DataFrame()
    if not dist.empty and "assigned_micro_market_id" in dist.columns:
        current_count = dist.groupby("assigned_micro_market_id")["distributor_id"].nunique().reset_index()
        current_count = current_count.rename(columns={"assigned_micro_market_id":"micro_market_id","distributor_id":"current_distributor_count"})
    else:
        current_count = pd.DataFrame({"micro_market_id": mmx["micro_market_id"].unique(), "current_distributor_count": 0})

    mmx = mmx.merge(current_count, on="micro_market_id", how="left")
    mmx["current_distributor_count"] = pd.to_numeric(mmx.get("current_distributor_count", 0), errors="coerce").fillna(0).astype(int)

    mmx["distributor_gap"] = (mmx["recommended_distributor_count"] - mmx["current_distributor_count"]).clip(lower=0).astype(int)

    # ---- Explanation strings (CEO-friendly, deterministic)
    def why_row(r):
        drivers = []
        if r.get("demand_proxy_index", 0) >= mmx["demand_proxy_index"].median():
            drivers.append("strong demand")
        if r.get("growth_proxy_index", 0) >= mmx["growth_proxy_index"].median():
            drivers.append("high growth")
        if r.get("construction_velocity_index", 0) >= mmx["construction_velocity_index"].median():
            drivers.append("construction momentum")
        if r.get("logistics_access_index", 0) >= mmx["logistics_access_index"].median():
            drivers.append("serviceability")
        if r.get("competitive_intensity_index", 0) <= mmx["competitive_intensity_index"].median():
            drivers.append("lower competition")
        if r.get("coverage_index_0_1", 0) < 0.35:
            drivers.append("low current coverage")
        if not drivers:
            drivers = ["balanced indicators"]
        return " | ".join(drivers[:4])

    mmx["why_now"] = mmx.apply(why_row, axis=1)

    # ---- Readiness score (data completeness)
    required = [
        "population_index","affluence_index","construction_velocity_index","infrastructure_spend_index",
        "retail_density_index","competitive_intensity_index","logistics_access_index","demand_proxy_index","growth_proxy_index"
    ]
    present = mmx[required].notna().sum(axis=1)
    mmx["data_readiness_0_100"] = (present / len(required) * 100).round(0).astype(int)

    # ---- Write artifacts
    os.makedirs("out", exist_ok=True)
    mmx.to_csv("out/micromarket_scored.csv", index=False)

    top_ws = mmx.sort_values(["whitespace_score_0_100","attractiveness_score_0_100"], ascending=False).head(25)
    top_ws.to_csv("out/micromarket_recommendations.csv", index=False)

    summary = {
        "as_of": str(datetime.now().date()),
        "micro_markets": int(mmx["micro_market_id"].nunique()),
        "avg_attractiveness": float(mmx["attractiveness_score_0_100"].mean()) if len(mmx) else 0.0,
        "avg_whitespace": float(mmx["whitespace_score_0_100"].mean()) if len(mmx) else 0.0,
        "total_gap": int(mmx["distributor_gap"].sum()),
        "coverage_avg": float(mmx["coverage_index_0_1"].mean()) if len(mmx) else 0.0
    }
    with open("out/micromarket_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("OK: out/micromarket_scored.csv")
    print("OK: out/micromarket_recommendations.csv")
    print("OK: out/micromarket_summary.json")

if __name__ == "__main__":
    main(demo_if_missing=True)
