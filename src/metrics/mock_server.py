from __future__ import annotations

import argparse
import json
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class MockPrometheusHandler(BaseHTTPRequestHandler):
    step = 0

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/v1/query":
            query = parse_qs(parsed.query).get("query", [""])[0]
            value = self.value_for(query)
            payload = {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [{"metric": {}, "value": [time.time(), str(value)]}],
                },
            }
            self._json(payload)
            return
        if parsed.path == "/api/v1/label/__name__/values":
            self._json(
                {
                    "status": "success",
                    "data": [
                        "vllm:num_requests_waiting",
                        "vllm:num_requests_running",
                        "vllm:time_to_first_token_seconds_bucket",
                        "DCGM_FI_DEV_GPU_UTIL",
                    ],
                }
            )
            return
        self.send_response(404)
        self.end_headers()

    def value_for(self, query: str) -> float:
        MockPrometheusHandler.step += 1
        pressure = MockPrometheusHandler.step > 8
        noise = random.uniform(-0.03, 0.03)
        if "queue" in query:
            return 2.7 + noise if pressure else 0.4 + noise
        if "first_token" in query:
            return 3.4 + noise if pressure else 1.1 + noise
        if "output_token" in query:
            return 0.30 if pressure else 0.08
        if "waiting" in query:
            return 14 if pressure else 2
        if "running" in query:
            return 16 if pressure else 5
        if "GPU_UTIL" in query:
            return 0.91 if pressure else 0.55
        if "FB_USED" in query:
            return 0.92 if pressure else 0.62
        if "prompt_tokens" in query:
            return 1200 if pressure else 500
        if "generation_tokens" in query:
            return 260 if pressure else 120
        return 0

    def _json(self, payload: dict) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny mock Prometheus server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9090)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), MockPrometheusHandler)
    print(f"mock prometheus listening on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

