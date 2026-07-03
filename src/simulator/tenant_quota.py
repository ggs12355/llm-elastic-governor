from __future__ import annotations

import argparse
import random
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class TenantRequest:
    request_id: int
    tenant: str
    arrival_time: float
    input_tokens: int
    output_tokens: int
    priority: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class RollingCounter:
    def __init__(self, window: float):
        self.window = window
        self.samples: deque[tuple[float, int]] = deque()

    def add(self, timestamp: float, value: int) -> None:
        self.samples.append((timestamp, value))
        self.prune(timestamp)

    def value(self, timestamp: float) -> int:
        self.prune(timestamp)
        return sum(value for _, value in self.samples)

    def prune(self, timestamp: float) -> None:
        cutoff = timestamp - self.window
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()


def generate_requests(config: dict) -> list[TenantRequest]:
    rnd = random.Random(config.get("seed", 23))
    tenants = list(config.get("tenants", {}).keys())
    requests = []
    t = 0.0
    for idx in range(config.get("requests", 1000)):
        t += rnd.expovariate(config.get("request_rate", 10))
        tenant = rnd.choice(tenants)
        long = rnd.random() < config.get("long_context_ratio", 0.2)
        output_heavy = rnd.random() < config.get("long_output_ratio", 0.2)
        requests.append(
            TenantRequest(
                request_id=idx,
                tenant=tenant,
                arrival_time=t,
                input_tokens=rnd.randint(128, 512) if not long else rnd.randint(4096, 12000),
                output_tokens=rnd.randint(64, 256) if not output_heavy else rnd.randint(1024, 2048),
                priority=config.get("tenants", {}).get(tenant, {}).get("priority", 1),
            )
        )
    return requests


def simulate(config: dict, mode: str) -> dict:
    counters: dict[str, RollingCounter] = defaultdict(lambda: RollingCounter(60))
    request_counters: dict[str, RollingCounter] = defaultdict(lambda: RollingCounter(60))
    accepted = 0
    rejected = 0
    throttled = 0
    usage = defaultdict(int)
    tenant_rejects = defaultdict(int)

    for req in generate_requests(config):
        tenant_cfg = config["tenants"][req.tenant]
        request_counters[req.tenant].prune(req.arrival_time)
        counters[req.tenant].prune(req.arrival_time)
        if mode == "request-level":
            over = request_counters[req.tenant].value(req.arrival_time) >= tenant_cfg.get("requests_per_minute", 60)
        else:
            over = counters[req.tenant].value(req.arrival_time) + req.total_tokens > tenant_cfg.get("tokens_per_minute", 60000)
        too_long = req.input_tokens > tenant_cfg.get("max_context_tokens", 8192)
        if too_long:
            rejected += 1
            tenant_rejects[req.tenant] += 1
            continue
        if over and req.priority <= config.get("low_priority_threshold", 1):
            throttled += 1
            tenant_rejects[req.tenant] += 1
            continue
        if over:
            rejected += 1
            tenant_rejects[req.tenant] += 1
            continue
        accepted += 1
        usage[req.tenant] += req.total_tokens
        counters[req.tenant].add(req.arrival_time, req.total_tokens)
        request_counters[req.tenant].add(req.arrival_time, 1)

    return {
        "mode": mode,
        "accepted": accepted,
        "rejected": rejected,
        "throttled": throttled,
        "token_usage": dict(usage),
        "tenant_rejects": dict(tenant_rejects),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate multi-tenant request/token quota")
    parser.add_argument("--config", default="configs/simulation/tenants.yaml")
    parser.add_argument("--output-dir", default="results/sim_tenant_quota")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [simulate(config, "request-level"), simulate(config, "token-level")]
    (output / "summary.yaml").write_text(yaml.safe_dump(rows, sort_keys=False), encoding="utf-8")
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

