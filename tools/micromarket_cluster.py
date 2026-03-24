#!/usr/bin/env python3
import os, json
import numpy as np
import pandas as pd
from datetime import datetime

SCORED = "out/micromarket_scored.csv"

FEATURES_DEFAULT = [
    # Core potential drivers
    "demand_proxy_index",
    "growth_proxy_index",
    "construction_velocity_index",
    "infrastructure_spend_index",
    "affluence_index",
    "retail_density_index",
    "logistics_access_index",
    # Competition (kept as a feature; model will separate competitive pockets)
    "competitive_intensity_index",
    # Coverage to separate whitespace vs already covered
    "coverage_index_0_1",
]

def zscore_col(x: pd.Series) -> np.ndarray:
    a = pd.to_numeric(x, errors="coerce").astype(float).to_numpy()
    m = np.nanmean(a)
    s = np.nanstd(a) + 1e-9
    a = np.where(np.isnan(a), m, a)
    return (a - m) / s

def kmeans_numpy(X: np.ndarray, k: int = 6, iters: int = 30, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    if n < k:
        k = max(1, n)

    # k-means++ style init (lightweight)
    centers = np.empty((k, X.shape[1]), dtype=float)
    idx0 = rng.integers(0, n)
    centers[0] = X[idx0]
    d2 = np.full(n, np.inf)

    for i in range(1, k):
        d2 = np.minimum(d2, np.sum((X - centers[i-1])**2, axis=1))
        probs = d2 / (d2.sum() + 1e-9)
        idx = rng.choice(n, p=probs)
        centers[i] = X[idx]

    labels = np.zeros(n, dtype=int)

    for _ in range(iters):
        # assign
        dist = np.sum((X[:, None, :] - centers[None, :, :])**2, axis=2)
        new_labels = np.argmin(dist, axis=1)

        if np.array_equal(new_labels, labels):
            break
        labels = new_labels

        # update
        for j in range(k):
            mask = labels == j
            if mask.sum() == 0:
                # re-seed empty cluster
                centers[j] = X[rng.integers(0, n)]
            else:
                centers[j] = X[mask].mean(axis=0)

    # final distances to center (for similarity score)
    dist = np.sqrt(np.sum((X - centers[labels])**2, axis=1))
    return labels, centers, dist

def similarity_from_dist(d: np.ndarray) -> np.ndarray:
    # convert distance to 0-100 similarity (higher is more similar to cluster centroid)
    # robust scale using percentile
    p90 = np.percentile(d, 90) + 1e-9
    sim = 100 * (1 - np.clip(d / p90, 0, 1))
    return sim.round(1)

def main(k=6):
    if not os.path.exists(SCORED):
        raise SystemExit("Missing out/micromarket_scored.csv. Run: python3 tools/micromarket_engine.py")

    df = pd.read_csv(SCORED)

    # pick features present
    feats = [c for c in FEATURES_DEFAULT if c in df.columns]
    if len(feats) < 4:
        raise SystemExit(f"Not enough features found for clustering. Present: {feats}")

    X = np.column_stack([zscore_col(df[c]) for c in feats])

    labels, centers, dist = kmeans_numpy(X, k=int(k), iters=40, seed=42)
    df["cluster_id"] = labels.astype(int)
    df["cluster_similarity_0_100"] = similarity_from_dist(dist)

    # Cluster “winner pockets”: high attractiveness + whitespace
    df["winner_score"] = (
        0.55 * pd.to_numeric(df.get("whitespace_score_0_100", 0), errors="coerce").fillna(0) +
        0.35 * pd.to_numeric(df.get("attractiveness_score_0_100", 0), errors="coerce").fillna(0) +
        0.10 * df["cluster_similarity_0_100"]
    ).round(1)

    # Cluster profile summary
    grp = df.groupby("cluster_id").agg(
        micro_markets=("micro_market_id","nunique"),
        avg_attractiveness=("attractiveness_score_0_100","mean"),
        avg_whitespace=("whitespace_score_0_100","mean"),
        avg_coverage=("coverage_index_0_1","mean"),
        total_gap=("distributor_gap","sum"),
        avg_readiness=("data_readiness_0_100","mean")
    ).reset_index()

    grp = grp.sort_values("avg_whitespace", ascending=False)

    # Recommendations: top 5 “winner” + top 5 “look-alikes”
    recos = []
    for cid in sorted(df["cluster_id"].unique()):
        sub = df[df["cluster_id"] == cid].copy()
        sub = sub.sort_values(["winner_score","cluster_similarity_0_100"], ascending=False)

        winners = sub.head(5).assign(reco_type="WINNER")
        lookalikes = sub.sort_values("cluster_similarity_0_100", ascending=False).head(5).assign(reco_type="LOOKALIKE")

        out = pd.concat([winners, lookalikes], ignore_index=True)
        keep = [
            "reco_type","cluster_id","micro_market_id","country","region","city","district",
            "attractiveness_score_0_100","whitespace_score_0_100","coverage_index_0_1",
            "distributor_gap","recommended_distributor_count","current_distributor_count",
            "data_readiness_0_100","cluster_similarity_0_100","why_now"
        ]
        keep = [c for c in keep if c in out.columns]
        recos.append(out[keep])

    recos_df = pd.concat(recos, ignore_index=True) if recos else pd.DataFrame()

    os.makedirs("out", exist_ok=True)
    df.to_csv("out/micromarket_clusters.csv", index=False)
    recos_df.to_csv("out/micromarket_cluster_recos.csv", index=False)
    grp.to_csv("out/micromarket_cluster_profiles.csv", index=False)

    summary = {
        "as_of": str(datetime.now().date()),
        "k": int(df["cluster_id"].nunique()),
        "features_used": feats,
        "top_cluster_by_whitespace": int(grp.iloc[0]["cluster_id"]) if len(grp) else None
    }
    with open("out/micromarket_cluster_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("OK: out/micromarket_clusters.csv")
    print("OK: out/micromarket_cluster_recos.csv")
    print("OK: out/micromarket_cluster_profiles.csv")
    print("OK: out/micromarket_cluster_summary.json")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=6)
    args = ap.parse_args()
    main(k=args.k)
