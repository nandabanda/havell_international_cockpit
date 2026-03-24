from pathlib import Path
import pandas as pd
import streamlit as st
import json

from core.ui_theme import apply_ivory, section
from core.nav_shell import render_premium_nav


render_premium_nav()
apply_ivory()

OUT = Path("out")

# ----------------------------
# Safe readers
# ----------------------------
def read_csv_safe(p: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(p) if p.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def read_json_safe(p: Path):
    try:
        if p.exists():
            return json.loads(p.read_text())
        return {}
    except Exception:
        return {}

# ----------------------------
# Load artifacts
# ----------------------------
dist_summary = read_csv_safe(OUT / "farming_distributor_summary.csv")
sku_weekly = read_csv_safe(OUT / "farming_sku_weekly.csv")
stress_sku = read_csv_safe(OUT / "supply_stress_sku.csv")
resolution = read_csv_safe(OUT / "supply_resolution_actions.csv")
network_summary = read_json_safe(OUT / "farming_network_summary.json")

# ----------------------------
# Header
# ----------------------------
st.title("🌾 Farming Engine — Active Distributor Governance")
section(
    "Purpose",
    "Manage Days of Cover, replenishment discipline, distributor health, and supply stress in an integrated loop."
)

# ============================================================
# 1️⃣ Network Snapshot
# ============================================================
st.divider()
section("1) Network Snapshot", "Executive summary of distributor health.")

if dist_summary.empty:
    st.warning("Missing out/farming_distributor_summary.csv")
else:
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Distributors", dist_summary["distributor_id"].nunique())
    c2.metric("Avg Health Score",
              f"{dist_summary['health_score_0_100'].mean():.1f}"
              if "health_score_0_100" in dist_summary else "-")
    c3.metric("Avg Weighted DoC",
              f"{dist_summary['weighted_doc'].mean():.1f}"
              if "weighted_doc" in dist_summary else "-")
    c4.metric("Capital Locked",
              f"{dist_summary['total_capital_locked'].sum():,.0f}"
              if "total_capital_locked" in dist_summary else "-")

    st.dataframe(dist_summary.head(200), use_container_width=True)

    st.download_button(
        "Download farming_distributor_summary.csv",
        (OUT / "farming_distributor_summary.csv").read_bytes(),
        file_name="farming_distributor_summary.csv",
        mime="text/csv",
        key="dl_farming_summary"
    )

# ============================================================
# 2️⃣ Replenishment & SKU View
# ============================================================
st.divider()
section("2) SKU Weekly & Replenishment View", "Velocity-based view of SKU activity.")

if sku_weekly.empty:
    st.info("Optional file missing: out/farming_sku_weekly.csv")
else:
    st.dataframe(sku_weekly.head(400), use_container_width=True)

    st.download_button(
        "Download farming_sku_weekly.csv",
        (OUT / "farming_sku_weekly.csv").read_bytes(),
        file_name="farming_sku_weekly.csv",
        mime="text/csv",
        key="dl_farming_sku"
    )

# ============================================================
# 3️⃣ Supply Stress Integration
# ============================================================
st.divider()
section("3) Supply Stress Signals", "SKUs or plants under constraint impacting distributor replenishment.")

if stress_sku.empty:
    st.info("Optional file missing: out/supply_stress_sku.csv")
else:
    st.dataframe(stress_sku.head(300), use_container_width=True)

    st.download_button(
        "Download supply_stress_sku.csv",
        (OUT / "supply_stress_sku.csv").read_bytes(),
        file_name="supply_stress_sku.csv",
        mime="text/csv",
        key="dl_farming_stress"
    )

# ============================================================
# 4️⃣ Resolution Actions
# ============================================================
st.divider()
section("4) Resolution Actions", "System-recommended actions: expedite, rebalance, substitute, throttle.")

if resolution.empty:
    st.info("Optional file missing: out/supply_resolution_actions.csv")
else:
    st.dataframe(resolution.head(300), use_container_width=True)

    st.download_button(
        "Download supply_resolution_actions.csv",
        (OUT / "supply_resolution_actions.csv").read_bytes(),
        file_name="supply_resolution_actions.csv",
        mime="text/csv",
        key="dl_farming_resolution"
    )

# ============================================================
# 5️⃣ Network JSON Summary (Optional)
# ============================================================
st.divider()
section("5) Network Summary (JSON)", "Compact executive summary artifact.")

if network_summary:
    st.json(network_summary)
    st.download_button(
        "Download farming_network_summary.json",
        (OUT / "farming_network_summary.json").read_bytes(),
        file_name="farming_network_summary.json",
        mime="application/json",
        key="dl_farming_json"
    )
else:
    st.info("Optional file missing: out/farming_network_summary.json")