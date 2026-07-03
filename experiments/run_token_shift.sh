#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${VLLM_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
mkdir -p results/token_shift
python -m loadgen.runner --profile configs/load_profiles/token_shift.yaml --base-url "$BASE_URL" --model "$MODEL" --output results/token_shift/requests.jsonl
python -m loadgen.analyze --input results/token_shift/requests.jsonl --output-dir results/token_shift/analysis

