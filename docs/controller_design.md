# Controller 设计

## 输入

`ControllerMetrics` 包含：

- queue time p95/p99
- TTFT p95/p99
- TPOT p95/p99
- e2e latency p99
- waiting/running requests
- GPU memory ratio
- GPU utilization
- prompt/generation tokens/s
- error/timeout rate
- current replicas
- long context ratio
- tenant overload ratio

## 输出动作

- `NOOP`
- `SCALE_OUT`
- `SCALE_IN`
- `THROTTLE_LOW_PRIORITY`
- `REJECT_LOW_PRIORITY`
- `ENABLE_LONG_CONTEXT_QUEUE`
- `WARN_GPU_MEMORY_PRESSURE`
- `WARN_P99_VIOLATION`
- `WARN_HPA_LAG`

## 策略顺序

1. 指标缺失：fail-safe no-op。
2. 显存临界：拒绝低优先级或长上下文请求。
3. 租户过载：低优先级限流。
4. 长上下文伤害 TTFT：启用长上下文队列。
5. SLO 压力持续：扩容。
6. 压力持续降低：缩容。
7. 普通显存压力：告警。

## 防抖机制

- `hysteresis_windows`：连续多个窗口满足条件才动作。
- `cooldown_seconds`：扩容后等待新副本启动和 warmup。
- `scale_in_cooldown_seconds`：缩容更保守，避免刚扩容又缩容。
- `min_replicas/max_replicas`：限制资源边界。

## Dry-run 与 Active

Dry-run：

```bash
python -m controller.main --metrics-source mock --mode dry-run --iterations 5
```

Active：

```bash
python -m controller.main --prometheus-url http://127.0.0.1:9090 --mode active
```

Active 模式会 patch Kubernetes Deployment scale。生产化还需要 leader election、审计日志、权限隔离、回滚策略和更完整的 CRD。

