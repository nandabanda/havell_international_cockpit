from __future__ import annotations

from pathlib import Path
import math
import pandas as pd
import numpy as np

OUT = Path("out"); OUT.mkdir(exist_ok=True)
DATA = Path("data")

# ----------------------------
# Helpers
# ----------------------------
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

def norm_0_100(x: pd.Series) -> pd.Series:
    x = x.astype(float)
    lo = np.nanmin(x); hi = np.nanmax(x)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return pd.Series([50.0]*len(x), index=x.index)
    return 100.0 * (x - lo) / (hi - lo)

# ----------------------------
# Load micro-market artifacts
# ----------------------------
scored = read_csv_safe(OUT / "micromarket_scored.csv")
if scored.empty:
    raise SystemExit("Missing out/micromarket_scored.csv. Run micromarket tools first.")

# Optional
clusters = read_csv_safe(OUT / "micromarket_clusters.csv")

# Distributor master (we now rely on this for real guardrails)
dist = read_csv_safe(DATA / "distributors_existing.csv")
if dist.empty:
    raise SystemExit("Missing data/distributors_existing.csv")

# ----------------------------
# Column mapping (micro markets)
# ----------------------------
geo_col = pick_col(scored, ["geo_name", "geography", "geo", "market", "country", "region"])
cluster_col = pick_col(scored, ["cluster_id", "cluster", "micromarket_cluster"])
micro_col = pick_col(scored, ["micro_market_id", "micromarket_id", "micro_id", "micromarket"])

score_col = pick_col(scored, ["opportunity_score", "score", "attractiveness_score", "priority_score"])
headroom_col = pick_col(scored, ["headroom", "value_headroom", "demand_headroom", "volume_headroom"])
comp_col = pick_col(scored, ["competition_intensity", "competitive_intensity", "competition"])
cov_col = pick_col(scored, ["current_coverage", "coverage", "numeric_distribution", "nd", "wd"])
density_col = pick_col(scored, ["density_index", "demand_density", "density"])

if micro_col is None:
    scored["_micro_market_id"] = [f"MM_{i}" for i in range(len(scored))]
    micro_col = "_micro_market_id"

if score_col is None:
    scored["_opportunity_score"] = 0.0
    score_col = "_opportunity_score"

scored["_score"] = to_num(scored[score_col]).fillna(0)
scored["_headroom"] = to_num(scored[headroom_col]).fillna(0) if headroom_col else 0.0
scored["_density"] = to_num(scored[density_col]).fillna(0) if density_col else 0.0
scored["_comp"] = to_num(scored[comp_col]).fillna(0) if comp_col else 0.0

if cov_col:
    cov = to_num(scored[cov_col]).fillna(0)
    if cov.max() > 1.5:
        cov = cov / 100.0
    scored["_coverage"] = cov.clip(0, 1)
else:
    scored["_coverage"] = np.nan

# ----------------------------
# A) Whitespace map
# ----------------------------
q_score = scored["_score"].quantile(0.75) if len(scored) >= 10 else scored["_score"].max()

if scored["_coverage"].notna().any():
    q_cov = scored["_coverage"].quantile(0.35) if scored["_coverage"].notna().sum() >= 10 else 0.35
    whitespace_flag = (scored["_score"] >= q_score) & (scored["_coverage"] <= q_cov)
    current_cov = scored["_coverage"].fillna(0)
else:
    q_den = scored["_density"].quantile(0.65) if len(scored) >= 10 else scored["_density"].max()
    whitespace_flag = (scored["_score"] >= q_score) & (scored["_density"] >= q_den)
    current_cov = pd.Series([np.nan]*len(scored), index=scored.index)

white = pd.DataFrame({
    "micro_market_id": scored[micro_col].astype(str),
    "geography": scored[geo_col].astype(str) if geo_col else "NA",
    "cluster_id": scored[cluster_col].astype(str) if cluster_col else "NA",
    "attractiveness_score": scored["_score"],
    "headroom": scored["_headroom"],
    "competition_intensity": scored["_comp"],
    "current_coverage": current_cov,
    "density_index": scored["_density"],
    "whitespace_flag": whitespace_flag.astype(int),
})
white.to_csv(OUT / "pre_farming_whitespace_map.csv", index=False)

# ----------------------------
# B) Territory plan
# ----------------------------
# Capacity per distributor derived from last_90d_sell_in_value median (proxy throughput)
cap_proxy = pick_col(dist, ["last_90d_sell_in_value", "sell_in_value_90d", "last90_sellin_value"])
if cap_proxy:
    cap = to_num(dist[cap_proxy]).replace(0, np.nan)
    cap_per = float(np.nanmedian(cap)) if np.isfinite(np.nanmedian(cap)) else 1.0e7
else:
    cap_per = 1.0e7  # fallback

grp = white.groupby(["geography", "cluster_id"], dropna=False).agg(
    micro_markets=("micro_market_id", "nunique"),
    whitespace_pockets=("whitespace_flag", "sum"),
    total_headroom=("headroom", "sum"),
    avg_score=("attractiveness_score", "mean"),
    avg_comp=("competition_intensity", "mean"),
    avg_density=("density_index", "mean"),
).reset_index()

def rec_count(row):
    head = row["total_headroom"] if pd.notna(row["total_headroom"]) else 0
    ws = row["whitespace_pockets"] if pd.notna(row["whitespace_pockets"]) else 0
    if head <= 0 and ws <= 0:
        return 0
    return max(1, int(math.ceil(max(head, 1) / cap_per)))

grp["recommended_distributor_count"] = grp.apply(rec_count, axis=1)
grp["territory_id"] = grp.apply(lambda r: f"TERR::{r['geography']}::{r['cluster_id']}", axis=1)

