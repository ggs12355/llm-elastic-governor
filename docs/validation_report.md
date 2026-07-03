# 验证报告

验证日期：2026-07-03

本报告记录第一版项目书中各项验证的完成情况。结论分为真实 GPU 验证、半真实平台验证和模拟验证，避免把单卡学习项目包装成生产级多节点调度系统。

## 验证环境

- GPU 实例：Ubuntu 22.04.5 LTS，NVIDIA GeForce RTX 4090，24 GB 显存。
- NVIDIA Driver：570.169。
- Python：3.10.12。
- 关键依赖：vLLM 0.10.2，torch 2.8.0+cu128，transformers 4.55.2，tokenizers 0.21.4，xformers 0.0.32.post1，triton 3.4.0。
- 容器环境：该 GPU 实例未安装 Docker、podman、nerdctl 或 ctr，因此本次真实推理验证走 Python venv/pip 路径。

## 总体状态

| 项目书目标 | 状态 | 说明 |
| --- | --- | --- |
| `make test` / 单元测试 | 已完成 | GPU 实例上 `14 passed in 0.05s`。 |
| Controller dry-run | 已完成 | 覆盖 NOOP、GPU memory warning、SCALE_OUT、cooldown/HPA lag。 |
| 多副本、prefix cache、topology、queue、tenant quota 模拟器 | 已完成 | 5 个模拟器均输出 summary 和实验结果。 |
| 真实 vLLM + Qwen OpenAI-compatible API | 已完成 | Qwen2.5-0.5B-Instruct 和 Qwen2.5-1.5B-Instruct 均完成 smoke/loadgen。 |
| GPU 指标采集 | 已完成 | 采集 utilization、显存、温度、功耗，并和请求级指标对应分析。 |
| Kubernetes/Prometheus/Grafana | 配置级完成 | YAML、RBAC、Service、HPA/KEDA-like、Grafana dashboard 已提供，但本次未在真实 K8s 集群部署。 |

## 真实 GPU 验证

### 0.5B smoke

模型：`Qwen/Qwen2.5-0.5B-Instruct`

启动参数：

```bash
python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.80 \
  --enforce-eager
```

压测 profile：`configs/load_profiles/steady_short.yaml`

| 指标 | 结果 |
| --- | ---: |
| 请求数 | 120 |
| 成功数 | 120 |
| 错误率 | 0 |
| 测试时长 | 60.27 s |
| 请求速率 | 1.99 req/s |
| prompt tokens/s | 27.08 |
| generation tokens/s | 182.88 |
| latency p50 / p95 / p99 | 1.04 s / 1.42 s / 1.43 s |
| TTFT p50 / p95 / p99 | 25.34 ms / 30.24 ms / 31.20 ms |
| TPOT p50 / p95 / p99 | 10.71 ms / 11.88 ms / 12.87 ms |
| GPU utilization avg / max | 20.19% / 21% |
| GPU memory avg / max | 19831 MiB / 19831 MiB |
| GPU memory ratio | 80.73% |

说明：0.5B 权重很小，但 vLLM 会按 `gpu-memory-utilization` 预留 KV cache，因此显存水位接近 80%，这正好可以用来解释“显存占用不等于模型权重大小”。

### 1.5B smoke

模型：`Qwen/Qwen2.5-1.5B-Instruct`

稳定启动参数：

```bash
python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.60 \
  --max-num-seqs 16 \
  --enforce-eager
```

vLLM 日志要点：

- 权重加载：2.8871 GiB。
- 可用 KV cache：11.08 GiB。
- GPU KV cache size：414,880 tokens。
- 对 2,048 tokens/request 的理论最大并发提示：202.58x。

压测 profile：`configs/load_profiles/steady_short.yaml`

| 指标 | 结果 |
| --- | ---: |
| 请求数 | 120 |
| 成功数 | 120 |
| 错误率 | 0 |
| 测试时长 | 60.42 s |
| 请求速率 | 1.99 req/s |
| prompt tokens/s | 27.01 |
| generation tokens/s | 154.92 |
| latency p50 / p95 / p99 | 1.04 s / 1.77 s / 2.00 s |
| TTFT p50 / p95 / p99 | 33.26 ms / 50.39 ms / 56.61 ms |
| TPOT p50 / p95 / p99 | 13.69 ms / 18.53 ms / 24.09 ms |
| GPU utilization avg / max | 23.64% / 40% |
| GPU memory avg / max | 14983 MiB / 14983 MiB |
| GPU memory ratio | 61.00% |

说明：初始尝试使用更大的 `max-model-len=4096` 和更高显存比例时服务没有及时进入可用状态。降低 `max-model-len`、`gpu-memory-utilization`、`max-num-seqs` 后，1.5B 在单张 4090 上稳定通过验证。这说明 vLLM 参数不是越大越好，需要按 SLO、上下文长度和显存水位做折中。

## Controller dry-run 验证

mock 指标源在 5 个 reconcile 周期内触发了以下决策：

