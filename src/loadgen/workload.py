from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class WorkloadItem:
    tenant_id: str
    workload_type: str
    prompt: str
    max_tokens: int
    streaming: bool = True


@dataclass(slots=True)
class WorkloadProfile:
    name: str
    duration_seconds: int
    concurrency: int
    request_rate: float
    timeout_seconds: float
    seed: int
    tenants: list[str]
    prompt_templates: list[str]
    output_tokens: list[int]
    long_prompt_tokens: int = 2048
    long_context_ratio: float = 0.0
    burst_after_seconds: int | None = None
    burst_rate_multiplier: float = 1.0
    streaming: bool = True

    @classmethod
    def from_file(cls, path: str | Path) -> WorkloadProfile:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(**data)


class WorkloadGenerator:
    def __init__(self, profile: WorkloadProfile):
        self.profile = profile
        self.random = random.Random(profile.seed)

    def item(self, index: int) -> WorkloadItem:
        tenant = self.random.choice(self.profile.tenants)
        template = self.random.choice(self.profile.prompt_templates)
        max_tokens = self.random.choice(self.profile.output_tokens)
        is_long = self.random.random() < self.profile.long_context_ratio
        prompt = template.format(index=index, tenant_id=tenant)
        workload_type = self.profile.name
        if is_long:
            filler = " ".join(f"context-{index}-{i}" for i in range(self.profile.long_prompt_tokens))
            prompt = f"{prompt}\n\nLong context:\n{filler}"
            workload_type = f"{self.profile.name}:long"
        return WorkloadItem(
            tenant_id=tenant,
            workload_type=workload_type,
            prompt=prompt,
            max_tokens=max_tokens,
            streaming=self.profile.streaming,
        )

    def effective_rate(self, elapsed: float) -> float:
        if self.profile.burst_after_seconds is None:
            return self.profile.request_rate
        if elapsed >= self.profile.burst_after_seconds:
            return self.profile.request_rate * self.profile.burst_rate_multiplier
        return self.profile.request_rate


def estimate_prompt_tokens(prompt: str) -> int:
    # A cheap tokenizer-independent estimate; replace with model tokenizer for precise experiments.
    return max(1, int(len(prompt.split()) * 1.25))


def profile_to_dict(profile: WorkloadProfile) -> dict[str, Any]:
    return {field: getattr(profile, field) for field in profile.__dataclass_fields__}

