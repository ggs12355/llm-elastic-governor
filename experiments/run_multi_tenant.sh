#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${VLLM_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
mkdir -p results/multi_tenant
python -m loadgen.runner --profile configs/load_profiles/multi_tenant_overload.yaml --base-url "$BASE_URL" --model "$MODEL" --output results/multi_tenant/requests.jsonl
python -m loadgen.analyze --input results/multi_tenant/requests.jsonl --output-dir results/multi_tenant/analysis

