from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionName(str, Enum):
    NOOP = "NOOP"
    SCALE_OUT = "SCALE_OUT"
    SCALE_IN = "SCALE_IN"
    THROTTLE_LOW_PRIORITY = "THROTTLE_LOW_PRIORITY"
    REJECT_LOW_PRIORITY = "REJECT_LOW_PRIORITY"
    ENABLE_LONG_CONTEXT_QUEUE = "ENABLE_LONG_CONTEXT_QUEUE"
    WARN_GPU_MEMORY_PRESSURE = "WARN_GPU_MEMORY_PRESSURE"
    WARN_P99_VIOLATION = "WARN_P99_VIOLATION"
    WARN_HPA_LAG = "WARN_HPA_LAG"


@dataclass(slots=True)
class RequestMetrics:
    request_id: str
    tenant_id: str
    workload_type: str
    prompt_tokens: int
    output_tokens: int
    start_time: float
    first_token_time: float | None
    end_time: float
    status_code: int
    error_reason: str = ""
    retry_count: int = 0
    streaming: bool = True

    @property
    def ttft(self) -> float | None:
        if self.first_token_time is None:
            return None
        return max(0.0, self.first_token_time - self.start_time)

    @property
    def latency(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def tpot(self) -> float | None:
        if self.first_token_time is None or self.output_tokens <= 1:
            return None
        return max(0.0, (self.end_time - self.first_token_time) / (self.output_tokens - 1))

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "workload_type": self.workload_type,
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "start_time": self.start_time,
            "first_token_time": self.first_token_time,
            "end_time": self.end_time,
            "ttft": self.ttft,
            "tpot": self.tpot,
            "latency": self.latency,
            "status_code": self.status_code,
            "error_reason": self.error_reason,
            "retry_count": self.retry_count,
            "streaming": self.streaming,
        }


@dataclass(slots=True)
class ControllerMetrics:
    queue_time_p95: float = 0.0
    queue_time_p99: float = 0.0
    ttft_p95: float = 0.0
    ttft_p99: float = 0.0
    tpot_p95: float = 0.0
    tpot_p99: float = 0.0
    e2e_latency_p99: float = 0.0
    waiting_requests: float = 0.0
    running_requests: float = 0.0
    gpu_memory_ratio: float = 0.0
    gpu_utilization: float = 0.0
    prompt_tokens_per_sec: float = 0.0
    generation_tokens_per_sec: float = 0.0
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    current_replicas: int = 1
    long_context_ratio: float = 0.0
    tenant_overload_ratio: float = 0.0
    missing: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Decision:
    action: ActionName
    reason: str
    desired_replicas: int | None = None
    severity: str = "info"
    signals: dict[str, float | int | str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "reason": self.reason,
            "desired_replicas": self.desired_replicas,
            "severity": self.severity,
            "signals": self.signals,
        }

