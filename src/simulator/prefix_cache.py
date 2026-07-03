from __future__ import annotations

import argparse
import csv
import random
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from common.statistics import summarize


@dataclass
class PrefixReplica:
    replica_id: int
    available_at: float = 0.0
    cache_capacity: int = 64
    cache: OrderedDict[str, None] = field(default_factory=OrderedDict)

    def has(self, prefix: str) -> bool:
        return prefix in self.cache

    def touch(self, prefix: str) -> bool:
        hit = prefix in self.cache
        if hit:
            self.cache.move_to_end(prefix)
            return True
        self.cache[prefix] = None
        if len(self.cache) > self.cache_capacity:
            self.cache.popitem(last=False)
        return False


def choose(replicas: list[PrefixReplica], prefix: str, policy: str, index: int) -> PrefixReplica:
    if policy == "round-robin":
        return replicas[index % len(replicas)]
    if policy == "least-queue":
        return min(replicas, key=lambda rep: rep.available_at)
    if policy == "prefix-aware":
        hits = [rep for rep in replicas if rep.has(prefix)]
        if hits:
            return min(hits, key=lambda rep: rep.available_at)
        return min(replicas, key=lambda rep: rep.available_at)
    if policy == "prefix-aware-balanced":
        hits = [rep for rep in replicas if rep.has(prefix)]
        if hits and min(hits, key=lambda rep: rep.available_at).available_at <= min(replicas, key=lambda rep: rep.available_at).available_at + 2:
            return min(hits, key=lambda rep: rep.available_at)
        return min(replicas, key=lambda rep: rep.available_at)
    return random.choice(replicas)


def simulate(config: dict, policy: str) -> dict:
    rnd = random.Random(config.get("seed", 3))
    replicas = [
        PrefixReplica(idx, cache_capacity=config.get("cache_capacity", 64))
        for idx in range(config.get("replicas", 4))
    ]
    prefix_cardinality = config.get("prefix_cardinality", 50)
    hot_prefixes = config.get("hot_prefixes", 8)
    requests = config.get("requests", 1000)
    events: list[dict] = []
    hits = 0
    for idx in range(requests):
        now = idx / config.get("request_rate", 8.0)
        if rnd.random() < config.get("hot_prefix_ratio", 0.7):
            prefix = f"prefix-{rnd.randint(1, hot_prefixes)}"
        else:
            prefix = f"prefix-{rnd.randint(hot_prefixes + 1, prefix_cardinality)}"
        rep = choose(replicas, prefix, policy, idx)
        hit = rep.touch(prefix)
        hits += int(hit)
        ttft = (0.25 if hit else 1.2) + rnd.uniform(0.0, 0.1)
        start = max(now, rep.available_at)
        queue = start - now
        service = ttft + rnd.uniform(0.2, 0.6)
        rep.available_at = start + service
        events.append(
            {
                "request_id": idx,
                "prefix": prefix,
                "replica_id": rep.replica_id,
                "cache_hit": hit,
                "ttft": ttft + queue,
                "queue_time": queue,
            }
        )
    load_by_replica = {rep.replica_id: 0 for rep in replicas}
    for event in events:
        load_by_replica[event["replica_id"]] += 1
    loads = list(load_by_replica.values())
    imbalance = max(loads) / max(1, min(loads))
    return {
        "policy": policy,
        "events": events,
        "summary": {
            "requests": requests,
            "hit_ratio": hits / requests,
            "ttft": summarize(e["ttft"] for e in events),
            "queue_time": summarize(e["queue_time"] for e in events),
            "load_by_replica": load_by_replica,
            "load_imbalance": imbalance,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate prefix cache locality routing")
    parser.add_argument("--config", default="configs/simulation/prefix_cache.yaml")
    parser.add_argument("--output-dir", default="results/sim_prefix_cache")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for policy in config.get("policies", ["round-robin", "least-queue", "prefix-aware", "prefix-aware-balanced"]):
        result = simulate(config, policy)
        events = result["events"]
        with (output / f"{policy}_events.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(events[0].keys()))
            writer.writeheader()
            writer.writerows(events)
        (output / f"{policy}_summary.yaml").write_text(
            yaml.safe_dump(result["summary"], sort_keys=False), encoding="utf-8"
        )
        print(policy, result["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

