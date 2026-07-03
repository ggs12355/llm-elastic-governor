from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class PolicyThresholds:
    queue_time_p99_high: float = 2.0
    ttft_p99_high: float = 3.0
    tpot_p99_high: float = 0.25
    e2e_latency_p99_high: float = 20.0
    waiting_requests_high: float = 8.0
    gpu_memory_ratio_high: float = 0.90
    gpu_memory_ratio_critical: float = 0.96
    gpu_utilization_low: float = 0.35
    gpu_utilization_high: float = 0.85
    error_rate_high: float = 0.03
    timeout_rate_high: float = 0.02
    long_context_ratio_high: float = 0.25
    tenant_overload_ratio_high: float = 0.30


@dataclass(slots=True)
class ControllerConfig:
    namespace: str = "llm-serving"
    deployment: str = "vllm-qwen"
    mode: str = "dry-run"
    min_replicas: int = 1
    max_replicas: int = 4
    scale_step: int = 1
    window_seconds: int = 60
    cooldown_seconds: int = 120
    scale_in_cooldown_seconds: int = 300
    hysteresis_windows: int = 2
    loop_interval_seconds: int = 15
    thresholds: PolicyThresholds = field(default_factory=PolicyThresholds)
    queries: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> ControllerConfig:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ControllerConfig:
        thresholds = PolicyThresholds(**(data.get("thresholds") or {}))
        known = {
            "namespace",
            "deployment",
            "mode",
            "min_replicas",
            "max_replicas",
            "scale_step",
            "window_seconds",
            "cooldown_seconds",
            "scale_in_cooldown_seconds",
            "hysteresis_windows",
            "loop_interval_seconds",
            "queries",
        }
        kwargs = {k: v for k, v in data.items() if k in known}
        return cls(**kwargs, thresholds=thresholds)

