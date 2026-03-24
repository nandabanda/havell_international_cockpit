from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, date
import json
import pandas as pd
import numpy as np

DATA = Path("data")
OUT = Path("out")
OUT.mkdir(exist_ok=True)

STAGE_ORDER = ["Target", "Qualification", "Technical", "Proposal", "Negotiation", "Closure"]

def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_csv_safe(p: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(p) if p.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None

def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def parse_date_col(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce").dt.date

def norm_prob(p: pd.Series) -> pd.Series:
    x = to_num(p).fillna(0)
    if x.max() > 1.5:  # assume 0-100
        x = x / 100.0
    return x.clip(0, 1)

def stage_rank(stage: str) -> int:
    try:
        return STAGE_ORDER.index(str(stage).strip())
    except Exception:
        return 999

def ensure_stage(stage: str) -> str:
    s = str(stage).strip()
    # normalize common variants
    mapping = {
        "qualify": "Qualification",
        "qualification": "Qualification",
        "technical": "Technical",
        "proposal": "Proposal",
        "negotiation": "Negotiation",
        "close": "Closure",
        "closure": "Closure",
        "target": "Target",
    }
    key = s.lower()
    if key in mapping:
        return mapping[key]
    # if already matches
    for stg in STAGE_ORDER:
        if s.lower() == stg.lower():
            return stg
    return s

def compute_sla_days(stage: str) -> int:
    # pragmatic defaults; tune later
    # (SLA-based stage movement required by the framework)
    # Target 14, Qualification 21, Technical 30, Proposal 21, Negotiation 30, Closure n/a
    stg = ensure_stage(stage)
    return {
        "Target": 14,
        "Qualification": 21,
        "Technical": 30,
        "Proposal": 21,
        "Negotiation": 30,
        "Closure": 9999,
    }.get(stg, 21)

def build_enriched(opps: pd.DataFrame, history: pd.DataFrame, approvals: pd.DataFrame) -> pd.DataFrame:
    if opps.empty:
        return pd.DataFrame()

    # Canonical columns (best-effort)
    c_id = pick_col(opps, ["opportunity_id", "opp_id", "id", "project_id"])
    if c_id is None:
        # create stable id from name + geo + owner
        name = pick_col(opps, ["project_name", "opportunity", "name", "project"])
        geo = pick_col(opps, ["geography", "geo", "market", "country", "region"])
        owner = pick_col(opps, ["owner", "sales_owner", "key_account_manager"])
        opps["_opportunity_id"] = (
            opps.get(name, "").astype(str) + "|" + opps.get(geo, "").astype(str) + "|" + opps.get(owner, "").astype(str)
        ).apply(lambda x: str(abs(hash(x)))[:12])
        c_id = "_opportunity_id"

    c_stage = pick_col(opps, ["stage", "funnel_stage", "status_stage"])
    c_value = pick_col(opps, ["value", "deal_value", "opportunity_value", "value_amount", "project_value"])
    c_prob  = pick_col(opps, ["probability", "prob", "win_probability"])
    c_close = pick_col(opps, ["close_date", "expected_close_date", "target_close_date"])
    c_geo   = pick_col(opps, ["geography", "geo", "market", "country", "region"])
    c_vert  = pick_col(opps, ["vertical", "segment", "industry"])
    c_owner = pick_col(opps, ["owner", "sales_owner", "key_account_manager"])

    # Margin/RGM inputs (before proposal)
    c_margin_floor = pick_col(opps, ["margin_floor", "min_margin", "margin_floor_pct"])
    c_margin_est   = pick_col(opps, ["expected_margin", "margin_pct", "gm_pct"])
    c_discount     = pick_col(opps, ["discount", "discount_pct"])
    c_corr_ok      = pick_col(opps, ["corridor_ok", "price_corridor_ok"])
    c_fx_impact    = pick_col(opps, ["fx_impact", "fx_cost", "fx_delta"])
    c_log_impact   = pick_col(opps, ["logistics_impact", "log_cost", "freight_impact"])

    out = opps.copy()
    out["stage"] = out[c_stage].astype(str).apply(ensure_stage) if c_stage else "Target"
    out["stage_rank"] = out["stage"].apply(stage_rank)

    out["value"] = to_num(out[c_value]).fillna(0) if c_value else 0.0
    out["probability"] = norm_prob(out[c_prob]) if c_prob else 0.0
    out["prob_adj_value"] = out["value"] * out["probability"]

    if c_close:
        out["close_date"] = pd.to_datetime(out[c_close], errors="coerce").dt.date
    else:
        out["close_date"] = pd.NaT

    out["geography"] = out[c_geo].astype(str) if c_geo else "NA"
    out["vertical"]  = out[c_vert].astype(str) if c_vert else "NA"
    out["owner"]     = out[c_owner].astype(str) if c_owner else "NA"

    # Stage history-derived fields (deal velocity, slippage)
    if not history.empty:
        h = history.copy()
        hid = pick_col(h, ["opportunity_id", "opp_id", "id", "project_id"])
        hstage = pick_col(h, ["stage", "funnel_stage", "to_stage", "stage_name"])
        hdate = pick_col(h, ["date", "event_date", "timestamp", "moved_on", "entered_on"])
        if hid and hstage and hdate:
            h["opportunity_id"] = h[hid].astype(str)
            h["stage"] = h[hstage].astype(str).apply(ensure_stage)
            h["event_date"] = pd.to_datetime(h[hdate], errors="coerce")
            h = h.dropna(subset=["event_date"])
            h = h.sort_values(["opportunity_id", "event_date"])

            # first enter date, last move date, days in current stage
            first = h.groupby("opportunity_id")["event_date"].min().rename("first_seen")
            last  = h.groupby("opportunity_id")["event_date"].max().rename("last_moved")
            current_stage = h.groupby("opportunity_id")["stage"].last().rename("stage_hist")

            tmp = pd.concat([first, last, current_stage], axis=1).reset_index()
            tmp["days_since_last_move"] = (pd.Timestamp.now().normalize() - tmp["last_moved"].dt.normalize()).dt.days

            out = out.merge(tmp, left_on=c_id, right_on="opportunity_id", how="left").drop(columns=["opportunity_id"], errors="ignore")

            # if stage missing in opps, use hist
            out["stage"] = np.where(out["stage"].isna() | (out["stage"].astype(str).str.len()==0), out["stage_hist"], out["stage"])
            out["stage"] = out["stage"].astype(str).apply(ensure_stage)
            out["stage_rank"] = out["stage"].apply(stage_rank)

            # SLA breach
            out["sla_days"] = out["stage"].apply(compute_sla_days)
            out["sla_breach"] = np.where(out["days_since_last_move"].fillna(0) > out["sla_days"], 1, 0)
        else:
            out["days_since_last_move"] = np.nan
            out["sla_breach"] = 0
            out["sla_days"] = out["stage"].apply(compute_sla_days)
    else:
        out["days_since_last_move"] = np.nan
        out["sla_breach"] = 0
        out["sla_days"] = out["stage"].apply(compute_sla_days)

    # Margin guardrails + approval triggers
    if c_margin_floor and c_margin_est:
        out["margin_floor"] = to_num(out[c_margin_floor])
        out["expected_margin"] = to_num(out[c_margin_est])
        out["margin_breach"] = np.where(out["expected_margin"] < out["margin_floor"], 1, 0)
    else:
        out["margin_breach"] = 0

    if c_discount:
        out["discount_pct"] = to_num(out[c_discount])
    else:
        out["discount_pct"] = np.nan

    if c_corr_ok:
        out["corridor_ok"] = out[c_corr_ok].astype(str).str.lower().isin(["1","true","yes","y","ok"])
        out["corridor_breach"] = np.where(out["corridor_ok"]==False, 1, 0)
    else:
        out["corridor_breach"] = 0

    if c_fx_impact:
        out["fx_impact"] = to_num(out[c_fx_impact])
    else:
        out["fx_impact"] = np.nan

    if c_log_impact:
        out["logistics_impact"] = to_num(out[c_log_impact])
    else:
        out["logistics_impact"] = np.nan

    # Deviation triggers approval workflow (if approvals file exists)
    out["approval_required"] = np.where((out["margin_breach"]==1) | (out["corridor_breach"]==1), 1, 0)
    out["approval_status"] = "NA"

    if not approvals.empty:
        a = approvals.copy()
        aid = pick_col(a, ["opportunity_id","opp_id","id","project_id"])
        astatus = pick_col(a, ["status","approval_status"])
        if aid and astatus:
            a["opportunity_id"] = a[aid].astype(str)
            a["approval_status"] = a[astatus].astype(str)
            a = a[["opportunity_id","approval_status"]].drop_duplicates("opportunity_id", keep="last")
            out = out.merge(a, left_on=c_id, right_on="opportunity_id", how="left", suffixes=("","_x"))
            out["approval_status"] = out["approval_status"].fillna("NA")
            out = out.drop(columns=["opportunity_id"], errors="ignore")

    # Intelligence flags: high value low probability + slippage
    out["high_value_low_prob"] = np.where((out["value"] >= out["value"].quantile(0.85)) & (out["probability"] <= 0.30), 1, 0)
    out["slippage_flag"] = np.where(out["sla_breach"]==1, 1, 0)

    keep = [
        c_id, "stage","stage_rank","owner","geography","vertical",
        "value","probability","prob_adj_value","close_date",
        "days_since_last_move","sla_days","sla_breach",
        "margin_breach","corridor_breach","approval_required","approval_status",
        "high_value_low_prob","slippage_flag",
        "discount_pct","fx_impact","logistics_impact",
    ]
    keep = [c for c in keep if c in out.columns] + [c_id]
    out = out.loc[:, dict.fromkeys(keep)].copy()  # preserve order, unique

    # rename id to opportunity_id for downstream consistency
    out = out.rename(columns={c_id: "opportunity_id"})

    return out

def write_forward_signal(enr: pd.DataFrame):
    if enr.empty:
        (OUT / "hunting_forward_signal.csv").write_text("")
        return

    df = enr.copy()
    # month buckets from close_date
    if "close_date" in df.columns:
        cd = pd.to_datetime(df["close_date"], errors="coerce")
        df["close_month"] = cd.dt.to_period("M").astype(str)
    else:
        df["close_month"] = "NA"

    # pipeline by month
    fwd = df.groupby("close_month").agg(
        total_pipeline=("value","sum"),
        prob_adj_pipeline=("prob_adj_value","sum"),
        deals=("opportunity_id","nunique"),
        sla_breaches=("sla_breach","sum"),
        approvals_required=("approval_required","sum"),
        margin_breaches=("margin_breach","sum"),
        corridor_breaches=("corridor_breach","sum"),
    ).reset_index().sort_values("close_month")

    fwd.to_csv(OUT / "hunting_forward_signal.csv", index=False)

def write_slippage(enr: pd.DataFrame):
    if enr.empty:
        (OUT / "hunting_slippage_scores.csv").write_text("")
        return
    df = enr.copy()
    df["slippage_score"] = df.get("days_since_last_move", 0).fillna(0)
    df = df.sort_values(["slippage_flag","slippage_score","prob_adj_value"], ascending=[False, False, False])
    cols = ["opportunity_id","stage","owner","geography","vertical","value","probability","prob_adj_value","days_since_last_move","sla_days","sla_breach","slippage_flag"]
    cols = [c for c in cols if c in df.columns]
    df[cols].to_csv(OUT / "hunting_slippage_scores.csv", index=False)

def write_approval_queue(enr: pd.DataFrame):
    if enr.empty:
        (OUT / "hunting_approval_queue.csv").write_text("")
        return
    df = enr.copy()
    q = df[df.get("approval_required", 0) == 1].copy()
    q = q.sort_values(["prob_adj_value","value"], ascending=[False, False])
    cols = ["opportunity_id","stage","owner","geography","vertical","value","probability","prob_adj_value","margin_breach","corridor_breach","approval_status"]
    cols = [c for c in cols if c in q.columns]
    q[cols].to_csv(OUT / "hunting_approval_queue.csv", index=False)

def write_kpis(enr: pd.DataFrame):
    k = {
        "timestamp": now_ts(),
        "total_pipeline": float(enr["value"].sum()) if (not enr.empty and "value" in enr.columns) else 0.0,
        "prob_adj_pipeline": float(enr["prob_adj_value"].sum()) if (not enr.empty and "prob_adj_value" in enr.columns) else 0.0,
        "deals": int(enr["opportunity_id"].nunique()) if (not enr.empty and "opportunity_id" in enr.columns) else 0,
        "sla_breaches": int(enr.get("sla_breach", pd.Series([])).sum()) if not enr.empty else 0,
        "approvals_required": int(enr.get("approval_required", pd.Series([])).sum()) if not enr.empty else 0,
        "high_value_low_prob": int(enr.get("high_value_low_prob", pd.Series([])).sum()) if not enr.empty else 0,
    }
    (OUT / "hunting_kpis.json").write_text(json.dumps(k, indent=2))

def write_stage_metrics(enr: pd.DataFrame):
    if enr.empty:
        (OUT / "hunting_stage_metrics.json").write_text("{}")
        return
    df = enr.copy()
    stage = df.groupby("stage").agg(
        deals=("opportunity_id","nunique"),
        total=("value","sum"),
        prob_adj=("prob_adj_value","sum"),
        sla_breaches=("sla_breach","sum"),
    ).reset_index()
    stage["stage_rank"] = stage["stage"].apply(stage_rank)
    stage = stage.sort_values("stage_rank")
    out = {"timestamp": now_ts(), "stage_metrics": stage.drop(columns=["stage_rank"]).to_dict(orient="records")}
    (OUT / "hunting_stage_metrics.json").write_text(json.dumps(out, indent=2))

def main():
    opps = read_csv_safe(DATA / "hunting_opportunities.csv")
    history = read_csv_safe(DATA / "hunting_stage_history.csv")
    approvals = read_csv_safe(DATA / "hunting_proposal_approvals.csv")

    enr = build_enriched(opps, history, approvals)

    # enforce stage order values
    if not enr.empty and "stage" in enr.columns:
        enr["stage"] = enr["stage"].astype(str).apply(ensure_stage)

    # write canonical artifacts
    enr.to_csv(OUT / "hunting_enriched.csv", index=False)
    write_forward_signal(enr)
    write_slippage(enr)
    write_approval_queue(enr)
    write_kpis(enr)
    write_stage_metrics(enr)

    print("OK: wrote hunting artifacts to out/")
    print(" - out/hunting_enriched.csv")
    print(" - out/hunting_forward_signal.csv")
    print(" - out/hunting_slippage_scores.csv")
    print(" - out/hunting_approval_queue.csv")
    print(" - out/hunting_kpis.json")
    print(" - out/hunting_stage_metrics.json")

if __name__ == "__main__":
    main()
