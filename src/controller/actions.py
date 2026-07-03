from __future__ import annotations

import json
import time
from pathlib import Path

from common.types import Decision


class DecisionLogger:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, decision: Decision) -> None:
        record = {"ts": time.time(), **decision.as_dict()}
        line = json.dumps(record, ensure_ascii=False)
        print(line)
        if self.path:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

