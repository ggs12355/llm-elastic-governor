# 实验设计

## 实验一：QPS 不能代表真实推理负载

对比：

- 短 prompt + 短 output
- 长 prompt + 短 output
- 短 prompt + 长 output
- 长 prompt + 长 output

观察：

- TTFT
- TPOT
- p99 latency
- GPU memory ratio
- prompt/generation tokens/s

结论模板：

> 在近似 QPS 下，长 prompt 明显抬高 TTFT，长 output 拉长 TPOT 和总 latency，说明 token-level 指标比 QPS 更接近 LLM 推理成本。

## 实验二：vLLM 参数调优

变量：

- `max_model_len`
- `max_num_seqs`
- `max_num_batched_tokens`
- `gpu_memory_utilization`

结论模板：

> 参数调大可能提高吞吐，但会带来更高 queue time、TTFT 或显存风险。服务参数需要按 SLO 和 workload 分布调优。

## 实验三：长短请求混部

配置：

```bash
bash experiments/run_long_context_mix.sh
```

结论模板：

> 少量长上下文请求会拖高短请求 p99，长上下文隔离或限并发可以保护短请求 SLO。

## 实验四：显存水位与准入控制

逐步提高并发、context length、output tokens。

对比：

- 不控制
- controller dry-run scale-out
- throttle low priority
- token-level quota

## 实验五：HPA-like baseline

对比：

- Static
- HPA/KEDA-like
- SLO-aware controller

重点不是证明 HPA 完全不可用，而是证明只看 CPU/GPU utilization 或 QPS 的策略会滞后或误判。

## 实验六到七：模拟器

```bash
make sim-replicas
make sim-prefix-cache
make sim-topology
make sim-queue
make sim-tenant-quota
```

所有模拟器输出到 `results/`，包含 summary 和部分图表。

