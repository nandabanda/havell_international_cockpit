from pathlib import Path
import json
import pandas as pd
import streamlit as st

from core.ui_theme import apply_ivory, section

apply_ivory()

OUT = Path("out")

def read_csv_safe(p: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(p) if p.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def read_json_safe(p: Path) -> dict:
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}

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

def norm_prob(p: pd.Series) -> pd.Series:
    x = to_num(p).fillna(0)
    if x.max() > 1.5:  # 0-100
        x = x / 100.0
    return x.clip(0, 1)

# Load artifacts (best effort)
enr = read_csv_safe(OUT / "hunting_enriched.csv")
fwd = read_csv_safe(OUT / "hunting_forward_signal.csv")
slip = read_csv_safe(OUT / "hunting_slippage_scores.csv")
apq = read_csv_safe(OUT / "hunting_approval_queue.csv")
kpi = read_json_safe(OUT / "hunting_kpis.json")
stage_metrics = read_json_safe(OUT / "hunting_stage_metrics.json")

st.title("🎯 Hunting Engine — Projects / OEM / Institutional")
section(
    "Framework",
    "Target → Qualification → Technical → Proposal → Negotiation → Closure | SLA-based movement | Prob-adjusted pipeline | Guardrails + approvals | Slippage intelligence"
)

# ------------------------------------------------------------
# Self-heal: ensure canonical columns exist
# ------------------------------------------------------------
if not enr.empty:
    # stage
    if "stage" not in enr.columns:
        c_stage = pick_col(enr, ["funnel_stage", "status_stage"])
        enr["stage"] = enr[c_stage].astype(str) if c_stage else "Target"

    # opportunity_id
    if "opportunity_id" not in enr.columns:
        c_id = pick_col(enr, ["opp_id", "opportunityid", "id", "project_id"])
        if c_id:
            enr["opportunity_id"] = enr[c_id].astype(str)
        else:
            enr["opportunity_id"] = [f"OPP_{i}" for i in range(len(enr))]

    # value
    if "value" not in enr.columns:
        c_value = pick_col(enr, ["deal_value", "opportunity_value", "value_amount", "project_value", "amount"])
        enr["value"] = to_num(enr[c_value]).fillna(0) if c_value else 0.0

    # probability
    if "probability" not in enr.columns:
        c_prob = pick_col(enr, ["win_probability", "prob", "probability_pct"])
        enr["probability"] = norm_prob(enr[c_prob]) if c_prob else 0.0
    else:
        enr["probability"] = norm_prob(enr["probability"])

    # prob_adj_value
    if "prob_adj_value" not in enr.columns:
        enr["prob_adj_value"] = to_num(enr["value"]).fillna(0) * to_num(enr["probability"]).fillna(0)

    # sla_breach
    if "sla_breach" not in enr.columns:
        # if you have days_since_last_move + sla_days, compute it; else default 0
        if ("days_since_last_move" in enr.columns) and ("sla_days" in enr.columns):
            enr["sla_breach"] = (to_num(enr["days_since_last_move"]).fillna(0) > to_num(enr["sla_days"]).fillna(9999)).astype(int)
        else:
            enr["sla_breach"] = 0

    # approval_required default (for guardrails)
    if "approval_required" not in enr.columns:
        enr["approval_required"] = 0

# ------------------------------------------------------------
# KPI strip (prefer kpis.json, else compute from enr)
# ------------------------------------------------------------
total_pipeline = float(kpi.get("total_pipeline", 0)) if kpi else (float(enr["value"].sum()) if not enr.empty else 0.0)
prob_adj_pipeline = float(kpi.get("prob_adj_pipeline", 0)) if kpi else (float(enr["prob_adj_value"].sum()) if not enr.empty else 0.0)
deals = int(kpi.get("deals", 0)) if kpi else (int(enr["opportunity_id"].nunique()) if not enr.empty else 0)
sla_breaches = int(kpi.get("sla_breaches", 0)) if kpi else (int(enr["sla_breach"].sum()) if not enr.empty else 0)
approvals_required = int(kpi.get("approvals_required", 0)) if kpi else (int(enr["approval_required"].sum()) if not enr.empty else 0)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Pipeline", f"{total_pipeline:,.0f}")
c2.metric("Prob-Adj Pipeline", f"{prob_adj_pipeline:,.0f}")
c3.metric("Deals", deals)
c4.metric("SLA Breaches", sla_breaches)
c5.metric("Approvals Required", approvals_required)

