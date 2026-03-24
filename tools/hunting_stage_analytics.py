#!/usr/bin/env python3
import pandas as pd
import os
import json
from datetime import datetime

STAGE_ORDER = ["Target","Qualification","Technical","Proposal","Negotiation","Won","Lost"]

def main():
    hist_file = "data/hunting_stage_history.csv"
    opp_file = "out/hunting_enriched.csv"
    out_file = "out/hunting_stage_metrics.json"

    if not os.path.exists(hist_file) or not os.path.exists(opp_file):
        print("Stage history or enriched opportunities not found.")
        return

    hist = pd.read_csv(hist_file)
    opp = pd.read_csv(opp_file)

    hist["date_entered"] = pd.to_datetime(hist["date_entered"], errors="coerce")
    hist = hist.sort_values(["opportunity_id","date_entered"])

    # ---- Stage duration calculation
    hist["next_date"] = hist.groupby("opportunity_id")["date_entered"].shift(-1)
    hist["stage_days"] = (hist["next_date"] - hist["date_entered"]).dt.days

    avg_stage_days = hist.groupby("stage")["stage_days"].mean().round(1).to_dict()

    # ---- True conversion calculation
    stage_counts = hist.groupby(["opportunity_id","stage"]).size().reset_index()[["opportunity_id","stage"]]
    conversion = {}

    for i in range(len(STAGE_ORDER)-1):
        s1 = STAGE_ORDER[i]
        s2 = STAGE_ORDER[i+1]

        entered_s1 = set(stage_counts[stage_counts["stage"]==s1]["opportunity_id"])
        entered_s2 = set(stage_counts[stage_counts["stage"]==s2]["opportunity_id"])

        if len(entered_s1) > 0:
            conversion[f"{s1}_to_{s2}"] = round(len(entered_s2 & entered_s1)/len(entered_s1)*100,1)
        else:
            conversion[f"{s1}_to_{s2}"] = 0.0

    # ---- Sales cycle (created to won)
    opp["created_date"] = pd.to_datetime(opp["created_date"], errors="coerce")
    won = opp[opp["stage"]=="Won"]
    won["cycle_days"] = (pd.Timestamp(datetime.now().date()) - won["created_date"]).dt.days
    avg_cycle = round(won["cycle_days"].mean(),1) if len(won)>0 else 0

    metrics = {
        "avg_stage_days": avg_stage_days,
        "true_conversion_pct": conversion,
        "avg_sales_cycle_days": avg_cycle
    }

    with open(out_file, "w") as f:
        json.dump(metrics, f, indent=2)

    print("Stage analytics written to out/hunting_stage_metrics.json")

if __name__ == "__main__":
    main()
