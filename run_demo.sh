#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

source .venv/bin/activate

pkill -f streamlit || true
streamlit cache clear

# Ensure demo artifacts exist (safe even if already present)
if [ -f tools/farming_supply_orchestrator.py ]; then
  python3 tools/farming_supply_orchestrator.py --demo_if_missing || true
fi

# Start
streamlit run app.py --server.port 8510 --server.headless true
