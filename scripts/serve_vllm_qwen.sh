#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-2048}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-16}"
MAX_NUM_BATCHED_TOKENS="${MAX_NUM_BATCHED_TOKENS:-2048}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.60}"
ENFORCE_EAGER="${ENFORCE_EAGER:-1}"
ENABLE_PREFIX_CACHING="${ENABLE_PREFIX_CACHING:-1}"

ARGS=(
  -m vllm.entrypoints.openai.api_server
  --model "$MODEL"
  --host 0.0.0.0
  --port 8000
  --max-model-len "$MAX_MODEL_LEN"
  --max-num-seqs "$MAX_NUM_SEQS"
  --max-num-batched-tokens "$MAX_NUM_BATCHED_TOKENS"
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
)

if [[ "$ENFORCE_EAGER" == "1" ]]; then
  ARGS+=(--enforce-eager)
fi

if [[ "$ENABLE_PREFIX_CACHING" == "1" ]]; then
  ARGS+=(--enable-prefix-caching)
fi

python "${ARGS[@]}"
