from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Workload:
    workload_id: int
    tenant: str
    gpus: int
    duration: int
    priority: int
    gang: bool
    submit_time: int


def generate_workloads(config: dict) -> list[Workload]:
    rnd = random.Random(config.get("seed", 19))
    tenants = list(config.get("quotas", {"team-a": 4, "team-b": 4}).keys())
    workloads = []
    for idx in range(config.get("workloads", 120)):
        tenant = rnd.choice(tenants)
        gang = rnd.random() < config.get("gang_ratio", 0.25)
        gpus = rnd.choice([2, 4]) if gang else 1
        workloads.append(
            Workload(
                workload_id=idx,
                tenant=tenant,
                gpus=gpus,
                duration=rnd.randint(20, 120),
                priority=rnd.choice([1, 2, 5, 10]),
                gang=gang,
                submit_time=rnd.randint(0, config.get("duration", 600)),
            )
        )
    return sorted(workloads, key=lambda w: w.submit_time)


def simulate(config: dict) -> dict:
    quotas = dict(config.get("quotas", {"team-a": 4, "team-b": 4}))
    total_gpus = config.get("total_gpus", sum(quotas.values()))
    workloads = generate_workloads(config)
    running: list[tuple[int, Workload]] = []
    usage = {tenant: 0 for tenant in quotas}
    admitted = 0
    pending = 0
    preempted = 0
    wait_times = []

    for workload in workloads:
        now = workload.submit_time
        still_running = []
        for finish, running_workload in running:
            if finish <= now:
                usage[running_workload.tenant] -= running_workload.gpus
            else:
                still_running.append((finish, running_workload))
        running = still_running

        free = total_gpus - sum(usage.values())
        tenant_free = quotas.get(workload.tenant, 0) - usage.get(workload.tenant, 0)
        can_borrow = config.get("borrowing", True) and free >= workload.gpus
        can_admit = tenant_free >= workload.gpus or can_borrow
        if not can_admit and config.get("preemption", True):
            victims = sorted(
                [rw for _, rw in running if rw.priority < workload.priority],
                key=lambda rw: rw.priority,
            )
            released = 0
            for victim in victims:
                usage[victim.tenant] -= victim.gpus
                released += victim.gpus
                preempted += 1
                running = [(finish, rw) for finish, rw in running if rw.workload_id != victim.workload_id]
                if released >= workload.gpus:
                    break
            free = total_gpus - sum(usage.values())
            can_admit = free >= workload.gpus
        if can_admit:
            usage[workload.tenant] = usage.get(workload.tenant, 0) + workload.gpus
            running.append((now + workload.duration, workload))
            admitted += 1
            wait_times.append(0)
        else:
            pending += 1
            wait_times.append(config.get("duration", 600) - now)

    fairness_denominator = sum(value * value for value in usage.values()) * len(usage)
    fairness = 0.0 if fairness_denominator == 0 else (sum(usage.values()) ** 2) / fairness_denominator
    return {
        "admitted": admitted,
        "pending": pending,
        "preempted": preempted,
        "fairness_index": fairness,
        "quota_usage": usage,
        "avg_wait_time": sum(wait_times) / max(1, len(wait_times)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate Kueue/Volcano-style queue semantics")
    parser.add_argument("--config", default="configs/simulation/queues.yaml")
    parser.add_argument("--output-dir", default="results/sim_queue")
    args = parser.parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = simulate(config)
    (output / "summary.yaml").write_text(yaml.safe_dump(summary, sort_keys=False), encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

