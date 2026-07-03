from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class SlidingWindow:
    seconds: float
    samples: deque[tuple[float, float]] = field(default_factory=deque)

    def add(self, value: float, timestamp: float | None = None) -> None:
        ts = time.time() if timestamp is None else timestamp
        self.samples.append((ts, value))
        self.prune(ts)

    def prune(self, now: float | None = None) -> None:
        ts = time.time() if now is None else now
        cutoff = ts - self.seconds
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()

    def values(self, now: float | None = None) -> list[float]:
        self.prune(now)
        return [value for _, value in self.samples]

    def latest(self, default: float = 0.0) -> float:
        return self.samples[-1][1] if self.samples else default

