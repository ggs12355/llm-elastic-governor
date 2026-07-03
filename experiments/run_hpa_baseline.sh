#!/usr/bin/env bash
set -euo pipefail

echo "HPA-like baseline uses deploy/k8s/hpa-baseline.yaml or KEDA ScaledObject."
echo "For local learning, run the same workload and compare against controller decisions."
BASE_URL="${VLLM_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
mkdir -p results/hpa
python -m loadgen.runner --profile configs/load_profiles/burst.yaml --base-url "$BASE_URL" --model "$MODEL" --output results/hpa/burst.jsonl
python -m loadgen.analyze --input results/hpa/burst.jsonl --output-dir results/hpa/analysis