top_nodes = (
    white.sort_values(["whitespace_flag","attractiveness_score","headroom"], ascending=[False, False, False])
    .groupby(["geography", "cluster_id"], dropna=False)
    .head(10)
    .groupby(["geography", "cluster_id"], dropna=False)["micro_market_id"]
    .apply(lambda s: ", ".join(list(s.astype(str))[:10]))
    .reset_index()
    .rename(columns={"micro_market_id": "proposed_nodes_top10"})
)

territory = grp.merge(top_nodes, on=["geography", "cluster_id"], how="left")
territory["rationale"] = territory.apply(
    lambda r: f"Headroom={r['total_headroom']:.0f}, Whitespaces={int(r['whitespace_pockets'])}, AvgScore={r['avg_score']:.2f}, AvgDensity={r['avg_density']:.2f}",
    axis=1
)

territory.to_csv(OUT / "pre_farming_territory_plan.csv", index=False)

# ----------------------------
# C) Appointment queue (REAL guardrails + micro-market matching)
# ----------------------------
dist_id = pick_col(dist, ["distributor_id"])
dist_name = pick_col(dist, ["distributor_name", "name"])
dist_country = pick_col(dist, ["country"])
dist_region = pick_col(dist, ["region"])
dist_city = pick_col(dist, ["city"])
dist_mm = pick_col(dist, ["assigned_micro_market_id", "micro_market_id"])

cov = pick_col(dist, ["coverage_strength_0_1"])
whs = pick_col(dist, ["warehouse_capacity_index"])
crd = pick_col(dist, ["credit_strength_index"])
sl  = pick_col(dist, ["service_level_index"])
sellin = pick_col(dist, ["last_90d_sell_in_value"])
skus = pick_col(dist, ["active_skus"])

# Normalized guardrails
dist["_warehouse_score"] = norm_0_100(to_num(dist[whs]).fillna(0)) if whs else 50.0
dist["_credit_score"] = norm_0_100(to_num(dist[crd]).fillna(0)) if crd else 50.0
dist["_service_score"] = norm_0_100(to_num(dist[sl]).fillna(0)) if sl else 50.0
dist["_sellin_score"] = norm_0_100(to_num(dist[sellin]).fillna(0)) if sellin else 50.0

# RGM acceptance proxy: coverage discipline (0-1 scaled to 0-100)
if cov:
    c = to_num(dist[cov]).fillna(0)
    c = c/100.0 if c.max() > 1.5 else c
    dist["_rgm_acceptance"] = (c.clip(0, 1) * 100.0)
else:
    dist["_rgm_acceptance"] = 50.0

# Composite suitability
dist["_suitability"] = (
    0.25*dist["_warehouse_score"] +
    0.25*dist["_credit_score"] +
    0.20*dist["_service_score"] +
    0.20*dist["_sellin_score"] +
    0.10*dist["_rgm_acceptance"]
)

# Build per-territory candidate list with best-fit matching
rows = []
for _, t in territory.iterrows():
    if int(t["recommended_distributor_count"]) <= 0:
        continue

    terr_id = str(t["territory_id"])
    geo = str(t["geography"])
    clu = str(t["cluster_id"])

    # Proposed micro markets for this territory
    nodes = str(t.get("proposed_nodes_top10") or "")
    nodes_set = set([x.strip() for x in nodes.split(",") if x.strip()])

    pool = dist.copy()

    # Best-fit: those assigned to the proposed micro markets
    if dist_mm and nodes_set:
        best = pool[pool[dist_mm].astype(str).isin(nodes_set)]
    else:
        best = pd.DataFrame()

    # If best-fit too small, fallback to same geo
    if best.empty:
        # approximate geo match using country/region
        if dist_country and geo != "NA":
            same = pool[pool[dist_country].astype(str) == geo]
            pool = same if not same.empty else pool
    else:
        pool = best

    pool = pool.sort_values("_suitability", ascending=False).head(max(12, int(t["recommended_distributor_count"])*6))

    for _, d in pool.iterrows():
        s = float(d["_suitability"])
        # Stronger thresholds since these are appointment decisions
        if s >= 78:
            rec = "APPOINT"
        elif s >= 62:
            rec = "REVIEW"
        else:
            rec = "REJECT"

        rows.append({
            "candidate_distributor_id": str(d[dist_id]) if dist_id else "NA",
            "candidate_distributor_name": str(d[dist_name]) if dist_name else "",
            "territory_id": terr_id,
            "geography": geo,
            "cluster_id": clu,
            "assigned_micro_market_id": str(d[dist_mm]) if dist_mm else "",
            "coverage_strength_0_1": float(to_num(pd.Series([d[cov]])).fillna(0).iloc[0]) if cov else "",
            "warehouse_score_0_100": float(d["_warehouse_score"]),
            "credit_score_0_100": float(d["_credit_score"]),
            "service_level_score_0_100": float(d["_service_score"]),
            "sellin_strength_0_100": float(d["_sellin_score"]),
            "rgm_acceptance_proxy_0_100": float(d["_rgm_acceptance"]),
            "suitability_0_100": round(s, 1),
            "recommendation": rec,
            "notes": "Matched by assigned_micro_market_id to proposed territory nodes when possible; otherwise geo fallback."
        })

apq = pd.DataFrame(rows)
apq = apq.drop_duplicates(["candidate_distributor_id","territory_id"], keep="first")
apq.to_csv(OUT / "pre_farming_appointment_queue.csv", index=False)

print("OK: wrote Pre-Farming outputs to out/")
print(" - out/pre_farming_whitespace_map.csv")
print(" - out/pre_farming_territory_plan.csv")
print(" - out/pre_farming_appointment_queue.csv")
