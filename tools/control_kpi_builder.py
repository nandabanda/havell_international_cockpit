import os
import pandas as pd
from datetime import datetime

OUT = "out"
os.makedirs(OUT, exist_ok=True)

def load_csv(name):
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def week_col(df):
    for c in ["week_id", "week", "wk", "period", "week_start", "date"]:
        if c in df.columns:
            return c
    return None

def ensure_week_id(df):
    if df is None or df.empty:
        return df
    c = week_col(df)
    if c is None:
        df = df.copy()
        df["week_id"] = datetime.now().strftime("%Y-W%U")
        return df
    if c != "week_id":
        df = df.copy()
        df["week_id"] = df[c].astype(str)
    else:
        df = df.copy()
        df["week_id"] = df["week_id"].astype(str)
    return df

def safe_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def pick(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def compute_hunting():
    sig = load_csv("hunting_forward_signal.csv")
    q   = load_csv("hunting_approval_queue.csv")

    sig = ensure_week_id(sig)
    q   = ensure_week_id(q)

    if sig.empty:
        return pd.DataFrame(columns=[
            "week_id","revenue","spend","gross_margin","profit","gm_pct",
            "pipeline_value","pipeline_count","approvals_pending","approvals_high_sev"
        ])

    rev_c = pick(sig, ["expected_revenue","expected_value","revenue","value"])
    spd_c = pick(sig, ["expected_spend","spend","trade_spend","investment"])
    gm_c  = pick(sig, ["expected_gm","gross_margin_value","gm_value","contribution"])

    sig["_revenue"] = safe_num(sig[rev_c]) if rev_c else 0.0
    sig["_spend"]   = safe_num(sig[spd_c]) if spd_c else 0.0
    sig["_gm"]      = safe_num(sig[gm_c])  if gm_c else 0.0

    g = sig.groupby("week_id", dropna=False).agg(
        revenue=("_revenue","sum"),
        spend=("_spend","sum"),
        gross_margin=("_gm","sum"),
        pipeline_value=("_revenue","sum"),
        pipeline_count=("week_id","size"),
    ).reset_index()

    g["profit"] = g["gross_margin"] - g["spend"]
    g["gm_pct"] = g.apply(lambda r: (r["gross_margin"]/r["revenue"]*100) if r["revenue"]>0 else 0.0, axis=1)

    # Approvals
    if not q.empty:
        sev_c = pick(q, ["severity","severity_score"])
        q["_sev"] = safe_num(q[sev_c]) if sev_c else 0.0
        qa = q.groupby("week_id", dropna=False).agg(
            approvals_pending=("week_id","size"),
            approvals_high_sev=("_sev", lambda x: (x>70).sum()),
        ).reset_index()
        g = g.merge(qa, on="week_id", how="left")
    else:
        g["approvals_pending"] = 0
        g["approvals_high_sev"] = 0

    g.fillna(0, inplace=True)
    return g

def compute_farming():
    dist = load_csv("farming_distributor_summary.csv")
    sku  = load_csv("farming_sku_weekly.csv")

    dist = ensure_week_id(dist)
    sku  = ensure_week_id(sku)

    # Base schema
    base_cols = [
        "week_id","revenue","spend","gross_margin","profit","gm_pct",
        "active_distributors","fill_rate","doh","service_risk_skus","value_at_risk"
    ]

    if dist.empty and sku.empty:
        return pd.DataFrame(columns=base_cols)

    # Revenue/spend/gm from dist if possible
    if not dist.empty:
        rev_c = pick(dist, ["sell_in_value","sellout_value","revenue","value","last_90d_sell_in_value","last_30d_sell_in_value"])
        spd_c = pick(dist, ["spend","trade_spend","rebates","discount_value"])
        gm_c  = pick(dist, ["gross_margin_value","gm_value","contribution","profit_value","gross_margin"])

        dist["_revenue"] = safe_num(dist[rev_c]) if rev_c else 0.0
        dist["_spend"]   = safe_num(dist[spd_c]) if spd_c else 0.0
        dist["_gm"]      = safe_num(dist[gm_c])  if gm_c else 0.0

        if "distributor_id" in dist.columns:
            dist["_ad"] = dist["distributor_id"].astype(str)
        else:
            dist["_ad"] = "NA"

        g = dist.groupby("week_id", dropna=False).agg(
            revenue=("_revenue","sum"),
            spend=("_spend","sum"),
            gross_margin=("_gm","sum"),
            active_distributors=("_ad","nunique"),
        ).reset_index()
    else:
        g = pd.DataFrame({"week_id": sku["week_id"].unique().tolist()})
        g["revenue"]=0.0; g["spend"]=0.0; g["gross_margin"]=0.0; g["active_distributors"]=0

    # Service metrics from sku
    if not sku.empty:
        fr_c = pick(sku, ["fill_rate","service_level","otif"])
        doh_c = pick(sku, ["doh","days_on_hand","days_cover","doH"])
        sku["_fr"] = safe_num(sku[fr_c]) if fr_c else 0.0
        sku["_doh"] = safe_num(sku[doh_c]) if doh_c else 0.0

        gs = sku.groupby("week_id", dropna=False).agg(
            fill_rate=("_fr","mean"),
            doh=("_doh","mean"),
        ).reset_index()

        g = g.merge(gs, on="week_id", how="left")
    else:
        g["fill_rate"]=0.0; g["doh"]=0.0

    # Add supply risk overlays if present
    stress = load_csv("supply_stress_sku.csv")
    stress = ensure_week_id(stress)
    if not stress.empty:
        var_c = pick(stress, ["value_at_risk","revenue_at_risk","risk_value"])
        stress["_var"] = safe_num(stress[var_c]) if var_c else 0.0
        stg = stress.groupby("week_id", dropna=False).agg(
            service_risk_skus=("week_id","size"),
            value_at_risk=("_var","sum"),
        ).reset_index()
        g = g.merge(stg, on="week_id", how="left")
    else:
        g["service_risk_skus"]=0; g["value_at_risk"]=0.0

    g["profit"] = g["gross_margin"] - g["spend"]
    g["gm_pct"] = g.apply(lambda r: (r["gross_margin"]/r["revenue"]*100) if r["revenue"]>0 else 0.0, axis=1)

    # Ensure columns
    for c in base_cols:
        if c not in g.columns:
            g[c] = 0
    g = g[base_cols].copy()
    g.fillna(0, inplace=True)
    return g

def compute_total(h, f):
    if h.empty and f.empty:
        return pd.DataFrame(columns=["week_id","revenue","spend","gross_margin","profit","gm_pct"])
    weeks = sorted(set(h["week_id"].tolist() if not h.empty else []) | set(f["week_id"].tolist() if not f.empty else []))
    t = pd.DataFrame({"week_id": weeks})

    def merge_sum(df, prefix):
        if df.empty:
            return
        cols = ["week_id","revenue","spend","gross_margin","profit"]
        m = df[cols].copy()
        m = m.rename(columns={c:f"{prefix}_{c}" for c in cols if c!="week_id"})
        return m

    mh = merge_sum(h, "h")
    mf = merge_sum(f, "f")
    if mh is not None: t = t.merge(mh, on="week_id", how="left")
    if mf is not None: t = t.merge(mf, on="week_id", how="left")
    t.fillna(0, inplace=True)

    t["revenue"] = t.get("h_revenue",0) + t.get("f_revenue",0)
    t["spend"]   = t.get("h_spend",0) + t.get("f_spend",0)
    t["gross_margin"] = t.get("h_gross_margin",0) + t.get("f_gross_margin",0)
    t["profit"]  = t.get("h_profit",0) + t.get("f_profit",0)
    t["gm_pct"]  = t.apply(lambda r: (r["gross_margin"]/r["revenue"]*100) if r["revenue"]>0 else 0.0, axis=1)

    return t[["week_id","revenue","spend","gross_margin","profit","gm_pct"]]

def main():
    h = compute_hunting()
    f = compute_farming()
    t = compute_total(h, f)

    h.to_csv(os.path.join(OUT, "control_kpi_hunting.csv"), index=False)
    f.to_csv(os.path.join(OUT, "control_kpi_farming.csv"), index=False)
    t.to_csv(os.path.join(OUT, "control_kpi_total.csv"), index=False)

    print("OK: wrote out/control_kpi_hunting.csv, out/control_kpi_farming.csv, out/control_kpi_total.csv")

if __name__ == "__main__":
    main()
