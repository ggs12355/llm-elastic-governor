from __future__ import annotations

import math
from collections.abc import Iterable


def percentile(values: Iterable[float], pct: float) -> float:
    data = sorted(float(v) for v in values if v is not None and not math.isnan(float(v)))
    if not data:
        return 0.0
    if len(data) == 1:
        return data[0]
    rank = (len(data) - 1) * pct / 100.0
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return data[int(rank)]
    weight = rank - low
    return data[low] * (1 - weight) + data[high] * weight


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return default if denominator == 0 else numerator / denominator


def summarize(values: Iterable[float]) -> dict[str, float]:
    data = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not data:
        return {"count": 0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    return {
        "count": len(data),
        "avg": sum(data) / len(data),
        "p50": percentile(data, 50),
        "p95": percentile(data, 95),
        "p99": percentile(data, 99),
        "max": max(data),
    }


def cdf_points(values: Iterable[float]) -> list[tuple[float, float]]:
    data = sorted(float(v) for v in values)
    if not data:
        return []
    n = len(data)
    return [(value, (idx + 1) / n) for idx, value in enumerate(data)]

