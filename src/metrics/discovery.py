from __future__ import annotations

import argparse
import requests


def discover_metric_names(prometheus_url: str) -> list[str]:
    resp = requests.get(f"{prometheus_url.rstrip('/')}/api/v1/label/__name__/values", timeout=10)
    resp.raise_for_status()
    return sorted(resp.json().get("data", []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover Prometheus metric names")
    parser.add_argument("--prometheus-url", default="http://127.0.0.1:9090")
    parser.add_argument("--contains", default="")
    args = parser.parse_args(argv)
    names = discover_metric_names(args.prometheus_url)
    for name in names:
        if args.contains.lower() in name.lower():
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

