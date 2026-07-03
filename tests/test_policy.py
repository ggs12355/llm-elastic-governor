from common.types import ActionName, ControllerMetrics
from controller.config import ControllerConfig
from controller.policy import SLOPolicy


def test_policy_scales_out_after_hysteresis():
    config = ControllerConfig(hysteresis_windows=2, cooldown_seconds=0, max_replicas=3)
    policy = SLOPolicy(config)
    metrics = ControllerMetrics(
        queue_time_p99=3.0,
        ttft_p99=4.0,
        tpot_p99=0.3,
        e2e_latency_p99=25,
        waiting_requests=12,
        gpu_memory_ratio=0.91,
        gpu_utilization=0.9,
        current_replicas=1,
    )
    first = policy.decide(metrics, now=100)
    second = policy.decide(metrics, now=101)
    assert first.action == ActionName.WARN_GPU_MEMORY_PRESSURE
    assert second.action == ActionName.SCALE_OUT
    assert second.desired_replicas == 2


def test_policy_rejects_on_critical_memory():
    policy = SLOPolicy(ControllerConfig())
    decision = policy.decide(ControllerMetrics(gpu_memory_ratio=0.98, current_replicas=1))
    assert decision.action == ActionName.REJECT_LOW_PRIORITY


def test_policy_throttles_tenant_overload():
    policy = SLOPolicy(ControllerConfig())
    decision = policy.decide(ControllerMetrics(tenant_overload_ratio=0.5, current_replicas=1))
    assert decision.action == ActionName.THROTTLE_LOW_PRIORITY


def test_policy_missing_metrics_noop():
    policy = SLOPolicy(ControllerConfig())
    decision = policy.decide(ControllerMetrics(missing=["ttft_p99"], current_replicas=1))
    assert decision.action == ActionName.NOOP
    assert decision.severity == "warning"
