from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class GPU:
    node: str
    gpu_id: int
    memory_total: int
    memory_free: int
    numa: int
    allocated: bool = False


@dataclass
class Job:
    job_id: int
    gpus: int
    memory_per_gpu: int
    kind: str


def build_cluster(config: dict) -> list[GPU]:
    gpus = []
    for node_idx in range(config.get("nodes", 2)):
        for gpu_idx in range(config.get("gpus_per_node", 4)):
            gpus.append(
                GPU(
                    node=f"node-{node_idx}",
                    gpu_id=gpu_idx,
                    memory_total=config.get("gpu_memory_gb", 24),
                    memory_free=config.get("gpu_memory_gb", 24),
                    numa=gpu_idx // max(1, config.get("gpus_per_numa", 2)),
                )
            )
    return gpus


def generate_jobs(config: dict) -> list[Job]:
    rnd = random.Random(config.get("seed", 11))
    jobs = []
    for idx in range(config.get("jobs", 80)):
        kind = rnd.choices(
            ["single-replica", "tensor-parallel", "long-context", "batch"],
            weights=[0.45, 0.25, 0.2, 0.1],
        )[0]
        if kind == "tensor-parallel":
            gpus, mem = rnd.choice([2, 4]), rnd.randint(10, 18)
        elif kind == "long-context":
            gpus, mem = 1, rnd.randint(18, 24)
        else:
            gpus, mem = 1, rnd.randint(6, 16)
        jobs.append(Job(idx, gpus, mem, kind))
    return jobs


def topology_cost(selected: list[GPU]) -> int:
    nodes = {gpu.node for gpu in selected}
    numas = {(gpu.node, gpu.numa) for gpu in selected}
    if len(nodes) > 1:
        return 100
    if len(numas) > 1:
        return 20
    return 0


def schedule_job(gpus: list[GPU], job: Job, policy: str) -> list[GPU] | None:
    candidates = [gpu for gpu in gpus if not gpu.allocated and gpu.memory_free >= job.memory_per_gpu]
    if len(candidates) < job.gpus:
        return None
    if policy == "spread":
        selected = sorted(candidates, key=lambda gpu: (gpu.node, gpu.gpu_id))[: job.gpus]
    elif policy == "binpack":
        selected = sorted(candidates, key=lambda gpu: (gpu.node, gpu.numa, gpu.gpu_id))[: job.gpus]
    elif policy == "topology-aware":
        best = None
        best_cost = 10**9
        for node in {gpu.node for gpu in candidates}:
            node_gpus = [gpu for gpu in candidates if gpu.node == node]
            for numa in {gpu.numa for gpu in node_gpus}:
                group = [gpu for gpu in node_gpus if gpu.numa == numa]
                if len(group) >= job.gpus:
                    cost = topology_cost(group[: job.gpus])
                    if cost < best_cost:
                        best = group[: job.gpus]
                        best_cost = cost
        selected = best or candidates[: job.gpus]
    elif policy == "memory-aware":
        selected = sorted(candidates, key=lambda gpu: gpu.memory_free, reverse=True)[: job.gpus]
    else:
        selected = candidates[: job.gpus]
    if len(selected) < job.gpus:
        return None
    for gpu in selected:
        gpu.allocated = True
        gpu.memory_free -= job.memory_per_gpu
    return selected


def simulate(config: dict, policy: str) -> dict:
    cluster = build_cluster(config)
    jobs = generate_jobs(config)
    admitted = 0
    unschedulable = 0
    costs = []
    cross_node = 0
    for job in jobs:
        selected = schedule_job(cluster, job, policy)
        if not selected:
            unschedulable += 1
            continue
        admitted += 1
        costs.append(topology_cost(selected))
        cross_node += int(len({gpu.node for gpu in selected}) > 1)
    fragmentation = sum(gpu.memory_free for gpu in cluster if not gpu.allocated) / max(1, sum(gpu.memory_total for gpu in cluster))
    return {
        "policy": policy,
        "admitted": admitted,
        "unschedulable": unschedulable,
        "success_rate": admitted / max(1, len(jobs)),
        "avg_topology_cost": sum(costs) / max(1, len(costs)),
        "cross_node_ratio": cross_node / max(1, admitted),
        "memory_fragmentation": fragmentation,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate GPU topology-aware scheduling")
    parser.add_argument("--config", default="configs/simulation/topology.yaml")
    parser.add_argument("--output-dir", default="results/sim_topology")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [simulate(config, policy) for policy in config.get("policies", ["binpack", "spread", "topology-aware", "memory-aware"])]
    (output / "summary.yaml").write_text(yaml.safe_dump(rows, sort_keys=False), encoding="utf-8")
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

