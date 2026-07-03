# 面试问答

## 这个项目解决什么问题？

它解决 LLM 在线推理平台在突发流量、长短请求混部、多租户过载和显存压力下的资源治理问题。核心不是部署模型，而是建立 token、queue、SLO、GPU memory 感知的观测、压测和控制链路。

## 为什么 QPS 不适合 LLM 推理？

因为 1 个短 prompt 短输出请求和 1 个长上下文长输出请求都算 1 QPS，但 prefill、decode、KV cache 和显存成本完全不同。LLM 推理需要看 prompt tokens/s、generation tokens/s、TTFT、TPOT、queue time 和 GPU memory。

## TTFT 和 TPOT 是什么？

TTFT 是请求发出到第一个 token 返回的时间，主要反映排队和 prefill。TPOT 是后续每个输出 token 的平均时间，主要反映 decode 阶段性能。

## 为什么普通 HPA-like 策略容易误判？

如果只看 CPU、GPU utilization 或 QPS，它看不到 token 分布、queue time、TTFT、TPOT、KV cache pressure 和冷启动延迟。Kubernetes HPA 可以接 custom metrics，但指标选择和控制逻辑仍需要 LLM-aware。

## 显存水位高为什么不能继续接请求？

长上下文和高并发会扩大 KV cache 占用。显存接近临界时继续接请求可能导致 preemption、recompute、OOM、timeout 和 p99 放大。此时需要 admission control、限流、隔离或扩容。

## 长短请求混部为什么会拖高短请求 p99？

长请求消耗更多 prefill 计算和 KV cache，占据 batch/scheduler 资源。短请求即使自身很轻，也会被排队和 batch 交互影响，导致尾延迟变差。

## prefix-aware routing 的 trade-off 是什么？

把相同 prefix 路由到同一副本能提高 cache hit，降低 TTFT。但如果热点 prefix 集中在少数副本，会造成负载不均。因此要在 cache locality 和 load balance 之间折中。

## Kueue 和 Volcano 的区别怎么讲？

Kueue 更偏 Kubernetes 原生的 workload admission、quota、borrowing 和 reclaim。Volcano 更偏 batch scheduler，强调 queue、priority、preemption、gang scheduling 和多任务协同调度。

## 项目哪些是真实实现？

真实实现是单机单 GPU vLLM、OpenAI-compatible loadgen、请求级指标、GPU 指标、参数调优。K8s controller patch 是半真实原型。多副本、多 GPU topology、Kueue/Volcano、多租户 token quota 是模拟器。

## 如果生产化还要补什么？

需要 AI Gateway、真实多租户认证鉴权、CRD、leader election、审计日志、灰度回滚、warm pool、真实 Prometheus 指标兼容、限流执行面、告警策略和多节点 GPU 调度集成。

