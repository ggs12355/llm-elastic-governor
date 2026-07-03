# 简历表述

## 稳健版本

**基于 vLLM 与 Kubernetes 的 LLM 推理服务弹性调度与 GPU 资源治理系统**

- 基于 RTX 4090 云 GPU 部署 vLLM + Qwen 推理服务，构建 OpenAI-compatible API 压测链路，采集 TTFT、TPOT、tokens/s、p95/p99 latency、错误率、超时率与 GPU 显存水位等指标。
- 设计 steady-short、burst、long-context-mix、token-shift、多租户过载等 workload，分析 `max_model_len`、`max_num_seqs`、`max_num_batched_tokens`、`gpu_memory_utilization` 对吞吐、尾延迟和显存压力的影响。
- 实现 queue time、TTFT、TPOT、p99、waiting requests、GPU memory 感知的 SLO-aware controller，支持 dry-run、Kubernetes Deployment patch、cooldown、hysteresis 和 structured decision log。
- 构建多副本扩容、prefix cache locality、GPU topology、Kueue/Volcano 队列语义和多租户 token quota 模拟器，用于验证扩容冷启动、缓存局部性、拓扑放置、队列准入和租户隔离策略。

## 强调学习边界版本

**LLM-Elastic-Governor：面向 vLLM 推理服务的 SLO-aware 调度与 GPU 资源治理学习平台**

- 真实实现单卡 vLLM 推理压测和 GPU 观测链路，半真实实现 Kubernetes controller patch，模拟实现多副本、多 GPU、多租户队列治理场景。
- 通过 Static、HPA/KEDA-like 和自研 SLO-aware controller 对比，验证 LLM 推理扩缩容不能只依赖 QPS、CPU 或 GPU utilization，需要结合 token throughput、queue time、TTFT/TPOT 和 GPU memory pressure。

## 面试一句话

这个项目用真实 vLLM 单卡实验证明 LLM 推理负载不能用 QPS 简化，再用 controller 和模拟器把 queue、token、SLO、KV cache、显存、多租户 quota 和 GPU 调度这些 AI Infra 问题串成一个可运行、可观测、可复现实验的学习型系统。

