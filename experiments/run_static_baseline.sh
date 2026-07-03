#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${VLLM_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
mkdir -p results/static
python -m loadgen.runner --profile configs/load_profiles/steady_short.yaml --base-url "$BASE_URL" --model "$MODEL" --output results/static/steady_short.jsonl
python -m loadgen.analyze --input results/static/steady_short.jsonl --output-dir results/static/analysis

