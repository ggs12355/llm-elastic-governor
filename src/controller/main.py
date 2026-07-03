from __future__ import annotations

import argparse
import time

from controller.actions import DecisionLogger
from controller.config import ControllerConfig
from controller.k8s_client import KubernetesScaleClient
from controller.metrics_client import MockMetricsClient, PrometheusMetricsClient
from controller.policy import SLOPolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SLO-aware vLLM elastic controller")
    parser.add_argument("--config", default="configs/controller/policy_default.yaml")
    parser.add_argument("--prometheus-url", default="http://127.0.0.1:9090")
    parser.add_argument("--metrics-source", choices=["prometheus", "mock"], default="prometheus")
    parser.add_argument("--mock-scenario", choices=["burst", "memory", "tenant"], default="burst")
    parser.add_argument("--mode", choices=["dry-run", "active"], default=None)
    parser.add_argument("--iterations", type=int, default=0, help="0 means run forever")
    parser.add_argument("--decision-log", default="results/controller/decisions.jsonl")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = ControllerConfig.from_file(args.config)
    if args.mode:
        config.mode = args.mode

    policy = SLOPolicy(config)
    logger = DecisionLogger(args.decision_log)
    k8s = KubernetesScaleClient(config.namespace, config.deployment)
    current_replicas = config.min_replicas

    if args.metrics_source == "mock":
        metrics_client = MockMetricsClient(args.mock_scenario)
    else:
        metrics_client = PrometheusMetricsClient(args.prometheus_url, config)

    iteration = 0
    while True:
        if config.mode == "active":
            try:
                current_replicas = k8s.get_replicas()
            except Exception as exc:
                print(f"warning: failed to read deployment replicas, using cached value: {exc}")
        metrics = metrics_client.collect(current_replicas=current_replicas)
        decision = policy.decide(metrics)
        logger.write(decision)
        if config.mode == "active" and decision.desired_replicas is not None:
            if decision.desired_replicas != current_replicas and decision.action.value.startswith("SCALE"):
                k8s.patch_replicas(decision.desired_replicas)
                current_replicas = decision.desired_replicas
        elif decision.desired_replicas is not None:
            current_replicas = decision.desired_replicas

        iteration += 1
        if args.iterations and iteration >= args.iterations:
            return 0
        time.sleep(config.loop_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())

