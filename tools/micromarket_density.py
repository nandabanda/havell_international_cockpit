#!/usr/bin/env python3
"""
Micro-Market Density Model (Distributor Development)
Outputs:
- out/micromarket_density_micro.csv  (micro-market level)
- out/micromarket_density_cluster.csv (cluster/archetype level)
"""

from __future__ import annotations
import os
import math
import argparse
import pandas as pd


def _safe_read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _clamp(x: float, lo: float, hi: float) -> float:
    if pd.isna(x):
        return lo
    return max(lo, min(hi, float(x)))


def run(
    clusters_csv: str,
    distributors_csv: str,
    out_micro: str,
    out_cluster: str,
    target_micro_per_dist: int,
    min_dist_per_micro: int,
    max_dist_per_micro: int,
    min_dist_per_cluster: int,
    max_dist_per_cluster: int,
) -> None:
    cl = _safe_read_csv(clusters_csv)
    if cl.empty:
        raise FileNotFoundError(f"Missing/empty: {clusters_csv}")

    # Existing distributors coverage (optional)
    dist = _safe_read_csv(distributors_csv)
    if dist.empty:
        dist_mm = pd.DataFrame(columns=["micro_market_id", "existing_distributors"])
    else:
        if "assigned_micro_market_id" in dist.columns:
            dist_mm = (
                dist.groupby("assigned_micro_market_id")
                .size()
                .reset_index(name="existing_distributors")
                .rename(columns={"assigned_micro_market_id": "micro_market_id"})
            )
        elif "micro_market_id" in dist.columns:
            dist_mm = dist.groupby("micro_market_id").size().reset_index(name="existing_distributors")
        else:
            dist_mm = pd.DataFrame(columns=["micro_market_id", "existing_distributors"])

    # Normalize schema expectations
    if "micro_market_id" not in cl.columns:
        raise ValueError("clusters file must contain micro_market_id")

    if "cluster_id" not in cl.columns:
        cl["cluster_id"] = "NA"

    # numeric safety
    cl = _to_num(
        cl,
        [
            "whitespace_score_0_100",
            "attractiveness_score_0_100",
            "coverage_index_0_1",
            "demand_proxy_index",
            "growth_proxy_index",
            "population_index",
            "competitive_intensity_index",
        ],
    )

    # Fill defaults (keeps tool robust)
    if "whitespace_score_0_100" not in cl.columns:
        cl["whitespace_score_0_100"] = 50
    if "attractiveness_score_0_100" not in cl.columns:
        cl["attractiveness_score_0_100"] = 50
    if "coverage_index_0_1" not in cl.columns:
        cl["coverage_index_0_1"] = 0.5

    # Density score: "how many micro-markets can one distributor reasonably cover?"
    # Lower coverage_index => low coverage => need more density.
    # Higher attractiveness + whitespace => need more density.
    # Competitive intensity slightly reduces recommended density (harder economics).
    comp = cl["competitive_intensity_index"] if "competitive_intensity_index" in cl.columns else 50

    # Convert to 0..1 bands
    A = (cl["attractiveness_score_0_100"] / 100.0).fillna(0.5)
    W = (cl["whitespace_score_0_100"] / 100.0).fillna(0.5)
    C = cl["coverage_index_0_1"].fillna(0.5)  # 0..1
    COMP = (comp / 100.0).fillna(0.5)

    # Opportunity index 0..1 (bounded)
    opp = (0.55 * A + 0.45 * W)
    opp = opp.clip(0.05, 0.98)

    # Coverage pressure 0..1 (low coverage = high pressure)
    pressure = (1.0 - C).clip(0.0, 1.0)

    # Competition dampener (more competition => slightly lower recommendation)
    damp = (1.0 - 0.15 * COMP).clip(0.75, 1.0)

    # Final density score (0..~1.2)
    density_score = (0.60 * opp + 0.40 * pressure) * damp

    # Convert to recommended distributors per micro-market:
    # baseline: 1 distributor per N micro-markets; higher density_score => fewer micro-markets per distributor => more distributors.
    # We scale density_score to micro-per-distributor band.
    # Example: density_score 0.2 -> ~target*1.4 micro/dist; 0.9 -> ~target*0.6 micro/dist
    micro_per_dist = target_micro_per_dist * (1.4 - density_score.clip(0.0, 1.0) * 0.8)
    micro_per_dist = micro_per_dist.clip(max(1, int(target_micro_per_dist * 0.4)), int(target_micro_per_dist * 1.6))

    # recommended distributors for a micro-market = ceil(1 / (micro_per_dist / target_micro_per_dist)) but
    # micro-market is atomic, so we treat it as "share of a distributor required":
    # dist_need = target_micro_per_dist / micro_per_dist, then clamp to min/max.
    dist_need = (target_micro_per_dist / micro_per_dist).clip(0.25, 3.0)
    rec_micro = dist_need.apply(lambda x: int(_clamp(math.ceil(x), min_dist_per_micro, max_dist_per_micro)))

    out = cl.merge(dist_mm, on="micro_market_id", how="left")
    out["existing_distributors"] = out["existing_distributors"].fillna(0).astype(int)

    out["density_score_0_100"] = (density_score.clip(0, 1) * 100).round(1)
    out["recommended_distributors_micro"] = rec_micro
    out["density_gap_micro"] = out["recommended_distributors_micro"] - out["existing_distributors"]
    out["density_gap_micro"] = out["density_gap_micro"].astype(int)

    # Cluster-level rollup
    grp_cols = ["cluster_id"]
    for c in ["country", "region"]:
        if c in out.columns:
            grp_cols.append(c)

    agg = (
        out.groupby(grp_cols)
        .agg(
            micro_markets=("micro_market_id", "nunique"),
            avg_density_score=("density_score_0_100", "mean"),
            avg_attractiveness=("attractiveness_score_0_100", "mean"),
            avg_whitespace=("whitespace_score_0_100", "mean"),
            avg_coverage=("coverage_index_0_1", "mean"),
            existing_distributors=("existing_distributors", "sum"),
            recommended_distributors=("recommended_distributors_micro", "sum"),
        )
        .reset_index()
    )

    # Clamp cluster recommendation bounds
    agg["recommended_distributors"] = agg["recommended_distributors"].apply(
        lambda x: int(_clamp(x, min_dist_per_cluster, max_dist_per_cluster))
    )
    agg["density_gap"] = (agg["recommended_distributors"] - agg["existing_distributors"]).astype(int)
    agg["avg_density_score"] = agg["avg_density_score"].round(1)
    agg["avg_attractiveness"] = agg["avg_attractiveness"].round(1)
    agg["avg_whitespace"] = agg["avg_whitespace"].round(1)
    agg["avg_coverage"] = agg["avg_coverage"].round(3)

    os.makedirs(os.path.dirname(out_micro) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(out_cluster) or ".", exist_ok=True)

    out.to_csv(out_micro, index=False)
    agg.to_csv(out_cluster, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clusters", default="out/micromarket_clusters.csv")
    ap.add_argument("--distributors", default="data/distributors_existing.csv")
    ap.add_argument("--out_micro", default="out/micromarket_density_micro.csv")
    ap.add_argument("--out_cluster", default="out/micromarket_density_cluster.csv")

    ap.add_argument("--target_micro_per_dist", type=int, default=4, help="Baseline: 1 distributor per N micro-markets")
    ap.add_argument("--min_dist_per_micro", type=int, default=1)
    ap.add_argument("--max_dist_per_micro", type=int, default=3)

    ap.add_argument("--min_dist_per_cluster", type=int, default=2)
    ap.add_argument("--max_dist_per_cluster", type=int, default=999)

    args = ap.parse_args()

    run(
        clusters_csv=args.clusters,
        distributors_csv=args.distributors,
        out_micro=args.out_micro,
        out_cluster=args.out_cluster,
        target_micro_per_dist=args.target_micro_per_dist,
        min_dist_per_micro=args.min_dist_per_micro,
        max_dist_per_micro=args.max_dist_per_micro,
        min_dist_per_cluster=args.min_dist_per_cluster,
        max_dist_per_cluster=args.max_dist_per_cluster,
    )
    print("OK: wrote", args.out_micro, "and", args.out_cluster)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Micro-Market Density Model (Distributor Development)
Outputs:
- out/micromarket_density_micro.csv  (micro-market level)
- out/micromarket_density_cluster.csv (cluster/archetype level)
"""

from __future__ import annotations
import os
import math
import argparse
import pandas as pd


def _safe_read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _clamp(x: float, lo: float, hi: float) -> float:
    if pd.isna(x):
        return lo
    return max(lo, min(hi, float(x)))


def run(
    clusters_csv: str,
    distributors_csv: str,
    out_micro: str,
    out_cluster: str,
    target_micro_per_dist: int,
    min_dist_per_micro: int,
    max_dist_per_micro: int,
    min_dist_per_cluster: int,
    max_dist_per_cluster: int,
) -> None:
    cl = _safe_read_csv(clusters_csv)
    if cl.empty:
        raise FileNotFoundError(f"Missing/empty: {clusters_csv}")

    # Existing distributors coverage (optional)
    dist = _safe_read_csv(distributors_csv)
    if dist.empty:
        dist_mm = pd.DataFrame(columns=["micro_market_id", "existing_distributors"])
    else:
        if "assigned_micro_market_id" in dist.columns:
            dist_mm = (
                dist.groupby("assigned_micro_market_id")
                .size()
                .reset_index(name="existing_distributors")
                .rename(columns={"assigned_micro_market_id": "micro_market_id"})
            )
        elif "micro_market_id" in dist.columns:
            dist_mm = dist.groupby("micro_market_id").size().reset_index(name="existing_distributors")
        else:
            dist_mm = pd.DataFrame(columns=["micro_market_id", "existing_distributors"])

    # Normalize schema expectations
    if "micro_market_id" not in cl.columns:
        raise ValueError("clusters file must contain micro_market_id")

    if "cluster_id" not in cl.columns:
        cl["cluster_id"] = "NA"

    # numeric safety
    cl = _to_num(
        cl,
        [
            "whitespace_score_0_100",
            "attractiveness_score_0_100",
            "coverage_index_0_1",
            "demand_proxy_index",
            "growth_proxy_index",
            "population_index",
            "competitive_intensity_index",
        ],
    )

    # Fill defaults (keeps tool robust)
    if "whitespace_score_0_100" not in cl.columns:
        cl["whitespace_score_0_100"] = 50
    if "attractiveness_score_0_100" not in cl.columns:
        cl["attractiveness_score_0_100"] = 50
    if "coverage_index_0_1" not in cl.columns:
        cl["coverage_index_0_1"] = 0.5

    # Density score: "how many micro-markets can one distributor reasonably cover?"
    # Lower coverage_index => low coverage => need more density.
    # Higher attractiveness + whitespace => need more density.
    # Competitive intensity slightly reduces recommended density (harder economics).
    comp = cl["competitive_intensity_index"] if "competitive_intensity_index" in cl.columns else 50

    # Convert to 0..1 bands
    A = (cl["attractiveness_score_0_100"] / 100.0).fillna(0.5)
    W = (cl["whitespace_score_0_100"] / 100.0).fillna(0.5)
    C = cl["coverage_index_0_1"].fillna(0.5)  # 0..1
    COMP = (comp / 100.0).fillna(0.5)

    # Opportunity index 0..1 (bounded)
    opp = (0.55 * A + 0.45 * W)
    opp = opp.clip(0.05, 0.98)

    # Coverage pressure 0..1 (low coverage = high pressure)
    pressure = (1.0 - C).clip(0.0, 1.0)

    # Competition dampener (more competition => slightly lower recommendation)
    damp = (1.0 - 0.15 * COMP).clip(0.75, 1.0)

    # Final density score (0..~1.2)
    density_score = (0.60 * opp + 0.40 * pressure) * damp

    # Convert to recommended distributors per micro-market:
    # baseline: 1 distributor per N micro-markets; higher density_score => fewer micro-markets per distributor => more distributors.
    # We scale density_score to micro-per-distributor band.
    # Example: density_score 0.2 -> ~target*1.4 micro/dist; 0.9 -> ~target*0.6 micro/dist
    micro_per_dist = target_micro_per_dist * (1.4 - density_score.clip(0.0, 1.0) * 0.8)
    micro_per_dist = micro_per_dist.clip(max(1, int(target_micro_per_dist * 0.4)), int(target_micro_per_dist * 1.6))

    # recommended distributors for a micro-market = ceil(1 / (micro_per_dist / target_micro_per_dist)) but
    # micro-market is atomic, so we treat it as "share of a distributor required":
    # dist_need = target_micro_per_dist / micro_per_dist, then clamp to min/max.
    dist_need = (target_micro_per_dist / micro_per_dist).clip(0.25, 3.0)
    rec_micro = dist_need.apply(lambda x: int(_clamp(math.ceil(x), min_dist_per_micro, max_dist_per_micro)))

    out = cl.merge(dist_mm, on="micro_market_id", how="left")
    out["existing_distributors"] = out["existing_distributors"].fillna(0).astype(int)

    out["density_score_0_100"] = (density_score.clip(0, 1) * 100).round(1)
    out["recommended_distributors_micro"] = rec_micro
    out["density_gap_micro"] = out["recommended_distributors_micro"] - out["existing_distributors"]
    out["density_gap_micro"] = out["density_gap_micro"].astype(int)

    # Cluster-level rollup
    grp_cols = ["cluster_id"]
    for c in ["country", "region"]:
        if c in out.columns:
            grp_cols.append(c)

    agg = (
        out.groupby(grp_cols)
        .agg(
            micro_markets=("micro_market_id", "nunique"),
            avg_density_score=("density_score_0_100", "mean"),
            avg_attractiveness=("attractiveness_score_0_100", "mean"),
            avg_whitespace=("whitespace_score_0_100", "mean"),
            avg_coverage=("coverage_index_0_1", "mean"),
            existing_distributors=("existing_distributors", "sum"),
            recommended_distributors=("recommended_distributors_micro", "sum"),
        )
        .reset_index()
    )

    # Clamp cluster recommendation bounds
    agg["recommended_distributors"] = agg["recommended_distributors"].apply(
        lambda x: int(_clamp(x, min_dist_per_cluster, max_dist_per_cluster))
    )
    agg["density_gap"] = (agg["recommended_distributors"] - agg["existing_distributors"]).astype(int)
    agg["avg_density_score"] = agg["avg_density_score"].round(1)
    agg["avg_attractiveness"] = agg["avg_attractiveness"].round(1)
    agg["avg_whitespace"] = agg["avg_whitespace"].round(1)
    agg["avg_coverage"] = agg["avg_coverage"].round(3)

    os.makedirs(os.path.dirname(out_micro) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(out_cluster) or ".", exist_ok=True)

    out.to_csv(out_micro, index=False)
    agg.to_csv(out_cluster, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clusters", default="out/micromarket_clusters.csv")
    ap.add_argument("--distributors", default="data/distributors_existing.csv")
    ap.add_argument("--out_micro", default="out/micromarket_density_micro.csv")
    ap.add_argument("--out_cluster", default="out/micromarket_density_cluster.csv")

    ap.add_argument("--target_micro_per_dist", type=int, default=4, help="Baseline: 1 distributor per N micro-markets")
    ap.add_argument("--min_dist_per_micro", type=int, default=1)
    ap.add_argument("--max_dist_per_micro", type=int, default=3)

    ap.add_argument("--min_dist_per_cluster", type=int, default=2)
    ap.add_argument("--max_dist_per_cluster", type=int, default=999)

    args = ap.parse_args()

    run(
        clusters_csv=args.clusters,
        distributors_csv=args.distributors,
        out_micro=args.out_micro,
        out_cluster=args.out_cluster,
        target_micro_per_dist=args.target_micro_per_dist,
        min_dist_per_micro=args.min_dist_per_micro,
        max_dist_per_micro=args.max_dist_per_micro,
        min_dist_per_cluster=args.min_dist_per_cluster,
        max_dist_per_cluster=args.max_dist_per_cluster,
    )
    print("OK: wrote", args.out_micro, "and", args.out_cluster)


if __name__ == "__main__":
    main()
