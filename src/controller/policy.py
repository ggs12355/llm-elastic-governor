from __future__ import annotations

import time
from dataclasses import dataclass, field

from common.types import ActionName, ControllerMetrics, Decision
from controller.config import ControllerConfig


@dataclass
class ControllerState:
    last_scale_out_ts: float = 0.0
    last_scale_in_ts: float = 0.0
    pressure_windows: int = 0
    relief_windows: int = 0
    last_action: ActionName = ActionName.NOOP


@dataclass
class SLOPolicy:
    config: ControllerConfig
    state: ControllerState = field(default_factory=ControllerState)

    def decide(self, metrics: ControllerMetrics, now: float | None = None) -> Decision:
        ts = time.time() if now is None else now
        th = self.config.thresholds
        current = max(self.config.min_replicas, metrics.current_replicas)
        signals = {
            "queue_time_p99": metrics.queue_time_p99,
            "ttft_p99": metrics.ttft_p99,
            "tpot_p99": metrics.tpot_p99,
            "e2e_latency_p99": metrics.e2e_latency_p99,
            "waiting_requests": metrics.waiting_requests,
            "running_requests": metrics.running_requests,
            "gpu_memory_ratio": metrics.gpu_memory_ratio,
            "gpu_utilization": metrics.gpu_utilization,
            "error_rate": metrics.error_rate,
            "timeout_rate": metrics.timeout_rate,
            "current_replicas": current,
        }

        if metrics.missing:
            return Decision(
                ActionName.NOOP,
                f"missing metrics: {','.join(metrics.missing)}; fallback to no-op",
                severity="warning",
                signals=signals,
            )

        if metrics.gpu_memory_ratio >= th.gpu_memory_ratio_critical:
            return Decision(
                ActionName.REJECT_LOW_PRIORITY,
                "critical GPU memory pressure; reject low-priority or long-context requests",
                desired_replicas=current,
                severity="critical",
                signals=signals,
            )

        if metrics.tenant_overload_ratio >= th.tenant_overload_ratio_high:
            return Decision(
                ActionName.THROTTLE_LOW_PRIORITY,
                "tenant overload ratio is high; throttle lower-priority tenants",
                desired_replicas=current,
                severity="warning",
                signals=signals,
            )

        if metrics.long_context_ratio >= th.long_context_ratio_high and metrics.ttft_p99 >= th.ttft_p99_high:
            return Decision(
                ActionName.ENABLE_LONG_CONTEXT_QUEUE,
                "long-context traffic is hurting TTFT; isolate or limit long-context requests",
                desired_replicas=current,
                severity="warning",
                signals=signals,
            )

        pressure_reasons = []
        if metrics.queue_time_p99 >= th.queue_time_p99_high:
            pressure_reasons.append("queue_time_p99")
        if metrics.ttft_p99 >= th.ttft_p99_high:
            pressure_reasons.append("ttft_p99")
        if metrics.tpot_p99 >= th.tpot_p99_high:
            pressure_reasons.append("tpot_p99")
        if metrics.e2e_latency_p99 >= th.e2e_latency_p99_high:
            pressure_reasons.append("e2e_latency_p99")
        if metrics.waiting_requests >= th.waiting_requests_high:
            pressure_reasons.append("waiting_requests")
        if metrics.gpu_memory_ratio >= th.gpu_memory_ratio_high:
            pressure_reasons.append("gpu_memory_ratio")
        if metrics.error_rate >= th.error_rate_high or metrics.timeout_rate >= th.timeout_rate_high:
            pressure_reasons.append("errors_or_timeouts")

        if pressure_reasons:
            self.state.pressure_windows += 1
            self.state.relief_windows = 0
        else:
            self.state.relief_windows += 1
            self.state.pressure_windows = 0

        if self.state.pressure_windows >= self.config.hysteresis_windows:
            if current >= self.config.max_replicas:
                return Decision(
                    ActionName.WARN_P99_VIOLATION,
                    f"pressure remains high but replicas already at max: {','.join(pressure_reasons)}",
                    desired_replicas=current,
                    severity="warning",
                    signals=signals,
                )
            if ts - self.state.last_scale_out_ts < self.config.cooldown_seconds:
                return Decision(
                    ActionName.WARN_HPA_LAG,
                    "scale-out pressure detected but cooldown is active",
                    desired_replicas=current,
                    severity="info",
                    signals=signals,
                )
            desired = min(self.config.max_replicas, current + self.config.scale_step)
            self.state.last_scale_out_ts = ts
            self.state.last_action = ActionName.SCALE_OUT
            return Decision(
                ActionName.SCALE_OUT,
                f"SLO pressure detected: {','.join(pressure_reasons)}",
                desired_replicas=desired,
                severity="warning",
                signals=signals,
            )

        if self._can_scale_in(metrics, ts, current):
            desired = max(self.config.min_replicas, current - self.config.scale_step)
            self.state.last_scale_in_ts = ts
            self.state.last_action = ActionName.SCALE_IN
            return Decision(
                ActionName.SCALE_IN,
                "sustained low pressure and low GPU utilization",
                desired_replicas=desired,
                severity="info",
                signals=signals,
            )

        if metrics.gpu_memory_ratio >= th.gpu_memory_ratio_high:
            return Decision(
                ActionName.WARN_GPU_MEMORY_PRESSURE,
                "GPU memory pressure is high but not critical",
                desired_replicas=current,
                severity="warning",
                signals=signals,
            )

        return Decision(ActionName.NOOP, "metrics within policy band", desired_replicas=current, signals=signals)

    def _can_scale_in(self, metrics: ControllerMetrics, now: float, current: int) -> bool:
        th = self.config.thresholds
        if current <= self.config.min_replicas:
            return False
        if self.state.relief_windows < self.config.hysteresis_windows:
            return False
        if now - self.state.last_scale_in_ts < self.config.scale_in_cooldown_seconds:
            return False
        if now - self.state.last_scale_out_ts < self.config.scale_in_cooldown_seconds:
            return False
        return (
            metrics.waiting_requests <= max(1.0, th.waiting_requests_high * 0.25)
            and metrics.queue_time_p99 <= th.queue_time_p99_high * 0.5
            and metrics.ttft_p99 <= th.ttft_p99_high * 0.5
            and metrics.gpu_utilization <= th.gpu_utilization_low
            and metrics.gpu_memory_ratio <= th.gpu_memory_ratio_high * 0.75
        )

