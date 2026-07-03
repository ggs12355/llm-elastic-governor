from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()
    result_dir = Path(args.results_dir)
    images = sorted(result_dir.glob("**/*.png"))
    print(f"found {len(images)} generated plot(s)")
    for image in images:
        print(image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

