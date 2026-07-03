# 项目书

## 项目名称

**基于 vLLM 与 Kubernetes 的大模型推理服务弹性调度与 GPU 资源治理系统**

英文名：**SLO-Aware Elastic Scheduling and GPU Resource Governance for vLLM-based LLM Serving on Kubernetes**

简称：**LLM-Elastic-Governor**

## 项目定位

面向 AI Infra 云资源调度、AI Infra 推理平台、云原生平台开发和推理服务 SRE 岗位。项目目标不是“部署一个大模型”，而是围绕在线推理中的 queue time、TTFT、TPOT、p99 latency、KV Cache pressure、GPU memory pressure、多租户过载和扩容冷启动，构建一套可运行、可观测、可压测、可调度、可模拟扩展的学习型仓库。

## 实现边界

真实实现：

- RTX 4090 或同类云 GPU 上运行 vLLM。
- Qwen 系列模型 OpenAI-compatible API。
- 自研 loadgen 采集请求级指标。
- GPU 指标采集和 vLLM 参数实验。

半真实实现：

- Kubernetes Deployment/Service/RBAC。
- Prometheus/Grafana 配置。
- Controller dry-run 和 Deployment patch。
- Static/HPA/KEDA-like baseline。

模拟实现：

- 多副本 scale-out 和 cold-start。
- prefix cache locality。
- GPU topology-aware scheduling。
- Kueue/Volcano 队列语义。
- 多租户 token-level quota。

## 核心问题

传统 Web 服务可以粗略使用 QPS、CPU、内存描述负载，但 LLM 推理更依赖 token、上下文长度、prefill/decode、KV Cache 和 GPU 显存。相同 QPS 下，长 prompt、长 output、长上下文、多租户突发会导致完全不同的 TTFT、TPOT、p99 和显存压力。

## 学习目标

- vLLM serving、OpenAI-compatible API。
- prefill/decode、KV Cache、PagedAttention、continuous batching、prefix cache。
- TTFT、TPOT、tokens/s、p99、queue time。
- Kubernetes GPU 调度、NVIDIA device plugin、DCGM Exporter。
- Prometheus/Grafana、controller reconcile、Deployment patch。
- HPA/KEDA 的边界和 LLM-aware autoscaling。
- 多副本路由、prefix-aware routing、多租户 token quota。
- GPU topology、Kueue、Volcano、gang scheduling、quota borrowing、preemption。

## 第一版成功标准

- `make test` 通过。
- `make mock-controller` 可以看到 dry-run 决策。
- `make sim-replicas`、`make sim-prefix-cache`、`make sim-topology`、`make sim-queue`、`make sim-tenant-quota` 可以输出结果。
- GPU 机器上能启动 vLLM 并运行 `scripts/run_gpu_smoke.sh`。
- docs 中包含架构、部署、指标、controller、实验、模拟器、排错、局限、面试和简历材料。

