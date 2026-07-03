#!/usr/bin/env bash
set -euo pipefail

PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"
mkdir -p results/controller
python -m controller.main --config configs/controller/policy_default.yaml --prometheus-url "$PROMETHEUS_URL" --mode dry-run --iterations "${ITERATIONS:-20}" --decision-log results/controller/decisions.jsonl

