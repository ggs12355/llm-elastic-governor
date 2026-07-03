from __future__ import annotations

import argparse
import json
from pathlib import Path

from common.plotting import plot_series
from common.statistics import cdf_points, safe_div, summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze loadgen JSONL output")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="results/analysis")
    return parser


def load_records(path: str | Path) -> list[dict]:
    records = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    return records


def analyze(records: list[dict]) -> dict:
    ok = [r for r in records if r.get("status_code") == 200]
    latencies = [r["latency"] for r in ok if r.get("latency") is not None]
    ttft = [r["ttft"] for r in ok if r.get("ttft") is not None]
    tpot = [r["tpot"] for r in ok if r.get("tpot") is not None]
    prompt_tokens = sum(r.get("prompt_tokens") or 0 for r in ok)
    output_tokens = sum(r.get("output_tokens") or 0 for r in ok)
    if records:
        start = min(r["start_time"] for r in records)
        end = max(r["end_time"] for r in records)
    else:
        start = end = 0
    duration = max(0.001, end - start)
    return {
        "requests": len(records),
        "success": len(ok),
        "errors": len(records) - len(ok),
        "error_rate": safe_div(len(records) - len(ok), len(records)),
        "duration_seconds": duration,
        "request_rate": len(records) / duration,
        "prompt_tokens_per_sec": prompt_tokens / duration,
        "generation_tokens_per_sec": output_tokens / duration,
        "latency": summarize(latencies),
        "ttft": summarize(ttft),
        "tpot": summarize(tpot),
    }


def write_outputs(records: list[dict], summary: dict, output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    for name in ["latency", "ttft", "tpot"]:
        values = [r.get(name) for r in records if r.get(name) is not None and r.get("status_code") == 200]
        with (out / f"{name}_cdf.csv").open("w", encoding="utf-8") as fh:
            fh.write("value,cdf\n")
            for value, cdf in cdf_points(values):
                fh.write(f"{value},{cdf}\n")

    sorted_records = sorted(records, key=lambda r: r["start_time"])
    plot_series(
        {
            "latency": [r.get("latency") or 0 for r in sorted_records],
            "ttft": [r.get("ttft") or 0 for r in sorted_records],
        },
        out / "latency_ttft.png",
        "Request latency and TTFT over time",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    records = load_records(args.input)
    summary = analyze(records)
    write_outputs(records, summary, args.output_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

