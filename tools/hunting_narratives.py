#!/usr/bin/env python3
import os, json
import pandas as pd
from datetime import datetime

def fmt_money(x):
    try:
        x = float(x)
    except Exception:
        return "—"
    if x >= 1e9: return f"{x/1e9:.2f}B"
    if x >= 1e6: return f"{x/1e6:.2f}M"
    if x >= 1e3: return f"{x/1e3:.1f}K"
    return f"{x:.0f}"

def safe_pct(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def main():
    opp_path = "out/hunting_enriched.csv"
    pred_path = "out/hunting_predictive_metrics.json"
    slip_path = "out/hunting_slippage_scores.csv"
    approvals_path = "out/hunting_approval_queue.csv"
    reasons_path = "out/hunting_exec_truth.json"
    forecast_path = "out/hunting_closure_forecast.csv"

    if not os.path.exists(opp_path):
        raise SystemExit("Missing out/hunting_enriched.csv. Run enrich first.")

    df = pd.read_csv(opp_path)
    df["expected_value_local"] = pd.to_numeric(df.get("expected_value_local", 0.0), errors="coerce").fillna(0.0)
    df["potential_annual_value_local"] = pd.to_numeric(df.get("potential_annual_value_local", 0.0), errors="coerce").fillna(0.0)
    df["win_probability_pct"] = pd.to_numeric(df.get("win_probability_pct", 0.0), errors="coerce").fillna(0.0)
    df["deal_quality_score_0_100"] = pd.to_numeric(df.get("deal_quality_score_0_100", 0.0), errors="coerce").fillna(0.0)
    df["days_since_last_activity"] = pd.to_numeric(df.get("days_since_last_activity", 0.0), errors="coerce").fillna(0.0)

    active = df[~df["stage"].isin(["Won","Lost"])].copy()

    total_weighted = float(active["expected_value_local"].sum())
    total_raw = float(active["potential_annual_value_local"].sum())
    quality_ratio = (total_weighted/total_raw*100.0) if total_raw>0 else 0.0

    # Concentration (top market & vertical)
    top_market = None
    top_vertical = None
    if "market" in active.columns and total_weighted > 0:
        m = active.groupby("market")["expected_value_local"].sum().sort_values(ascending=False)
        top_market = (m.index[0], float(m.iloc[0]), float(m.iloc[0]/total_weighted*100))
    if "vertical" in active.columns and total_weighted > 0:
        v = active.groupby("vertical")["expected_value_local"].sum().sort_values(ascending=False)
        top_vertical = (v.index[0], float(v.iloc[0]), float(v.iloc[0]/total_weighted*100))

    # Predictive metrics if available
    pred = json.load(open(pred_path)) if os.path.exists(pred_path) else {}
    high_risk_pct = safe_pct(pred.get("high_risk_pipeline_pct", 0))
    top_market_pct = safe_pct(pred.get("top_market_concentration_pct", top_market[2] if top_market else 0))

    # Closure forecast
    close_30 = 0.0
    close_60 = 0.0
    if os.path.exists(forecast_path):
        fc = pd.read_csv(forecast_path)
        b = dict(zip(fc["close_bucket"], fc["weighted_pipeline_local"]))
        close_30 = float(b.get("0-30", 0.0))
        close_60 = float(b.get("31-60", 0.0))

    # Top stall reasons
    top_reasons = []
    if os.path.exists(reasons_path):
        ex = json.load(open(reasons_path))
        rr = ex.get("top_reasons", [])[:5]
        for r in rr:
            top_reasons.append(f"{r.get('event_type','')}/{r.get('reason_code','')}: {r.get('count',0)}")

    # Approvals pending
    pending_approvals = 0
    if os.path.exists(approvals_path):
        ap = pd.read_csv(approvals_path)
        if not ap.empty and "status" in ap.columns:
            pending_approvals = int(ap["status"].astype(str).str.upper().isin(["PENDING","REQUESTED","IN_REVIEW"]).sum())

    # Slippage top deals
    slip = pd.read_csv(slip_path) if os.path.exists(slip_path) else pd.DataFrame()
    slip = slip.merge(active[["opportunity_id","account_name","stage","market","vertical","owner","expected_value_local","win_probability_pct","days_since_last_activity"]],
                      on="opportunity_id", how="left") if not slip.empty else slip
    if not slip.empty:
        slip["slippage_risk_score"] = pd.to_numeric(slip["slippage_risk_score"], errors="coerce").fillna(0.0)
        slip = slip.sort_values("slippage_risk_score", ascending=False)

    def deal_sentence(row):
        val = fmt_money(row.get("expected_value_local", 0))
        p = float(row.get("win_probability_pct", 0))
        stg = row.get("stage", "—")
        owner = row.get("owner", "—")
        mk = row.get("market", "—")
        vert = row.get("vertical", "—")
        days = float(row.get("days_since_last_activity", 0))
        risk = float(row.get("slippage_risk_score", 0))

        # Action inference
        if risk >= 80:
            action = "Escalate now; deal likely to slip without intervention."
        elif risk >= 60:
            action = "Prioritize follow-up; unblock next step and tighten close plan."
        elif stg in ["Proposal","Negotiation"] and days > 10:
            action = "Re-engage; confirm decision maker and approval path."
        else:
            action = "Keep cadence; move to next milestone."

        return {
            "opportunity_id": row.get("opportunity_id","—"),
            "headline": f"{row.get('account_name','—')} — {stg} — {val} weighted — {p:.0f}% win",
            "detail": f"Market: {mk} | Vertical: {vert} | Owner: {owner} | Inactive: {days:.0f} days | Slippage risk: {risk:.0f}/100.",
            "action": action
        }

    top_deals = []
    if not slip.empty:
        for _, r in slip.head(8).iterrows():
            top_deals.append(deal_sentence(r))
    else:
        # fallback: highest EV
        t = active.sort_values("expected_value_local", ascending=False).head(8)
        for _, r in t.iterrows():
            r = r.to_dict()
            r["slippage_risk_score"] = 0
            top_deals.append(deal_sentence(r))

    # CEO summary narrative (2–4 lines)
    lines = []
    lines.append(f"Weighted pipeline is {fmt_money(total_weighted)} ({quality_ratio:.1f}% quality ratio vs total pipeline).")
    if close_30 > 0 or close_60 > 0:
        lines.append(f"Expected closures: {fmt_money(close_30)} in 0–30 days, {fmt_money(close_60)} in 31–60 days (weighted).")
    if top_market:
        lines.append(f"Pipeline is concentrated in {top_market[0]} at {top_market_pct:.1f}% of weighted value.")
    if top_vertical:
        lines.append(f"Top vertical is {top_vertical[0]} at {top_vertical[2]:.1f}% of weighted value.")
    if high_risk_pct > 0:
        lines.append(f"{high_risk_pct:.1f}% of weighted pipeline is at high slippage risk (>60 score).")
    if pending_approvals > 0:
        lines.append(f"There are {pending_approvals} pending guardrail approvals that may delay proposals or force margin exceptions.")
    if top_reasons:
        lines.append("Top stall drivers (last 90 days): " + "; ".join(top_reasons) + ".")

    output = {
        "as_of": str(datetime.now().date()),
        "ceo_summary": lines[:6],
        "top_deals": top_deals
    }

    os.makedirs("out", exist_ok=True)
    with open("out/hunting_narratives.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("OK: wrote out/hunting_narratives.json")

if __name__ == "__main__":
    main()
