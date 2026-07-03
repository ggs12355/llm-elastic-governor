from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()
    for path in sorted(Path(args.results_dir).glob("**/summary.json")):
        print(f"\n== {path} ==")
        print(json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2, ensure_ascii=False))
    for path in sorted(Path(args.results_dir).glob("**/*summary.yaml")):
        print(f"\n== {path} ==")
        print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

