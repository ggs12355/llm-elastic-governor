from __future__ import annotations

import argparse
import csv
import heapq
import random
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from common.plotting import plot_series
from common.statistics import summarize


@dataclass(order=True)
class SimRequest:
    arrival_time: float
    request_id: int
    prompt_tokens: int = field(compare=False)
    output_tokens: int = field(compare=False)
    tenant_id: str = field(compare=False)
    prefix_id: str = field(compare=False)


@dataclass
class Replica:
    replica_id: int
    ready_at: float = 0.0
    available_at: float = 0.0
    gpu_memory_capacity: float = 1.0
    cache: set[str] = field(default_factory=set)

    def load(self, now: float) -> float:
        return max(0.0, self.available_at - now)


def generate_requests(config: dict) -> list[SimRequest]:
    rnd = random.Random(config.get("seed", 7))
    duration = config.get("duration_seconds", 300)
    rate = config.get("request_rate", 3.0)
    long_ratio = config.get("long_context_ratio", 0.1)
    requests: list[SimRequest] = []
    t = 0.0
    idx = 0
    while t < duration:
        t += rnd.expovariate(rate)
        is_long = rnd.random() < long_ratio
        prompt = rnd.randint(64, 256) if not is_long else rnd.randint(2048, 8192)
        output = rnd.randint(64, 256)
        requests.append(
            SimRequest(
                arrival_time=t,
                request_id=idx,
                prompt_tokens=prompt,
                output_tokens=output,
                tenant_id=f"tenant-{rnd.randint(1, 4)}",
                prefix_id=f"prefix-{rnd.randint(1, config.get('prefix_cardinality', 20))}",
            )
        )
        idx += 1
    return requests


def service_time(req: SimRequest, cache_hit: bool) -> float:
    prefill = req.prompt_tokens * (0.00018 if cache_hit else 0.00055)
    decode = req.output_tokens * 0.012
    return prefill + decode


def choose_replica(replicas: list[Replica], req: SimRequest, now: float, policy: str) -> Replica:
    ready = [rep for rep in replicas if rep.ready_at <= now]
    if not ready:
        return min(replicas, key=lambda rep: rep.ready_at)
    if policy == "round-robin":
        return ready[req.request_id % len(ready)]
    if policy == "least-queue":
        return min(ready, key=lambda rep: rep.available_at)
    if policy == "prefix-aware":
        hits = [rep for rep in ready if req.prefix_id in rep.cache]
        if hits:
            return min(hits, key=lambda rep: rep.available_at)
        return min(ready, key=lambda rep: rep.available_at)
    if policy == "prefix-aware-balanced":
        least_loaded = min(ready, key=lambda rep: rep.available_at)
        hits = [rep for rep in ready if req.prefix_id in rep.cache]
        if hits:
            best_hit = min(hits, key=lambda rep: rep.available_at)
            if best_hit.available_at <= least_loaded.available_at + 5.0:
                return best_hit
        return least_loaded
    if policy == "tenant-sticky":
        return ready[hash(req.tenant_id) % len(ready)]
    return min(ready, key=lambda rep: rep.available_at)


def simulate(config: dict, policy: str) -> dict:
    requests = generate_requests(config)
    replicas = [
        Replica(replica_id=idx)
        for idx in range(config.get("initial_replicas", 1))
    ]
    max_replicas = config.get("max_replicas", 4)
    cold_start = config.get("cold_start_seconds", 90)
    queue_threshold = config.get("scale_queue_threshold", 20)
    events: list[dict] = []
    actions: list[tuple[float, int]] = []
    cache_hits = 0

    for req in requests:
        now = req.arrival_time
        projected_queue_time = min(max(0.0, rep.available_at - now) for rep in replicas)
        if projected_queue_time >= queue_threshold and len(replicas) < max_replicas:
            new = Replica(replica_id=len(replicas), ready_at=now + cold_start, available_at=now + cold_start)
            replicas.append(new)
            actions.append((now, len(replicas)))
        rep = choose_replica(replicas, req, now, policy)
        start = max(now, rep.available_at, rep.ready_at)
        hit = req.prefix_id in rep.cache
        cache_hits += int(hit)
        duration = service_time(req, hit)
        finish = start + duration
        queue_time = start - now
        rep.available_at = finish
        rep.cache.add(req.prefix_id)
        events.append(
            {
                "request_id": req.request_id,
                "arrival_time": now,
                "replica_id": rep.replica_id,
                "queue_time": queue_time,
                "latency": finish - now,
                "service_time": duration,
                "cache_hit": hit,
                "replicas": len(replicas),
            }
        )

    latencies = [e["latency"] for e in events]
    queue_times = [e["queue_time"] for e in events]
    return {
        "policy": policy,
        "events": events,
        "actions": actions,
        "summary": {
            "requests": len(events),
            "replicas_final": len(replicas),
            "cache_hit_ratio": cache_hits / max(1, len(events)),
            "latency": summarize(latencies),
            "queue_time": summarize(queue_times),
        },
    }


def write_result(result: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    events = result["events"]
    with (output_dir / f"{result['policy']}_events.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(events[0].keys()) if events else ["request_id"])
        writer.writeheader()
        writer.writerows(events)
    (output_dir / f"{result['policy']}_summary.yaml").write_text(
        yaml.safe_dump(result["summary"], sort_keys=False), encoding="utf-8"
    )
    plot_series(
        {
            "latency": [e["latency"] for e in events],
            "queue_time": [e["queue_time"] for e in events],
            "replicas": [e["replicas"] for e in events],
        },
        output_dir / f"{result['policy']}_timeseries.png",
        f"multi-replica simulation: {result['policy']}",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate multi-replica vLLM scale-out")
    parser.add_argument("--config", default="configs/simulation/replicas.yaml")
    parser.add_argument("--output-dir", default="results/sim_replicas")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    policies = config.get("policies", ["round-robin", "least-queue", "prefix-aware"])
    for policy in policies:
        result = simulate(config, policy)
        write_result(result, Path(args.output_dir))
        print(policy, result["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
