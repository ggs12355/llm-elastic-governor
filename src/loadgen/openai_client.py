from __future__ import annotations

import json
import time
from collections.abc import Iterator

import requests


class OpenAICompatibleClient:
    def __init__(self, base_url: str, model: str, timeout: float = 60.0, api_key: str = "EMPTY"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def chat_completion_stream(self, prompt: str, max_tokens: int) -> Iterator[tuple[float, str]]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "stream": True,
        }
        with requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self.headers,
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    continue
                content = (
                    payload.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content", "")
                )
                if content:
                    yield time.time(), content

    def chat_completion(self, prompt: str, max_tokens: int) -> tuple[float, str]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "stream": False,
        }
        resp = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        return time.time(), content

