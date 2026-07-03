# 指标体系

## 请求级指标

- `TTFT = first_token_time - start_time`
- `TPOT = (end_time - first_token_time) / (output_tokens - 1)`
- `latency = end_time - start_time`
- `tokens/s = tokens / duration`
- `error_rate = failed_requests / total_requests`
- `timeout_rate = timeout_requests / total_requests`

## 为什么 QPS 不够

两个请求都算 1 QPS，但资源成本可能完全不同：

- 100 token 输入和 8000 token 输入的 prefill 成本不同。
- 32 token 输出和 2048 token 输出的 decode 时间不同。
- 长上下文会扩大 KV Cache，占用显存。
- 长短请求混部会拖高短请求 p99。

## vLLM 指标

不同 vLLM 版本的指标名可能变化，因此仓库提供 `metrics.discovery`：

```bash
python -m metrics.discovery --prometheus-url http://127.0.0.1:9090 --contains vllm
```

常见关注项：

- waiting/running requests
- time to first token
- time per output token
- request queue time
- prompt/generation throughput
- cache/preemption 相关指标

## GPU 指标

推荐 DCGM Exporter：

- GPU utilization
- framebuffer memory used/free
- power usage
- temperature
- SM/memory utilization

无 DCGM 时使用：

```bash
python -m metrics.gpu_collector
```

## 分析重点

不要只看平均值。真实推理平台更关心：

- p95/p99 是否违反 SLO。
- p99 上升是否和 queue time、TTFT、GPU memory 同步。
- GPU utilization 低但 p99 高时，是否存在长上下文、batching、慢客户端或队列问题。
- 显存水位高时，是否需要 admission control，而不是继续接请求。

