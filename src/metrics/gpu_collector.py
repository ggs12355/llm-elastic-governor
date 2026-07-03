from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from metrics.parser import parse_nvidia_smi_csv


QUERY = (
    "index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect GPU metrics via nvidia-smi")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--output", default="results/gpu_metrics.jsonl")
    return parser


def collect_once() -> list[dict]:
    ts = time.time()
    completed = subprocess.run(
        [
            "nvidia-smi",
            f"--query-gpu={QUERY}",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return [sample.as_dict() for sample in parse_nvidia_smi_csv(completed.stdout, ts)]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with output.open("a", encoding="utf-8") as fh:
        while time.time() - start < args.duration:
            try:
                for sample in collect_once():
                    fh.write(json.dumps(sample, ensure_ascii=False) + "\n")
                    print(sample)
            except Exception as exc:
                print(f"warning: nvidia-smi collection failed: {exc}")
            time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

