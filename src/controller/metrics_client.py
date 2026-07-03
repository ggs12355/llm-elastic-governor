from __future__ import annotations

import itertools
import random
from dataclasses import fields

from common.types import ControllerMetrics
from controller.config import ControllerConfig


DEFAULT_QUERIES = {
    "queue_time_p99": 'histogram_quantile(0.99, sum(rate(vllm:request_queue_time_seconds_bucket[1m])) by (le))',
    "ttft_p99": 'histogram_quantile(0.99, sum(rate(vllm:time_to_first_token_seconds_bucket[1m])) by (le))',
    "tpot_p99": 'histogram_quantile(0.99, sum(rate(vllm:time_per_output_token_seconds_bucket[1m])) by (le))',
    "waiting_requests": "sum(vllm:num_requests_waiting)",
    "running_requests": "sum(vllm:num_requests_running)",
    "gpu_memory_ratio": "avg(DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE))",
    "gpu_utilization": "avg(DCGM_FI_DEV_GPU_UTIL) / 100",
    "prompt_tokens_per_sec": "sum(rate(vllm:prompt_tokens_total[1m]))",
    "generation_tokens_per_sec": "sum(rate(vllm:generation_tokens_total[1m]))",
    "error_rate": "sum(rate(vllm:request_failure_total[1m]))",
    "timeout_rate": "0",
}


class PrometheusMetricsClient:
    def __init__(self, base_url: str, config: ControllerConfig, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.queries = {**DEFAULT_QUERIES, **(config.queries or {})}
        self.timeout = timeout

    def collect(self, current_replicas: int = 1) -> ControllerMetrics:
        data = {"current_replicas": current_replicas}
        missing: list[str] = []
        metric_names = {field.name for field in fields(ControllerMetrics)}
        for name, query in self.queries.items():
            if name not in metric_names:
                continue
            value = self._query_scalar(query)
            if value is None:
                missing.append(name)
                value = 0.0
            data[name] = value
        metrics = ControllerMetrics(**data)
        metrics.missing = missing
        return metrics

    def _query_scalar(self, query: str) -> float | None:
        if query.strip() == "0":
            return 0.0
        try:
            import requests

            resp = requests.get(
                f"{self.base_url}/api/v1/query",
                params={"query": query},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
            result = payload.get("data", {}).get("result", [])
            if not result:
                return None
            value = result[0].get("value", [None, None])[1]
            return float(value)
        except Exception:
            return None


class MockMetricsClient:
    def __init__(self, scenario: str = "burst"):
        self.scenario = scenario
        self._step = itertools.count()

    def collect(self, current_replicas: int = 1) -> ControllerMetrics:
        step = next(self._step)
        jitter = random.uniform(-0.05, 0.05)
        if self.scenario == "memory":
            mem = min(0.99, 0.75 + step * 0.03)
            return ControllerMetrics(
                queue_time_p99=1.0,
                ttft_p99=1.5,
                tpot_p99=0.12,
                e2e_latency_p99=10,
                waiting_requests=4,
                running_requests=6,
                gpu_memory_ratio=mem,
                gpu_utilization=0.82,
                prompt_tokens_per_sec=800,
                generation_tokens_per_sec=180,
                current_replicas=current_replicas,
            )
        if self.scenario == "tenant":
            return ControllerMetrics(
                queue_time_p99=1.3,
                ttft_p99=2.0,
                e2e_latency_p99=13,
                waiting_requests=7,
                running_requests=10,
                gpu_memory_ratio=0.82,
                gpu_utilization=0.78,
                tenant_overload_ratio=0.45,
                current_replicas=current_replicas,
            )
        pressure = step >= 2
        return ControllerMetrics(
            queue_time_p99=(0.7 if not pressure else 2.8) + jitter,
            ttft_p99=(1.0 if not pressure else 3.6) + jitter,
            tpot_p99=(0.08 if not pressure else 0.28),
            e2e_latency_p99=(8 if not pressure else 24),
            waiting_requests=(2 if not pressure else 12),
            running_requests=(4 if not pressure else 16),
            gpu_memory_ratio=(0.62 if not pressure else 0.91),
            gpu_utilization=(0.55 if not pressure else 0.9),
            prompt_tokens_per_sec=(500 if not pressure else 1300),
            generation_tokens_per_sec=(120 if not pressure else 280),
            current_replicas=current_replicas,
        )
