# 架构说明

LLM-Elastic-Governor 分成三条路径：真实推理路径、控制器路径、模拟器路径。

## 真实推理路径

```text
loadgen -> OpenAI-compatible API -> vLLM -> GPU
```

真实路径关注请求级指标：

- TTFT：Time To First Token，主要受 prefill、排队和 cache 命中影响。
- TPOT：Time Per Output Token，主要反映 decode 阶段速度。
- p95/p99 latency：尾延迟，在线服务 SLO 的核心。
- prompt/generation tokens per second：比 QPS 更贴近 LLM 成本。
- error/timeout rate：过载、OOM、客户端超时的结果信号。

## 控制器路径

```text
Prometheus/vLLM/DCGM metrics -> SLOPolicy -> dry-run log or Kubernetes Deployment patch
```

控制器不直接替代 vLLM scheduler，它站在平台层做治理：

- 扩容：queue、TTFT、TPOT、p99、waiting requests 持续升高时触发。
- 限流：租户过载或显存临界时保护系统。
- 隔离：长上下文比例过高时建议 long-context queue。
- 防抖：window、cooldown、hysteresis 避免频繁扩缩容。

## 模拟器路径

单卡环境无法真实验证多副本、多 GPU、多租户队列，因此仓库提供模拟器：

- `multi_replica.py`：扩容冷启动、负载均衡、cache cold-start。
- `prefix_cache.py`：prefix-aware routing 的收益和负载不均代价。
- `topology_scheduler.py`：GPU memory、NUMA、same-node placement。
- `queue_scheduler.py`：Kueue/Volcano 风格 quota、borrowing、preemption、gang。
- `tenant_quota.py`：request-level quota 和 token-level quota 对比。

## 边界

真实实现和模拟实现必须在文档、简历、面试里分清：

- 真实：单机单 GPU vLLM、loadgen、GPU 指标、参数实验。
- 半真实：K8s Deployment、Prometheus/Grafana、controller patch。
- 模拟：多副本、多 GPU 拓扑、队列调度、多租户 token quota。

