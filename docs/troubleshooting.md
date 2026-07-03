# Troubleshooting

## vLLM 启动 OOM

处理顺序：

1. 降低 `max_model_len`。
2. 降低 `max_num_seqs`。
3. 降低 `max_num_batched_tokens`。
4. 调低或调高 `gpu_memory_utilization` 做对比。
5. 换 1.5B/0.5B 模型验证链路。
6. 尝试 AWQ/GPTQ 量化模型。

## `/v1/models` 不通

检查：

```bash
curl http://127.0.0.1:8000/v1/models
ss -lntp | grep 8000
```

Kubernetes：

```bash
kubectl get pods -n llm-serving
kubectl logs -n llm-serving deploy/vllm-qwen
kubectl port-forward -n llm-serving svc/vllm-qwen 8000:8000
```

## Prometheus 读不到 vLLM 指标

检查：

- vLLM `/metrics` 是否存在。
- Pod annotation 是否正确。
- Prometheus scrape config 是否加载。
- 指标名是否随版本变化。

发现指标：

```bash
python -m metrics.discovery --contains vllm
```

## Controller 一直 NOOP

可能原因：

- 指标缺失进入 fail-safe。
- 阈值过高。
- `hysteresis_windows` 还没满足。
- cooldown 生效。
- mock scenario 没有制造压力。

## GPU utilization 低但 p99 高

排查：

- queue time 是否高。
- TTFT 是否高，是否长 prompt 多。
- TPOT 是否高，是否长 output 多。
- 是否 streaming slow client。
- 是否显存压力或 KV cache preemption。
- batch 参数是否太保守或太激进。