| 周期 | action | 原因 |
| --- | --- | --- |
| 1 | NOOP | 指标处于策略带内。 |
| 2 | NOOP | 指标仍处于策略带内。 |
| 3 | WARN_GPU_MEMORY_PRESSURE | GPU memory ratio 达到 0.91，但尚未满足扩容稳定窗口。 |
| 4 | SCALE_OUT | queue time、TTFT、TPOT、e2e latency、waiting requests、GPU memory 同时越过阈值，期望副本从 1 到 2。 |
| 5 | WARN_HPA_LAG | 扩容压力仍在，但 cooldown 生效，提示传统 HPA-like 策略的滞后风险。 |

这一段验证的是策略逻辑和 action 生成，不代表已经在真实 Kubernetes 集群里完成自动扩缩容闭环。

## 模拟器验证

### 多副本扩容与路由

代表性结果：

| 策略 | cache hit ratio | avg latency | p99 latency |
| --- | ---: | ---: | ---: |
| round-robin | 0.9047 | 323.26 | 905.33 |
| least-queue | 0.9047 | 259.55 | 651.99 |
| tenant-sticky | 0.9523 | 573.77 | 1202.37 |
| prefix-aware | 0.9762 | 1179.30 | 2316.18 |
| prefix-aware-balanced | 0.9309 | 254.91 | 651.99 |

结论：单纯追求 prefix cache 命中率会导致负载倾斜，p99 反而恶化。更合理的策略是 prefix-aware 与 queue/load balancing 结合。

### Prefix cache locality

| 策略 | hit ratio | avg TTFT | p99 TTFT | load imbalance |
| --- | ---: | ---: | ---: | ---: |
| round-robin | 0.8067 | 65.41 | 117.26 | 1.00 |
| least-queue | 0.8125 | 64.99 | 112.60 | 1.04 |
| prefix-aware | 0.9342 | 50.26 | 146.83 | 1.68 |
| prefix-aware-balanced | 0.9217 | 48.00 | 81.36 | 1.05 |

结论：prefix-aware-balanced 在保持较高缓存命中的同时控制负载倾斜，TTFT p99 最优。

### GPU topology-aware scheduling

| 策略 | admitted | success rate | avg topology cost | cross-node ratio |
| --- | ---: | ---: | ---: | ---: |
| binpack | 7 | 7.78% | 17.14 | 14.29% |
| spread | 7 | 7.78% | 17.14 | 14.29% |
| topology-aware | 7 | 7.78% | 2.86 | 0 |
| memory-aware | 7 | 7.78% | 17.14 | 14.29% |

结论：在容量成为瓶颈时，各策略 admitted 数相同，但 topology-aware 能显著降低跨节点/跨拓扑成本。这部分是模拟验证，不是真实多节点 Kubernetes scheduler 插件。

### Kueue/Volcano 风格队列

- admitted：96。
- pending：24。
- preempted：42。
- fairness index：0.9883。
- avg wait time：49.5。

结论：队列语义能表达 quota、preemption、fair sharing 等平台能力，但当前实现用于学习语义和策略，不替代真实 Kueue/Volcano 集成。

### 多租户 token quota

| 模式 | accepted | rejected | throttled |
| --- | ---: | ---: | ---: |
| request-level | 520 | 487 | 193 |
| token-level | 319 | 665 | 216 |

结论：request-level quota 更容易被长 prompt 或长 output 绕过成本约束；token-level quota 更保守，但更接近 LLM 推理成本和预算治理。

## 真实性与价值判断

真实痛点成立：

- LLM 服务不能只看 QPS，prompt/output tokens、TTFT、TPOT、KV cache 和显存水位都会改变真实成本。
- vLLM serving 参数直接影响吞吐、延迟、显存预留和稳定性。
- prefix cache、queue time、冷启动和多租户 quota 是 AI Infra 平台中真实存在的调度问题。
- HPA/KEDA 这类通用扩缩容机制如果只看 CPU/GPU utilization 或 QPS，容易对 token-level 负载变化反应滞后。

当前价值：

- 作为学习型仓库，已经覆盖真实推理、压测、GPU 观测、控制器策略、K8s 配置和复杂调度语义模拟。
- 作为简历项目，可以突出“我能把 AI Infra 问题拆成指标、策略、实验和工程边界”，而不是只写“部署过 vLLM”。

不能夸大的部分：

- 未完成真实多节点 GPU 集群上的 scheduler 插件。
- 未完成真实 Kueue/Volcano/KEDA 生产集成。
- 未修改 vLLM 内部 scheduler、KV block manager 或 PagedAttention。
- 未完成 7B 或更大模型在本实例上的系统对比实验。
- 未在真实 Kubernetes 集群里跑 Prometheus/Grafana/controller active patch 全链路。

## 后续最有价值的扩展

1. 在真实 K8s 集群中部署 vLLM、Prometheus、controller，并验证 active patch。
2. 增加长上下文、长输出、burst、多租户混部的真实 GPU profile。
3. 接入 tokenizer 做更精确的 token 统计。
4. 增加 vLLM `/metrics` 采集，替代部分 nvidia-smi fallback 指标。
5. 用 7B/AWQ/GPTQ 做显存和吞吐对比。
6. 对接 Kueue 或 Volcano，做真实队列对象和 quota 验证。
