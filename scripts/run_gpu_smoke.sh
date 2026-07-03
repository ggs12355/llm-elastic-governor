#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${VLLM_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"

mkdir -p results/gpu_smoke

curl -sS "$BASE_URL/v1/models" | jq .

python -m metrics.gpu_collector \
  --interval 2 \
  --duration 30 \
  --output results/gpu_smoke/gpu_metrics.jsonl &
GPU_COLLECTOR_PID=$!

python -m loadgen.runner \
  --profile configs/load_profiles/steady_short.yaml \
  --base-url "$BASE_URL" \
  --model "$MODEL" \
  --output results/gpu_smoke/requests.jsonl

wait "$GPU_COLLECTOR_PID" || true

python -m loadgen.analyze \
  --input results/gpu_smoke/requests.jsonl \
  --output-dir results/gpu_smoke/analysis

