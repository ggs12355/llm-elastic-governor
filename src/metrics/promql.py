from __future__ import annotations

VLLM_PROMQL = {
    "queue_time_p99": 'histogram_quantile(0.99, sum(rate(vllm:request_queue_time_seconds_bucket[1m])) by (le))',
    "ttft_p99": 'histogram_quantile(0.99, sum(rate(vllm:time_to_first_token_seconds_bucket[1m])) by (le))',
    "tpot_p99": 'histogram_quantile(0.99, sum(rate(vllm:time_per_output_token_seconds_bucket[1m])) by (le))',
    "waiting_requests": "sum(vllm:num_requests_waiting)",
    "running_requests": "sum(vllm:num_requests_running)",
    "prompt_tokens_per_sec": "sum(rate(vllm:prompt_tokens_total[1m]))",
    "generation_tokens_per_sec": "sum(rate(vllm:generation_tokens_total[1m]))",
}

DCGM_PROMQL = {
    "gpu_utilization": "avg(DCGM_FI_DEV_GPU_UTIL) / 100",
    "gpu_memory_ratio": "avg(DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE))",
    "gpu_power_watts": "avg(DCGM_FI_DEV_POWER_USAGE)",
    "gpu_temperature": "avg(DCGM_FI_DEV_GPU_TEMP)",
}

