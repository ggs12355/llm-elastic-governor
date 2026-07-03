from __future__ import annotations

import argparse
import json
import queue
import threading
import time
import uuid
from pathlib import Path

from common.types import RequestMetrics
from loadgen.openai_client import OpenAICompatibleClient
from loadgen.workload import WorkloadGenerator, WorkloadProfile, estimate_prompt_tokens


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenAI-compatible LLM load generator")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--output", default="results/loadgen.jsonl")
    parser.add_argument("--api-key", default="EMPTY")
    return parser


class LoadRunner:
    def __init__(self, profile: WorkloadProfile, base_url: str, model: str, output: Path, api_key: str):
        self.profile = profile
        self.generator = WorkloadGenerator(profile)
        self.client = OpenAICompatibleClient(base_url, model, profile.timeout_seconds, api_key)
        self.output = output
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.jobs: queue.Queue[tuple[int, float]] = queue.Queue(maxsize=profile.concurrency * 4)
        self.stop = threading.Event()
        self.write_lock = threading.Lock()

    def run(self) -> None:
        workers = [
            threading.Thread(target=self._worker, name=f"loadgen-worker-{idx}", daemon=True)
            for idx in range(self.profile.concurrency)
        ]
        for worker in workers:
            worker.start()
        start = time.time()
        request_index = 0
        while time.time() - start < self.profile.duration_seconds:
            elapsed = time.time() - start
            rate = max(0.01, self.generator.effective_rate(elapsed))
            self.jobs.put((request_index, time.time()))
            request_index += 1
            time.sleep(1.0 / rate)
        self.stop.set()
        self.jobs.join()
        for worker in workers:
            worker.join(timeout=1)

    def _worker(self) -> None:
        while not self.stop.is_set() or not self.jobs.empty():
            try:
                index, _scheduled = self.jobs.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                metrics = self._send(index)
            except Exception as exc:
                now = time.time()
                item = self.generator.item(index)
                metrics = RequestMetrics(
                    request_id=str(uuid.uuid4()),
                    tenant_id=item.tenant_id,
                    workload_type=item.workload_type,
                    prompt_tokens=estimate_prompt_tokens(item.prompt),
                    output_tokens=0,
                    start_time=now,
                    first_token_time=None,
                    end_time=time.time(),
                    status_code=599,
                    error_reason=repr(exc),
                    streaming=item.streaming,
                )
            self._write(metrics)
            self.jobs.task_done()

    def _send(self, index: int) -> RequestMetrics:
        item = self.generator.item(index)
        request_id = str(uuid.uuid4())
        start = time.time()
        first_token_time = None
        content_chunks: list[str] = []
        if item.streaming:
            for ts, token in self.client.chat_completion_stream(item.prompt, item.max_tokens):
                if first_token_time is None:
                    first_token_time = ts
                content_chunks.append(token)
            end = time.time()
        else:
            end, content = self.client.chat_completion(item.prompt, item.max_tokens)
            content_chunks.append(content)
            first_token_time = end
        output_text = "".join(content_chunks)
        output_tokens = max(1, int(len(output_text.split()) * 1.25)) if output_text else 0
        return RequestMetrics(
            request_id=request_id,
            tenant_id=item.tenant_id,
            workload_type=item.workload_type,
            prompt_tokens=estimate_prompt_tokens(item.prompt),
            output_tokens=output_tokens,
            start_time=start,
            first_token_time=first_token_time,
            end_time=end,
            status_code=200,
            streaming=item.streaming,
        )

    def _write(self, metrics: RequestMetrics) -> None:
        with self.write_lock:
            with self.output.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(metrics.as_dict(), ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    profile = WorkloadProfile.from_file(args.profile)
    runner = LoadRunner(profile, args.base_url, args.model, Path(args.output), args.api_key)
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

