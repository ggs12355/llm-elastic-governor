# 模拟器设计

## Multi-replica

目标：模拟扩容冷启动、负载均衡和 queue pressure。

策略：

- round-robin
- least-queue
- tenant-sticky
- prefix-aware

观察：

- p99 latency
- queue time
- replicas over time
- cache hit ratio

## Prefix Cache

目标：模拟 replica-local prefix cache。

结论：

- round-robin 可能打散 cache。
- prefix-aware 提高命中率。
- prefix-aware 可能造成负载不均。
- prefix-aware-balanced 在 locality 和 load balance 之间折中。

## Topology Scheduler

目标：模拟多 GPU、多节点、多 NUMA 的放置策略。

结论：

- AI 任务不能只看 GPU 数量。
- 多卡任务要考虑 same-node/same-NUMA。
- 显存碎片会造成总资源够但任务调度不上。

## Queue Scheduler

目标：模拟 Kueue/Volcano 风格语义：

- quota
- borrowing
- preemption
- gang scheduling
- pending/admission

结论：

- Kueue 更偏 workload admission 和 quota。
- Volcano 更偏 batch scheduling、gang 和 queue。
- 训练和推理混部时准入策略不同。

## Tenant Quota

目标：对比 request-level quota 和 token-level quota。

结论：

- QPS 限流不能表达长上下文和长输出成本。
- token-level quota 更贴近实际 GPU 计算与 KV cache 压力。
- 高优租户需要保底和隔离。

