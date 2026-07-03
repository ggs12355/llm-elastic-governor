from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GpuSample:
    timestamp: float
    index: int
    name: str
    utilization_gpu: float
    memory_used_mb: float
    memory_total_mb: float
    temperature_c: float
    power_w: float

    @property
    def memory_ratio(self) -> float:
        return 0.0 if self.memory_total_mb == 0 else self.memory_used_mb / self.memory_total_mb

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "timestamp": self.timestamp,
            "index": self.index,
            "name": self.name,
            "utilization_gpu": self.utilization_gpu,
            "memory_used_mb": self.memory_used_mb,
            "memory_total_mb": self.memory_total_mb,
            "memory_ratio": self.memory_ratio,
            "temperature_c": self.temperature_c,
            "power_w": self.power_w,
        }


def parse_nvidia_smi_csv(text: str, timestamp: float) -> list[GpuSample]:
    samples: list[GpuSample] = []
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 7:
            continue
        samples.append(
            GpuSample(
                timestamp=timestamp,
                index=int(parts[0]),
                name=parts[1],
                utilization_gpu=float(parts[2]),
                memory_used_mb=float(parts[3]),
                memory_total_mb=float(parts[4]),
                temperature_c=float(parts[5]),
                power_w=float(parts[6]),
            )
        )
    return samples

