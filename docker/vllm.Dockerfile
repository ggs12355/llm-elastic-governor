FROM vllm/vllm-openai:latest

ENV MODEL=Qwen/Qwen2.5-1.5B-Instruct
ENV MAX_MODEL_LEN=8192
ENV GPU_MEMORY_UTILIZATION=0.90

ENTRYPOINT ["sh", "-c", "python -m vllm.entrypoints.openai.api_server --host 0.0.0.0 --port 8000 --model ${MODEL} --max-model-len ${MAX_MODEL_LEN} --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION} --enable-prefix-caching"]

