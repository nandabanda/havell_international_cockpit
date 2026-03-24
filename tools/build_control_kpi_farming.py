#!/usr/bin/env python3
import os
import json
import argparse
from datetime import datetime
import pandas as pd
import numpy as np

OUT_DIR = "out"

def read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def read_json(path: str):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    except Exception:
        return {}

def pick_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def ensure_week_id(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "week_id" in df.columns:
        df["week_id"] = df["week_id"].astype(str)
        return df

    # Try a date column
    date_col = pick_col(df, ["week_start", "week", "date", "week_date", "period_start", "period"])
    if date_col:
        d = pd.to_datetime(df[date_col], errors="coerce")
        # ISO year-week: YYYY-Www
        iso = d.dt.isocalendar()
        df["week_id"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
        return df

    # Fallback: single "current week"
    now = datetime.now()
    iso = now.isocalendar()
    df["week_id"] = f"{iso.year}-W{int(iso.week):02d}"
    return df

def build_from_weekly_sku(weekly: pd.DataFrame) -> pd.DataFrame:
    if weekly.empty:
        return pd.DataFrame()

    weekly = weekly.copy()
    weekly = ensure_week_id(weekly)

    # Revenue / Spend / Margin candidates (choose what exists)
    rev_col = pick_col(weekly, [
        "revenue", "sales_value", "sell_in_value", "sellout_value", "net_sales", "nsr_value",
        "invoice_value", "value"
    ])
    spend_col = pick_col(weekly, [
        "spend", "trade_spend", "promo_spend", "discount_value", "rebate_value", "claims_value",
        "scheme_spend", "marketing_spend", "dme"
    ])
    gm_col = pick_col(weekly, [
        "gross_margin", "gm_value", "margin_value", "contribution", "contribution_value"
    ])
    profit_col = pick_col(weekly, [
        "profit", "net_profit", "pbt", "ebit", "contribution_after_spend"
    ])
    fill_col = pick_col(weekly, [
        "fill_rate", "service_level", "fillrate", "fill_rate_pct"
    ])
    otif_col = pick_col(weekly, [
        "otif", "otif_pct", "on_time_in_full", "otif_rate"
    ])
    doh_col = pick_col(weekly, [
        "doh", "days_of_holding", "days_cover", "doc", "days_of_cover"
    ])
    backorder_col = pick_col(weekly, [
        "backorders", "backorder_units", "bo_units", "open_backorders"
    ])

    g = weekly.groupby("week_id", dropna=False)

    out = pd.DataFrame({"week_id": list(g.size().index)}).sort_values("week_id")

    # Aggregations (sum for value metrics, mean for rates)
    if rev_col:
        out["revenue"] = g[rev_col].apply(lambda x: to_num(x).sum(min_count=1)).values
    else:
        out["revenue"] = 0.0

    if spend_col:
        out["spend"] = g[spend_col].apply(lambda x: to_num(x).sum(min_count=1)).values
    else:
        out["spend"] = 0.0

    if gm_col:
        out["gross_margin"] = g[gm_col].apply(lambda x: to_num(x).sum(min_count=1)).values
    else:
        # If GM not provided but revenue exists, keep blank for now (0); we will proxy later only if needed.
        out["gross_margin"] = 0.0

    if profit_col:
        out["profit"] = g[profit_col].apply(lambda x: to_num(x).sum(min_count=1)).values
    else:
        out["profit"] = 0.0

    if fill_col:
        out["fill_rate"] = g[fill_col].apply(lambda x: to_num(x).mean()).values
    else:
        out["fill_rate"] = np.nan

    if otif_col:
        out["otif"] = g[otif_col].apply(lambda x: to_num(x).mean()).values
    else:
        out["otif"] = np.nan

    if doh_col:
        out["doh"] = g[doh_col].apply(lambda x: to_num(x).mean()).values
    else:
        out["doh"] = np.nan

    if backorder_col:
        out["backorders"] = g[backorder_col].apply(lambda x: to_num(x).sum(min_count=1)).values
    else:
        out["backorders"] = np.nan

    return out

def add_stress_and_actions(kpi: pd.DataFrame, stress: pd.DataFrame, actions: pd.DataFrame) -> pd.DataFrame:
    kpi = kpi.copy()
    if kpi.empty:
        return kpi

    # Stress metrics
    if not stress.empty:
        stress = stress.copy()
        stress = ensure_week_id(stress)

        var_col = pick_col(stress, ["value_at_risk", "risk_value", "value_risk", "var_value"])
        sev_col = pick_col(stress, ["severity", "risk_score", "stress_score"])
        exc_flag_col = pick_col(stress, ["is_exception", "exception", "flag_exception"])

        sg = stress.groupby("week_id", dropna=False)
        if var_col:
            var_series = sg[var_col].apply(lambda x: to_num(x).sum(min_count=1))
            kpi = kpi.merge(var_series.rename("value_at_risk"), on="week_id", how="left")
        else:
            kpi["value_at_risk"] = kpi.get("value_at_risk", np.nan)

        # exceptions count
        if exc_flag_col:
            exc = sg[exc_flag_col].apply(lambda x: (to_num(x).fillna(0) > 0).sum())
            kpi = kpi.merge(exc.rename("exceptions"), on="week_id", how="left")
        elif sev_col:
            exc = sg[sev_col].apply(lambda x: (to_num(x).fillna(0) >= 70).sum())
            kpi = kpi.merge(exc.rename("exceptions"), on="week_id", how="left")
        else:
            kpi["exceptions"] = kpi.get("exceptions", np.nan)
    else:
        if "value_at_risk" not in kpi.columns:
            kpi["value_at_risk"] = np.nan
        if "exceptions" not in kpi.columns:
            kpi["exceptions"] = np.nan

    # Actions count
    if not actions.empty:
        actions = actions.copy()
        actions = ensure_week_id(actions)
        ag = actions.groupby("week_id", dropna=False).size()
        kpi = kpi.merge(ag.rename("actions_count"), on="week_id", how="left")
    else:
        if "actions_count" not in kpi.columns:
            kpi["actions_count"] = np.nan

    return kpi

def finalize(kpi: pd.DataFrame) -> pd.DataFrame:
    kpi = kpi.copy()
    if kpi.empty:
        # Create a single-row stub so charts don't die
        now = datetime.now().isocalendar()
        kpi = pd.DataFrame([{
            "week_id": f"{now.year}-W{int(now.week):02d}",
            "revenue": 0.0,
            "spend": 0.0,
            "gross_margin": 0.0,
            "profit": 0.0,
            "gm_pct": 0.0,
        }])
        return kpi

    # If gross_margin is missing but revenue exists, apply a conservative proxy ONLY when needed
    # (This avoids all-zero waterfalls if the input files have revenue but no GM columns.)
    gm_zero = (pd.to_numeric(kpi["gross_margin"], errors="coerce").fillna(0) == 0)
    rev_pos = (pd.to_numeric(kpi["revenue"], errors="coerce").fillna(0) > 0)
    if gm_zero.any() and rev_pos.any():
        proxy_rate = 0.22  # conservative FMCG proxy; replace later with real GM
        kpi.loc[gm_zero & rev_pos, "gross_margin"] = pd.to_numeric(kpi.loc[gm_zero & rev_pos, "revenue"], errors="coerce").fillna(0) * proxy_rate

    # If profit missing but we have GM and spend, proxy profit = GM - spend
    pr_zero = (pd.to_numeric(kpi["profit"], errors="coerce").fillna(0) == 0)
    gm_pos = (pd.to_numeric(kpi["gross_margin"], errors="coerce").fillna(0) > 0)
    if pr_zero.any() and gm_pos.any():
        kpi.loc[pr_zero & gm_pos, "profit"] = (
            pd.to_numeric(kpi.loc[pr_zero & gm_pos, "gross_margin"], errors="coerce").fillna(0)
            - pd.to_numeric(kpi.loc[pr_zero & gm_pos, "spend"], errors="coerce").fillna(0)
        ).clip(lower=0)

    # GM%
    rev = pd.to_numeric(kpi["revenue"], errors="coerce").fillna(0)
    gm = pd.to_numeric(kpi["gross_margin"], errors="coerce").fillna(0)
    kpi["gm_pct"] = np.where(rev > 0, (gm / rev) * 100.0, 0.0)

    # Fill sensible defaults
    for c in ["fill_rate", "otif", "doh", "backorders", "value_at_risk", "exceptions", "actions_count"]:
        if c not in kpi.columns:
            kpi[c] = np.nan

    # Sort
    kpi["week_id"] = kpi["week_id"].astype(str)
    kpi = kpi.sort_values("week_id").reset_index(drop=True)
    return kpi

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    weekly = read_csv(os.path.join(out_dir, "farming_sku_weekly.csv"))
    dist = read_csv(os.path.join(out_dir, "farming_distributor_summary.csv"))  # not required for KPI cube right now
    stress = read_csv(os.path.join(out_dir, "supply_stress_sku.csv"))
    actions = read_csv(os.path.join(out_dir, "supply_resolution_actions.csv"))
    net = read_json(os.path.join(out_dir, "farming_network_summary.json"))

    kpi = build_from_weekly_sku(weekly)

    # If we still have nothing (weekly missing), attempt fallback: distributor summary aggregated (if it has week_id)
    if kpi.empty and not dist.empty:
        dist2 = ensure_week_id(dist.copy())
        rev_col = pick_col(dist2, ["revenue", "sales_value", "sell_in_value", "net_sales", "nsr_value"])
        spend_col = pick_col(dist2, ["spend", "trade_spend", "promo_spend", "discount_value", "dme"])
        gm_col = pick_col(dist2, ["gross_margin", "gm_value", "contribution"])
        g = dist2.groupby("week_id", dropna=False)
        kpi = pd.DataFrame({"week_id": list(g.size().index)}).sort_values("week_id")
        kpi["revenue"] = g[rev_col].apply(lambda x: to_num(x).sum(min_count=1)).values if rev_col else 0.0
        kpi["spend"] = g[spend_col].apply(lambda x: to_num(x).sum(min_count=1)).values if spend_col else 0.0
        kpi["gross_margin"] = g[gm_col].apply(lambda x: to_num(x).sum(min_count=1)).values if gm_col else 0.0
        kpi["profit"] = 0.0

    # Add stress/actions overlays
    kpi = add_stress_and_actions(kpi, stress, actions)

    # Add a couple network summary fields if useful (won't break anything)
    if isinstance(net, dict) and net:
        # These are optional and safe
        for key in ["active_distributors", "active_skus", "service_pulse", "notes"]:
            if key in net:
                kpi[key] = net[key]

    kpi = finalize(kpi)

    out_path = os.path.join(out_dir, "control_kpi_farming.csv")
    kpi.to_csv(out_path, index=False)

    print(f"OK: wrote {out_path} ({len(kpi)} rows)")
    print("Columns:", ", ".join(kpi.columns.tolist()))
    print(kpi.tail(5).to_string(index=False))

if __name__ == "__main__":
    main()
