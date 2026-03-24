#!/usr/bin/env python3
import argparse, os, json
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

STAGE_ORDER = ["Target", "Qualification", "Technical", "Proposal", "Negotiation", "Won", "Lost"]

REQUIRED_COLS = [
    "opportunity_id","account_name","account_type","vertical","market","country","owner","stage",
    "created_date","last_activity_date","expected_close_date",
    "potential_annual_value_local","currency","win_probability_pct"
]

def _parse_date(x):
    if pd.isna(x) or str(x).strip()=="":
        return pd.NaT
    return pd.to_datetime(x, errors="coerce")

def _num(x, default=0.0):
    try:
        v = pd.to_numeric(x, errors="coerce")
        if pd.isna(v): return float(default)
        return float(v)
    except Exception:
        return float(default)

def validate(df: pd.DataFrame) -> list[str]:
    errs=[]
    missing=[c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        errs.append(f"Missing required columns: {missing}")

    # Validate stages
    if "stage" in df.columns:
        bad = df[~df["stage"].astype(str).isin(STAGE_ORDER)]
        if len(bad)>0:
            errs.append(f"Invalid stage values found. Allowed: {STAGE_ORDER}")

    # Dates
    for c in ["created_date","last_activity_date","expected_close_date"]:
        if c in df.columns:
            if df[c].isna().all():
                errs.append(f"All values missing/invalid in {c}")

    # Value
    if "potential_annual_value_local" in df.columns:
        vals = pd.to_numeric(df["potential_annual_value_local"], errors="coerce")
        if (vals<=0).sum() > 0:
            errs.append("potential_annual_value_local has non-positive values (must be >0).")

    # Probability
    if "win_probability_pct" in df.columns:
        p = pd.to_numeric(df["win_probability_pct"], errors="coerce")
        if ((p<0) | (p>100)).sum() > 0:
            errs.append("win_probability_pct out of bounds (0–100).")

    return errs

def enrich(df: pd.DataFrame, as_of: str | None = None) -> tuple[pd.DataFrame, dict]:
    d = df.copy()

    # Normalize types
    d["created_date"] = d["created_date"].apply(_parse_date)
    d["last_activity_date"] = d["last_activity_date"].apply(_parse_date)
    d["expected_close_date"] = d["expected_close_date"].apply(_parse_date)

    d["potential_annual_value_local"] = pd.to_numeric(d["potential_annual_value_local"], errors="coerce").fillna(0.0)
    d["win_probability_pct"] = pd.to_numeric(d["win_probability_pct"], errors="coerce").fillna(0.0).clip(0,100)

    # As-of (defaults to today)
    as_of_dt = pd.to_datetime(as_of, errors="coerce") if as_of else pd.Timestamp(datetime.now().date())
    if pd.isna(as_of_dt):
        as_of_dt = pd.Timestamp(datetime.now().date())

    # Derived
    d["win_probability_01"] = (d["win_probability_pct"]/100.0).clip(0,1)
    d["expected_value_local"] = d["potential_annual_value_local"] * d["win_probability_01"]

    d["days_since_last_activity"] = (as_of_dt - d["last_activity_date"]).dt.days
    d["days_to_close"] = (d["expected_close_date"] - as_of_dt).dt.days

    # SLA rules (adjustable, but deterministic)
    # - Proposal/Negotiation: SLA 7 days
    # - Qualification/Technical: SLA 14 days
    # - Target: SLA 21 days
    # - Won/Lost: no SLA
    sla_map = {
        "Proposal":7, "Negotiation":7,
        "Qualification":14, "Technical":14,
        "Target":21,
        "Won":9999, "Lost":9999
    }
    d["sla_days"] = d["stage"].map(sla_map).fillna(14).astype(int)
    d["sla_breached"] = (d["days_since_last_activity"].fillna(9999) > d["sla_days"]) & (~d["stage"].isin(["Won","Lost"]))

    # Next Action classification (simple + explainable)
    def next_action(row):
        if row["stage"] in ["Won","Lost"]:
            return "Closed"
        if row["sla_breached"]:
            return "Overdue follow-up"
        if row["stage"] == "Target":
            return "Schedule first meeting"
        if row["stage"] == "Qualification":
            return "Complete qualification pack"
        if row["stage"] == "Technical":
            return "Complete technical validation"
        if row["stage"] == "Proposal":
            return "Proposal push + approvals"
        if row["stage"] == "Negotiation":
            return "Close negotiation / unblock"
        return "Follow-up"
    d["next_action"] = d.apply(next_action, axis=1)

    # Deal Quality Score (0–100) — deterministic
    # Factors:
    #   - Probability (50%)
    #   - Stage maturity (25%)
    #   - Freshness (25%)
    stage_score_map = {
        "Target":20, "Qualification":35, "Technical":50, "Proposal":65, "Negotiation":78, "Won":95, "Lost":5
    }
    d["stage_score"] = d["stage"].map(stage_score_map).fillna(40)

    freshness = 100 - (d["days_since_last_activity"].fillna(60).clip(0,60) * (100/60))
    d["freshness_score"] = freshness.clip(0,100)

    d["deal_quality_score_0_100"] = (
        0.50*d["win_probability_pct"] +
        0.25*d["stage_score"] +
        0.25*d["freshness_score"]
    ).round(1).clip(0,100)

    # KPI pack
    total_pipeline = float(d["potential_annual_value_local"].sum())
    weighted_pipeline = float(d["expected_value_local"].sum())
    active_deals = int((~d["stage"].isin(["Won","Lost"])).sum())
    overdue = int(d["sla_breached"].sum())
    quality_ratio = (weighted_pipeline/total_pipeline*100.0) if total_pipeline>0 else 0.0

    # Conversion proxy (from stage distribution)
    stage_counts = d["stage"].value_counts().to_dict()

    kpis = {
        "as_of": str(as_of_dt.date()),
        "pipeline_total_local": total_pipeline,
        "pipeline_weighted_local": weighted_pipeline,
        "pipeline_quality_ratio_pct": round(quality_ratio, 1),
        "active_deals": active_deals,
        "overdue_actions": overdue,
        "stage_counts": stage_counts
    }

    # Sort order for UI
    d["stage_rank"] = d["stage"].apply(lambda s: STAGE_ORDER.index(s) if s in STAGE_ORDER else 99)
    d = d.sort_values(["sla_breached","deal_quality_score_0_100","expected_value_local"], ascending=[False, False, False])

    return d, kpis

def demo_data(n=24) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    stages = ["Target","Qualification","Technical","Proposal","Negotiation","Won","Lost"]
    probs = {"Target":20,"Qualification":35,"Technical":48,"Proposal":62,"Negotiation":74,"Won":100,"Lost":0}

    today = pd.Timestamp(datetime.now().date())
    rows=[]
    for i in range(n):
        stg = rng.choice(stages, p=[.18,.18,.16,.18,.14,.10,.06])
        created = today - pd.Timedelta(days=int(rng.integers(20,120)))
        last_act = today - pd.Timedelta(days=int(abs(rng.normal(9,6))))
        close = today + pd.Timedelta(days=int(rng.integers(10,110)))
        val = float(rng.integers(250_000, 2_800_000))
        rows.append({
            "opportunity_id": f"HNT-{i+1:04d}",
            "account_name": rng.choice(["OEM Alpha","EPC Beta","Developer Gamma","PanelBuilder Delta"]),
            "account_type": rng.choice(["OEM","EPC","Developer","Panel Builder"]),
            "vertical": rng.choice(["Switchgear","Cables","Motors","Lighting Pro","Solar"]),
            "market": rng.choice(["UAE","KSA","Qatar","Oman","Singapore","Indonesia"]),
            "country": rng.choice(["UAE","KSA","Qatar","Oman","Singapore","Indonesia"]),
            "owner": rng.choice(["Owner A","Owner B","Owner C"]),
            "stage": stg,
            "created_date": str(created.date()),
            "last_activity_date": str(last_act.date()),
            "expected_close_date": str(close.date()),
            "potential_annual_value_local": val,
            "currency": rng.choice(["AED","SAR","QAR","OMR","SGD","IDR"]),
            "win_probability_pct": float(np.clip(probs[stg] + rng.normal(0,10), 0, 100)),
            "quoted_price_index_vs_list": float(np.clip(rng.normal(0.95,0.05), 0.75, 1.10)),
            "discount_pct": float(np.clip(rng.normal(8,4), 0, 25)),
            "margin_floor_pct": 16.0,
            "expected_gm_pct": float(np.clip(rng.normal(18,4), 5, 35)),
            "logistics_cost_pct": float(np.clip(rng.normal(3.5,1.2), 0, 10)),
            "fx_assumption": 1.0,
            "payment_terms_days": int(rng.choice([30,45,60,90])),
            "notes": ""
        })
    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/hunting_opportunities.csv")
    ap.add_argument("--out_csv", default="out/hunting_enriched.csv")
    ap.add_argument("--out_kpis", default="out/hunting_kpis.json")
    ap.add_argument("--as_of", default=None, help="YYYY-MM-DD (optional)")
    ap.add_argument("--demo_if_missing", action="store_true")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    os.makedirs(os.path.dirname(args.out_kpis), exist_ok=True)

    if not os.path.exists(args.inp):
        if args.demo_if_missing:
            df = demo_data()
        else:
            raise SystemExit(f"ERROR: input not found: {args.inp} (use --demo_if_missing)")
    else:
        df = pd.read_csv(args.inp)

    # Validate
    errs = validate(df)
    if errs:
        print("VALIDATION ERRORS:")
        for e in errs:
            print("-", e)
        raise SystemExit("Fix input file issues before running enrich.")

    enriched, kpis = enrich(df, as_of=args.as_of)

    enriched.to_csv(args.out_csv, index=False)
    with open(args.out_kpis, "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=2)

    print(f"OK: wrote {args.out_csv}")
    print(f"OK: wrote {args.out_kpis}")

if __name__ == "__main__":
    main()