# ------------------------------------------------------------
# Revenue visibility
# ------------------------------------------------------------
st.divider()
section("Revenue Visibility", "Forward pipeline view (total vs probability-adjusted).")
if fwd.empty:
    st.info("No forward signal yet. If you created it, run: python3 tools/hunting_alignment.py")
else:
    st.dataframe(fwd, use_container_width=True)
    st.download_button(
        "Download hunting_forward_signal.csv",
        (OUT / "hunting_forward_signal.csv").read_bytes(),
        file_name="hunting_forward_signal.csv",
        mime="text/csv",
        key="dl_h_fwd"
    )

# ------------------------------------------------------------
# Funnel discipline (no-crash)
# ------------------------------------------------------------
st.divider()
section("Funnel Discipline", "Stage distribution and bottlenecks (SLA breaches).")

if stage_metrics.get("stage_metrics"):
    st.dataframe(pd.DataFrame(stage_metrics["stage_metrics"]), use_container_width=True)
else:
    if enr.empty:
        st.info("No enriched pipeline yet. Ensure out/hunting_enriched.csv exists.")
    else:
        snap = (
            enr.groupby("stage")
            .agg(
                deals=("opportunity_id","nunique"),
                total=("value","sum"),
                prob_adj=("prob_adj_value","sum"),
                sla_breaches=("sla_breach","sum"),
            )
            .reset_index()
        )
        st.dataframe(snap, use_container_width=True)

# ------------------------------------------------------------
# Guardrails / approvals
# ------------------------------------------------------------
st.divider()
section("Margin & Pricing Guardrails", "Deviation triggers approval workflow before proposal (if approval queue exists).")
if apq.empty:
    st.info("No approvals queue found (out/hunting_approval_queue.csv). This is OK if guardrails not triggered yet.")
else:
    st.dataframe(apq, use_container_width=True)
    st.download_button(
        "Download hunting_approval_queue.csv",
        (OUT / "hunting_approval_queue.csv").read_bytes(),
        file_name="hunting_approval_queue.csv",
        mime="text/csv",
        key="dl_h_apq"
    )

# ------------------------------------------------------------
# Intelligence layer
# ------------------------------------------------------------
st.divider()
section("Intelligence Layer", "Slippage alerts and high-value low-probability flags.")

t1, t2 = st.columns(2)

with t1:
    st.subheader("Slippage Alerts (Top 50)")
    if slip.empty:
        st.info("No slippage scores yet. If you created it, run: python3 tools/hunting_alignment.py")
    else:
        st.dataframe(slip.head(50), use_container_width=True)
        st.download_button(
            "Download hunting_slippage_scores.csv",
            (OUT / "hunting_slippage_scores.csv").read_bytes(),
            file_name="hunting_slippage_scores.csv",
            mime="text/csv",
            key="dl_h_slip"
        )

with t2:
    st.subheader("High-Value Low-Probability (Top 50)")
    if enr.empty:
        st.info("No enriched pipeline loaded.")
    else:
        # derive HVLP if missing
        if "high_value_low_prob" not in enr.columns:
            v = enr["value"].fillna(0)
            p = enr["probability"].fillna(0)
            thr = v.quantile(0.85) if len(v) >= 10 else v.max()
            enr["high_value_low_prob"] = ((v >= thr) & (p <= 0.30)).astype(int)

        hv = enr[enr["high_value_low_prob"] == 1].sort_values(["value","probability"], ascending=[False, True]).head(50)
        cols = [c for c in ["opportunity_id","stage","owner","geography","vertical","value","probability","prob_adj_value","sla_breach","approval_required"] if c in hv.columns]
        st.dataframe(hv[cols], use_container_width=True)

# ------------------------------------------------------------
# Enriched pipeline table
# ------------------------------------------------------------
st.divider()
section("Pipeline (Enriched)", "Single source of truth for Hunting governance.")
if enr.empty:
    st.info("No hunting_enriched.csv yet. Run: python3 tools/hunting_alignment.py")
else:
    st.dataframe(enr.head(200), use_container_width=True)
    st.download_button(
        "Download hunting_enriched.csv",
        (OUT / "hunting_enriched.csv").read_bytes(),
        file_name="hunting_enriched.csv",
        mime="text/csv",
        key="dl_h_enr"
    )
