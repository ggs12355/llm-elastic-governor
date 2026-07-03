#!/usr/bin/env bash
set -euo pipefail

PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"
python -m controller.main --config configs/controller/policy_default.yaml --prometheus-url "$PROMETHEUS_URL" --mode active

