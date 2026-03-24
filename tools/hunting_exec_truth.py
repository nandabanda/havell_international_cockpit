#!/usr/bin/env python3
import os, json
import pandas as pd
from datetime import datetime

STAGE_ORDER = ["Target","Qualification","Technical","Proposal","Negotiation","Won","Lost"]

def _read_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

def _to_dt(s):
    return pd.to_datetime(s, errors="coerce")

def main():
    opp_path = "out/hunting_enriched.csv"
    stage_metrics_path = "out/hunting_stage_metrics.json"
    events_path = "data/hunting_stage_events.csv"
    approvals_path = "data/hunting_proposal_approvals.csv"

    if not os.path.exists(opp_path):
        raise SystemExit("Missing out/hunting_enriched.csv. Run: python3 tools/hunting_enrich.py --demo_if_missing")

    opp = pd.read_csv(opp_path)
    opp["expected_close_date"] = _to_dt(opp.get("expected_close_date"))
    opp["last_activity_date"] = _to_dt(opp.get("last_activity_date"))

    stage_metrics = json.load(open(stage_metrics_path)) if os.path.exists(stage_metrics_path) else {}
    avg_stage_days = stage_metrics.get("avg_stage_days", {}) or {}

    # -------- 1) Closure forecast (30/60/90)
    as_of = pd.Timestamp(datetime.now().date())
    f = opp[~opp["stage"].isin(["Won","Lost"])].copy()
    f["days_to_close"] = (f["expected_close_date"] - as_of).dt.days

    def bucket(d):
        if pd.isna(d): return "Unknown"
        if d <= 30: return "0-30"
        if d <= 60: return "31-60"
        if d <= 90: return "61-90"
        return "90+"

    f["close_bucket"] = f["days_to_close"].apply(bucket)
    f["expected_value_local"] = pd.to_numeric(f.get("expected_value_local", 0.0), errors="coerce").fillna(0.0)

    forecast = (f.groupby("close_bucket")["expected_value_local"]
                  .sum()
                  .reindex(["0-30","31-60","61-90","90+","Unknown"])
                  .fillna(0.0)
                  .reset_index()
                  .rename(columns={"expected_value_local":"weighted_pipeline_local"}))

    os.makedirs("out", exist_ok=True)
    forecast.to_csv("out/hunting_closure_forecast.csv", index=False)

    # -------- 2) Stage “truth” reasons (stall + exit)
    ev = _read_csv(events_path)
    if not ev.empty:
        ev["event_date"] = _to_dt(ev.get("event_date"))
        ev["event_type"] = ev["event_type"].astype(str).str.upper().str.strip()
        ev["reason_code"] = ev["reason_code"].astype(str).str.upper().str.strip()

        # Top stall reasons (last 90 days)
        recent = ev[ev["event_date"] >= (as_of - pd.Timedelta(days=90))]
        stall = recent[recent["event_type"].isin(["STALL","EXIT"])].copy()

        top_reasons = (stall.groupby(["event_type","reason_code"])
                           .size()
                           .sort_values(ascending=False)
                           .head(12)
                           .reset_index(name="count"))
    else:
        top_reasons = pd.DataFrame(columns=["event_type","reason_code","count"])

    # -------- 3) Owner x Stage aging heatmap (uses avg stage days from stage history)
    # If stage history missing, fall back to days_since_last_activity as a proxy.
    heat = opp.copy()
    heat["owner"] = heat.get("owner","—").astype(str)
    heat["stage"] = heat.get("stage","—").astype(str)

    if avg_stage_days:
        heat["stage_avg_days"] = heat["stage"].map(lambda s: float(avg_stage_days.get(s, 0)) if s in avg_stage_days else 0.0)
        # “pressure index” = stage avg days + days since last activity (captures both systemic and current staleness)
        heat["days_since_last_activity"] = pd.to_numeric(heat.get("days_since_last_activity", 0.0), errors="coerce").fillna(0.0)
        heat["aging_pressure_days"] = (0.6*heat["stage_avg_days"] + 0.4*heat["days_since_last_activity"]).round(1)
    else:
        heat["days_since_last_activity"] = pd.to_numeric(heat.get("days_since_last_activity", 0.0), errors="coerce").fillna(0.0)
        heat["aging_pressure_days"] = heat["days_since_last_activity"].clip(0, 90)

    heatmap = (heat[~heat["stage"].isin(["Won","Lost"])]
               .groupby(["owner","stage"])["aging_pressure_days"]
               .mean()
               .reset_index())

    # -------- 4) Approval checkpoint queue
    ap = _read_csv(approvals_path)
    if not ap.empty:
        ap["requested_date"] = _to_dt(ap.get("requested_date"))
        ap["approved_date"] = _to_dt(ap.get("approved_date"))
        ap["status"] = ap.get("status","").astype(str).str.upper().str.strip()
        ap["corridor_ok"] = ap.get("corridor_ok","").astype(str).str.upper().str.strip()

        # Add expected value for prioritization
        m = opp[["opportunity_id","account_name","market","vertical","stage","owner","expected_value_local","win_probability_pct","potential_annual_value_local"]].copy()
        m["expected_value_local"] = pd.to_numeric(m["expected_value_local"], errors="coerce").fillna(0.0)
        apq = ap.merge(m, on="opportunity_id", how="left")

        # Pending items first, then highest value
        apq["pending_flag"] = apq["status"].isin(["PENDING","REQUESTED","IN_REVIEW"])
        apq = apq.sort_values(["pending_flag","expected_value_local","requested_date"], ascending=[False, False, True])

        keep = [
            "opportunity_id","account_name","market","vertical","stage","owner",
            "approval_type","status","requested_date","approved_date",
            "requested_discount_pct","approved_discount_pct","margin_floor_pct","expected_gm_pct","corridor_ok",
            "expected_value_local","win_probability_pct","potential_annual_value_local","approver","notes"
        ]
        keep = [c for c in keep if c in apq.columns]
        apq[keep].to_csv("out/hunting_approval_queue.csv", index=False)
    else:
        pd.DataFrame().to_csv("out/hunting_approval_queue.csv", index=False)

    # -------- Output JSON summary for UI
    exec_truth = {
        "as_of": str(as_of.date()),
        "top_reasons": top_reasons.to_dict(orient="records"),
        "heatmap": heatmap.to_dict(orient="records"),
    }

    with open("out/hunting_exec_truth.json", "w", encoding="utf-8") as fjson:
        json.dump(exec_truth, fjson, indent=2)

    print("OK: wrote out/hunting_exec_truth.json")
    print("OK: wrote out/hunting_closure_forecast.csv")
    print("OK: wrote out/hunting_approval_queue.csv")

if __name__ == "__main__":
    main()
