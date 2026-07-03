#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${VLLM_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
mkdir -p results/long_context_mix
python -m loadgen.runner --profile configs/load_profiles/long_context_mix.yaml --base-url "$BASE_URL" --model "$MODEL" --output results/long_context_mix/requests.jsonl
python -m loadgen.analyze --input results/long_context_mix/requests.jsonl --output-dir results/long_context_mix/analysis

