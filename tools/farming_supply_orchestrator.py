#!/usr/bin/env python3
"""
Integrated Farming + Supply Orchestrator (Weekly)
Assumptions:
- Weekly SKU-level sell-in + weekly inventory snapshot per distributor
- No sell-out; velocity is reconstructed
- Dynamic Target DoC based on volatility (CV)
- Multi-plant / regional hub capacity planning: monthly plan + weekly execution using historical week pattern weights
- Supply resolution suggestions trigger at capacity stress >= 90%

Inputs (minimum):
- data/farming_sellin_weekly.csv
- data/farming_inventory_weekly.csv
- data/supply_capacity_monthly.csv

Optional inputs:
- data/supply_week_pattern.csv
- data/hub_inventory_weekly.csv
- out/hunting_forward_signal.csv

Outputs:
- out/farming_sku_weekly.csv
- out/farming_distributor_summary.csv
- out/farming_network_summary.json
- out/supply_stress_sku.csv
- out/supply_stress_plant.csv
- out/supply_resolution_actions.csv
- out/supply_resolution_summary.json
"""

from __future__ import annotations
import os, json, argparse
import numpy as np
import pandas as pd


def read_csv_safe(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def ensure_cols(df: pd.DataFrame, cols_defaults: dict) -> pd.DataFrame:
    for c, d in cols_defaults.items():
        if c not in df.columns:
            df[c] = d
    return df


def to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def clamp_series(s: pd.Series, lo: float, hi: float) -> pd.Series:
    return s.fillna(lo).clip(lo, hi)


def week_key_normalize(df: pd.DataFrame, week_col: str = "week_id") -> pd.DataFrame:
    if week_col in df.columns:
        df[week_col] = df[week_col].astype(str)
    return df


def rolling_cv(x: pd.Series, window: int = 8) -> pd.Series:
    mu = x.rolling(window, min_periods=max(3, window // 2)).mean()
    sd = x.rolling(window, min_periods=max(3, window // 2)).std()
    cv = sd / (mu.abs() + 1e-9)
    return cv.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def band_doc(doc: float) -> str:
    if pd.isna(doc):
        return "Unknown"
    if doc < 21:
        return "Stock Risk"
    if doc < 45:
        return "Healthy"
    if doc < 70:
        return "Capital Heavy"
    return "Excess"


def stress_band(u: float) -> str:
    if pd.isna(u):
        return "Unknown"
    if u < 0.70:
        return "Underutilized"
    if u < 0.90:
        return "Normal"
    if u <= 1.00:
        return "Tight"
    return "Overload"


def build_farming(
    sellin: pd.DataFrame,
    inv: pd.DataFrame,
    target_base_doc: float = 40.0,
    volatility_mult: float = 15.0,
    volatility_cap: float = 20.0,
    reorder_min_qty: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:

    sellin = week_key_normalize(sellin)
    inv = week_key_normalize(inv)

    sellin = ensure_cols(sellin, {
        "week_id": "",
        "distributor_id": "",
        "sku_id": "",
        "sell_in_qty": 0.0,
        "sell_in_value": np.nan,
        "buy_price": np.nan,
    })
    inv = ensure_cols(inv, {
        "week_id": "",
        "distributor_id": "",
        "sku_id": "",
        "opening_inventory_qty": np.nan,
        "closing_inventory_qty": np.nan,
        "in_transit_qty": 0.0,
        "unit_cost": np.nan,
    })

    sellin = to_numeric(sellin, ["sell_in_qty", "sell_in_value", "buy_price"])
    inv = to_numeric(inv, ["opening_inventory_qty", "closing_inventory_qty", "in_transit_qty", "unit_cost"])

    base = pd.merge(
        sellin,
        inv,
        on=["week_id", "distributor_id", "sku_id"],
        how="outer",
        suffixes=("", "_inv"),
    )

    base = ensure_cols(base, {
        "sell_in_qty": 0.0,
        "opening_inventory_qty": np.nan,
        "closing_inventory_qty": np.nan,
        "in_transit_qty": 0.0,
        "unit_cost": np.nan,
    })

    base["week_id"] = base["week_id"].astype(str)
    base = base.sort_values(["distributor_id", "sku_id", "week_id"]).reset_index(drop=True)

    base["implied_sellout_qty"] = (
        base["opening_inventory_qty"].fillna(0.0)
        + base["sell_in_qty"].fillna(0.0)
        - base["closing_inventory_qty"].fillna(0.0)
    ).clip(0.0, None)

    base["vel_4w"] = base.groupby(["distributor_id", "sku_id"])["implied_sellout_qty"] \
        .transform(lambda s: s.rolling(4, min_periods=2).mean())

    base["vel_12w"] = base.groupby(["distributor_id", "sku_id"])["implied_sellout_qty"] \
        .transform(lambda s: s.rolling(12, min_periods=4).mean())

    base["vel_cv_8w"] = base.groupby(["distributor_id", "sku_id"])["implied_sellout_qty"] \
        .transform(lambda s: rolling_cv(s, window=8))

    base["target_doc"] = target_base_doc + clamp_series(volatility_mult * base["vel_cv_8w"], 0.0, volatility_cap)

    base["vel_weekly_effective"] = base["vel_4w"].fillna(base["vel_12w"]).fillna(0.0)
    base["vel_daily_effective"] = (base["vel_weekly_effective"] / 7.0).fillna(0.0)

    base["inv_effective_qty"] = base["closing_inventory_qty"].fillna(0.0) + base["in_transit_qty"].fillna(0.0)

    base["doc"] = np.where(
        base["vel_daily_effective"] > 1e-9,
        base["inv_effective_qty"] / base["vel_daily_effective"],
        np.nan,
    )
    base["doc_band"] = base["doc"].apply(band_doc)

    base["reorder_qty_reco"] = np.where(
        (base["doc"].notna()) & (base["doc"] < base["target_doc"]) & (base["vel_daily_effective"] > 0),
        (base["target_doc"] - base["doc"]) * base["vel_daily_effective"],
        0.0,
    ).clip(reorder_min_qty, None)

    base["excess_qty"] = np.where(
        (base["doc"].notna()) & (base["doc"] > base["target_doc"]) & (base["vel_daily_effective"] > 0),
        (base["doc"] - base["target_doc"]) * base["vel_daily_effective"],
        0.0,
    ).clip(0.0, None)

    base["unit_cost"] = base["unit_cost"].fillna(base["buy_price"]).fillna(0.0)
    base["capital_locked_value"] = base["excess_qty"] * base["unit_cost"]

    dist = base.groupby(["week_id", "distributor_id"]).agg(
        skus=("sku_id", "nunique"),
        total_sellin_qty=("sell_in_qty", "sum"),
        total_implied_sellout_qty=("implied_sellout_qty", "sum"),
        total_reorder_qty=("reorder_qty_reco", "sum"),
        total_capital_locked=("capital_locked_value", "sum"),
        pct_skus_stock_risk=("doc_band", lambda s: float((s == "Stock Risk").mean()) if len(s) else 0.0),
        pct_skus_excess=("doc_band", lambda s: float((s == "Excess").mean()) if len(s) else 0.0),
    ).reset_index()

    tmp = base.copy()
    tmp["inv_weight"] = tmp["inv_effective_qty"].fillna(0.0)
    tmp["doc_for_weight"] = tmp["doc"].fillna(0.0)
    wdoc = tmp.groupby(["week_id", "distributor_id"]).apply(
        lambda g: float((g["doc_for_weight"] * g["inv_weight"]).sum() / (g["inv_weight"].sum() + 1e-9))
    ).reset_index(name="weighted_doc")
    dist = dist.merge(wdoc, on=["week_id", "distributor_id"], how="left")

    dist["inv_balance_score"] = (1.0 - (dist["pct_skus_excess"] + dist["pct_skus_stock_risk"]) / 2.0).clip(0, 1) * 100
    dist["rhythm_score"] = np.where(dist["total_sellin_qty"] > 0, 80.0, 50.0)
    dist["momentum_score"] = np.where(dist["total_implied_sellout_qty"] > 0, 80.0, 55.0)

    dist["health_score_0_100"] = (
        0.50 * dist["inv_balance_score"] +
        0.25 * dist["rhythm_score"] +
        0.25 * dist["momentum_score"]
    ).round(1)

    latest_week = dist["week_id"].astype(str).max() if len(dist) else ""
    latest = dist[dist["week_id"].astype(str) == str(latest_week)].copy()

    network = {
        "latest_week_id": str(latest_week),
        "distributors": int(latest["distributor_id"].nunique()) if len(latest) else 0,
        "network_weighted_doc": float(latest["weighted_doc"].mean()) if len(latest) else None,
        "total_capital_locked": float(latest["total_capital_locked"].sum()) if len(latest) else 0.0,
        "avg_health_score": float(latest["health_score_0_100"].mean()) if len(latest) else None,
        "pct_skus_stock_risk_avg": float(latest["pct_skus_stock_risk"].mean()) if len(latest) else 0.0,
        "pct_skus_excess_avg": float(latest["pct_skus_excess"].mean()) if len(latest) else 0.0,
    }

    farming_cols = [
        "week_id","distributor_id","sku_id",
        "sell_in_qty","sell_in_value","buy_price",
        "opening_inventory_qty","closing_inventory_qty","in_transit_qty","inv_effective_qty",
        "implied_sellout_qty","vel_4w","vel_12w","vel_cv_8w",
        "target_doc","doc","doc_band",
        "reorder_qty_reco","excess_qty","unit_cost","capital_locked_value"
    ]
    for c in farming_cols:
        if c not in base.columns:
            base[c] = np.nan

    return base[farming_cols].copy(), dist.copy(), network


def build_supply(
    farming_sku_weekly: pd.DataFrame,
    supply_capacity_monthly: pd.DataFrame,
    supply_week_pattern: pd.DataFrame,
    hunting_forward: pd.DataFrame,
    stress_threshold: float = 0.90,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:

    cap = ensure_cols(supply_capacity_monthly, {
        "month_id": "",
        "plant_id": "",
        "sku_id": "",
        "monthly_capacity_qty": 0.0,
        "primary_region": "",
        "secondary_plant_id": "",
    })
    cap = to_numeric(cap, ["monthly_capacity_qty"])
    cap["month_id"] = cap["month_id"].astype(str)
    cap["plant_id"] = cap["plant_id"].astype(str)
    cap["sku_id"] = cap["sku_id"].astype(str)

    pat = supply_week_pattern.copy()
    if pat.empty:
        pat = pd.DataFrame({"week_in_month":[1,2,3,4], "weight":[0.25,0.25,0.25,0.25]})
    pat = ensure_cols(pat, {"week_in_month": 1, "weight": 0.25})
    pat = to_numeric(pat, ["week_in_month","weight"])
    pat["week_in_month"] = pat["week_in_month"].fillna(1).astype(int)
    pat["weight"] = pat["weight"].fillna(0.25)
    wsum = pat["weight"].sum()
    pat["weight"] = pat["weight"] / (wsum + 1e-9)

    f = farming_sku_weekly.copy()
    f = ensure_cols(f, {"week_id": "", "sku_id": "", "reorder_qty_reco": 0.0})
    f["week_id"] = f["week_id"].astype(str)
    f["sku_id"] = f["sku_id"].astype(str)
    f = to_numeric(f, ["reorder_qty_reco"])
    demand_week_sku = f.groupby(["week_id","sku_id"]).agg(reorder_qty=("reorder_qty_reco","sum")).reset_index()

    h = hunting_forward.copy()
    if h.empty:
        h = pd.DataFrame(columns=["week_id","sku_id","demand_qty"])
    h = ensure_cols(h, {"week_id":"", "sku_id":"", "demand_qty":0.0})
    h["week_id"] = h["week_id"].astype(str)
    h["sku_id"] = h["sku_id"].astype(str)
    h = to_numeric(h, ["demand_qty"])
    hunting_week_sku = h.groupby(["week_id","sku_id"]).agg(hunting_qty=("demand_qty","sum")).reset_index()

    d = demand_week_sku.merge(hunting_week_sku, on=["week_id","sku_id"], how="left")
    d["hunting_qty"] = d["hunting_qty"].fillna(0.0)
    d["total_demand_qty"] = d["reorder_qty"].fillna(0.0) + d["hunting_qty"].fillna(0.0)

    def infer_month(week_id: str) -> str:
        s = str(week_id)
        if len(s) >= 7 and s[4] == "-" and s[6] == "-":
            return s[:7]  # YYYY-MM
        if "W" in s:
            return s[:4] + "-MUNK"
        return "MUNK"

    d["month_id"] = d["week_id"].apply(infer_month)
    d["week_in_month"] = 1
    try:
        dt = pd.to_datetime(d["week_id"], errors="coerce")
        wk = ((dt.dt.day - 1) // 7 + 1).clip(1, 4)
        d.loc[dt.notna(), "week_in_month"] = wk[dt.notna()].astype(int)
    except Exception:
        pass

    cap_primary = cap.copy()
    cap_primary["rank"] = cap_primary.groupby(["month_id","sku_id"])["monthly_capacity_qty"].rank(method="first", ascending=False)
    cap_primary = cap_primary[cap_primary["rank"] == 1].drop(columns=["rank"])

    cap_primary_w = cap_primary.assign(_k=1).merge(pat.assign(_k=1), on="_k").drop(columns=["_k"])
    cap_primary_w["weekly_capacity_qty"] = cap_primary_w["monthly_capacity_qty"] * cap_primary_w["weight"]

    d2 = d.merge(
        cap_primary_w[["month_id","plant_id","sku_id","week_in_month","weekly_capacity_qty","monthly_capacity_qty"]],
        on=["month_id","sku_id","week_in_month"],
        how="left"
    )

    d2["weekly_capacity_qty"] = d2["weekly_capacity_qty"].fillna(0.0)
    d2["plant_id"] = d2["plant_id"].fillna("UNKNOWN")

    d2["capacity_utilization"] = np.where(
        d2["weekly_capacity_qty"] > 1e-9,
        d2["total_demand_qty"] / d2["weekly_capacity_qty"],
        np.nan
    )
    d2["stress_band"] = d2["capacity_utilization"].apply(stress_band)

    supply_stress_sku = d2[[
        "week_id","month_id","week_in_month","plant_id","sku_id",
        "reorder_qty","hunting_qty","total_demand_qty","weekly_capacity_qty","capacity_utilization","stress_band"
    ]].copy()

    plant = supply_stress_sku.groupby(["week_id","plant_id"]).agg(
        total_demand=("total_demand_qty","sum"),
        total_capacity=("weekly_capacity_qty","sum"),
        max_util=("capacity_utilization","max"),
        skus_tight=("capacity_utilization", lambda s: int((s >= stress_threshold).sum())),
    ).reset_index()
    plant["utilization"] = np.where(plant["total_capacity"] > 1e-9, plant["total_demand"] / plant["total_capacity"], np.nan)
    plant["stress_band"] = plant["utilization"].apply(stress_band)

    tight = supply_stress_sku[supply_stress_sku["capacity_utilization"].fillna(0.0) >= stress_threshold].copy()
    actions = []
    if not tight.empty:
        tight["priority_score"] = (
            0.45 * (tight["hunting_qty"].fillna(0.0) / (tight["hunting_qty"].max() + 1e-9)) +
            0.35 * (tight["total_demand_qty"].fillna(0.0) / (tight["total_demand_qty"].max() + 1e-9)) +
            0.20 * (tight["capacity_utilization"].fillna(0.0) / (tight["capacity_utilization"].max() + 1e-9))
        ) * 100
        tight["priority_score"] = tight["priority_score"].round(1)

        for _, r in tight.sort_values(["week_id","priority_score"], ascending=[True, False]).iterrows():
            week_id = r["week_id"]; sku_id = r["sku_id"]; plant_id = r["plant_id"]
            util = r["capacity_utilization"]; demand = r["total_demand_qty"]; capw = r["weekly_capacity_qty"]

            actions.append({
                "week_id": week_id,
                "sku_id": sku_id,
                "plant_id": plant_id,
                "action_type": "PRIORITIZE_SKU",
                "severity": "HIGH" if util > 1.0 else "MEDIUM",
                "recommended_move": f"Prioritize SKU {sku_id} in allocation; protect Hunting volume first.",
                "notes": f"Util={util:.2f}, Demand={demand:.0f}, Cap={capw:.0f}"
            })

            if util > 1.0:
                excess = max(0.0, demand - capw)
                actions.append({
                    "week_id": week_id,
                    "sku_id": sku_id,
                    "plant_id": plant_id,
                    "action_type": "DELAY_VOLUME",
                    "severity": "HIGH",
                    "recommended_move": f"Delay ~{excess:.0f} units (non-critical replenishment) to next cycle.",
                    "notes": "Overload detected; delay replenishment volume while protecting strategic demand."
                })

            alt = cap[cap["sku_id"] == sku_id].copy()
            if not alt.empty:
                alt = alt[alt["plant_id"] != plant_id].sort_values("monthly_capacity_qty", ascending=False).head(1)
                if len(alt):
                    alt_plant = str(alt.iloc[0]["plant_id"])
                    actions.append({
                        "week_id": week_id,
                        "sku_id": sku_id,
                        "plant_id": plant_id,
                        "action_type": "REROUTE_PRODUCTION",
                        "severity": "MEDIUM" if util <= 1.0 else "HIGH",
                        "recommended_move": f"Shift part of SKU {sku_id} from {plant_id} to {alt_plant} (overflow routing).",
                        "notes": "Hybrid allocation: primary + overflow routing."
                    })

    resolution_actions = pd.DataFrame(actions)
    if resolution_actions.empty:
        resolution_actions = pd.DataFrame(columns=["week_id","sku_id","plant_id","action_type","severity","recommended_move","notes"])

    latest_week = supply_stress_sku["week_id"].astype(str).max() if len(supply_stress_sku) else ""
    sw = supply_stress_sku[supply_stress_sku["week_id"].astype(str) == str(latest_week)].copy()
    supply_summary = {
        "latest_week_id": str(latest_week),
        "plants": int(sw["plant_id"].nunique()) if len(sw) else 0,
        "skus": int(sw["sku_id"].nunique()) if len(sw) else 0,
        "tight_skus": int((sw["capacity_utilization"].fillna(0.0) >= stress_threshold).sum()) if len(sw) else 0,
        "max_sku_utilization": float(sw["capacity_utilization"].max()) if len(sw) else None,
        "total_demand_qty": float(sw["total_demand_qty"].sum()) if len(sw) else 0.0,
        "total_capacity_qty": float(sw["weekly_capacity_qty"].sum()) if len(sw) else 0.0,
        "resolution_actions": int(len(resolution_actions)),
        "stress_threshold": stress_threshold,
    }

    return supply_stress_sku, plant, resolution_actions, supply_summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sellin", default="data/farming_sellin_weekly.csv")
    ap.add_argument("--inventory", default="data/farming_inventory_weekly.csv")
    ap.add_argument("--capacity", default="data/supply_capacity_monthly.csv")
    ap.add_argument("--week_pattern", default="data/supply_week_pattern.csv")
    ap.add_argument("--hunting_forward", default="out/hunting_forward_signal.csv")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--stress_threshold", type=float, default=0.90)
    ap.add_argument("--target_base_doc", type=float, default=40.0)
    ap.add_argument("--volatility_mult", type=float, default=15.0)
    ap.add_argument("--volatility_cap", type=float, default=20.0)
    ap.add_argument("--demo_if_missing", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    sellin = read_csv_safe(args.sellin)
    inv = read_csv_safe(args.inventory)
    cap = read_csv_safe(args.capacity)
    pat = read_csv_safe(args.week_pattern)
    hunt = read_csv_safe(args.hunting_forward)

    if args.demo_if_missing and (sellin.empty or inv.empty or cap.empty):
        print("DEMO: generating minimal demo inputs under data/ ...")
        os.makedirs("data", exist_ok=True)
        weeks = pd.date_range("2026-02-02", periods=6, freq="W-MON").strftime("%Y-%m-%d").tolist()
        dist_ids = ["D001","D002","D003"]
        skus = ["SKU_A","SKU_B","SKU_C","SKU_D"]
        rng = np.random.default_rng(7)
        rows_s, rows_i = [], []
        for w in weeks:
            for d in dist_ids:
                for s in skus:
                    sellin_qty = float(max(0, rng.normal(120, 35)))
                    rows_s.append([w,d,s,round(sellin_qty,0), round(sellin_qty*100,2), 100.0])
                    open_inv = float(max(0, rng.normal(300, 80)))
                    close_inv = float(max(0, open_inv + sellin_qty - rng.normal(110, 25)))
                    rows_i.append([w,d,s,round(open_inv,0), round(close_inv,0), 0.0, 75.0])

        pd.DataFrame(rows_s, columns=["week_id","distributor_id","sku_id","sell_in_qty","sell_in_value","buy_price"]).to_csv(args.sellin, index=False)
        pd.DataFrame(rows_i, columns=["week_id","distributor_id","sku_id","opening_inventory_qty","closing_inventory_qty","in_transit_qty","unit_cost"]).to_csv(args.inventory, index=False)
        cap_demo = pd.DataFrame([
            ["2026-02","P1","SKU_A", 1800,"","P2"],
            ["2026-02","P1","SKU_B", 1600,"","P2"],
            ["2026-02","P2","SKU_C", 1400,"","P1"],
            ["2026-02","P2","SKU_D", 1200,"","P1"],
            ["2026-03","P1","SKU_A", 1900,"","P2"],
            ["2026-03","P1","SKU_B", 1700,"","P2"],
            ["2026-03","P2","SKU_C", 1500,"","P1"],
            ["2026-03","P2","SKU_D", 1300,"","P1"],
        ], columns=["month_id","plant_id","sku_id","monthly_capacity_qty","primary_region","secondary_plant_id"])
        cap_demo.to_csv(args.capacity, index=False)

        pd.DataFrame({"week_in_month":[1,2,3,4], "weight":[0.24,0.26,0.25,0.25]}).to_csv(args.week_pattern, index=False)

        os.makedirs("out", exist_ok=True)
        pd.DataFrame([[weeks[2],"SKU_A",150],[weeks[3],"SKU_B",120]], columns=["week_id","sku_id","demand_qty"]).to_csv(args.hunting_forward, index=False)

        sellin = read_csv_safe(args.sellin)
        cap = read_csv_safe(args.capacity)
        pat = read_csv_safe(args.week_pattern)
        hunt = read_csv_safe(args.hunting_forward)

    if sellin.empty or inv.empty:
        raise SystemExit("ERROR: Provide data/farming_sellin_weekly.csv and data/farming_inventory_weekly.csv (or run with --demo_if_missing).")
    if cap.empty:
        raise SystemExit("ERROR: Provide data/supply_capacity_monthly.csv (or run with --demo_if_missing).")

    farming_sku, farming_dist, farming_net = build_farming(
        sellin=sellin,
        inv=inv,
        target_base_doc=args.target_base_doc,
        volatility_mult=args.volatility_mult,
        volatility_cap=args.volatility_cap,
    )
    supply_sku, supply_plant, resolution, supply_sum = build_supply(
        farming_sku_weekly=farming_sku,
        supply_capacity_monthly=cap,
        supply_week_pattern=pat,
        hunting_forward=hunt,
        stress_threshold=args.stress_threshold,
    )

    farming_sku.to_csv(os.path.join(args.outdir, "farming_sku_weekly.csv"), index=False)
    farming_dist.to_csv(os.path.join(args.outdir, "farming_distributor_summary.csv"), index=False)
    with open(os.path.join(args.outdir, "farming_network_summary.json"), "w") as f:
        json.dump(farming_net, f, indent=2)

    supply_sku.to_csv(os.path.join(args.outdir, "supply_stress_sku.csv"), index=False)
    supply_plant.to_csv(os.path.join(args.outdir, "supply_stress_plant.csv"), index=False)
    resolution.to_csv(os.path.join(args.outdir, "supply_resolution_actions.csv"), index=False)
    with open(os.path.join(args.outdir, "supply_resolution_summary.json"), "w") as f:
        json.dump(supply_sum, f, indent=2)

    print("OK: wrote farming + supply artifacts to", args.outdir)


if __name__ == "__main__":
    main()
