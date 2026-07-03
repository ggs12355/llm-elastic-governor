# 局限性与后续扩展

## 第一版局限

- 单卡环境无法真实验证多副本 GPU scale-out。
- 未修改 vLLM scheduler 或 KV cache allocator。
- Kueue/Volcano 为语义模拟，不是真实插件开发。
- topology-aware scheduling 为模拟，不是真实多节点调度器。
- controller 是平台层原型，不是生产级 autoscaler。
- loadgen 的 token 统计默认使用近似估计，严谨实验应接 tokenizer。

## 生产化需要补充

- controller leader election。
- CRD 化策略配置。
- 更完整的 PromQL discovery 和指标兼容层。
- 多租户认证、鉴权、计费、审计。
- AI Gateway / router。
- 灰度发布和回滚。
- 冷启动预测和 warm pool。
- 更精细的 prefix-aware routing。
- 和真实 Kueue/Volcano/KEDA 的集成。
- chaos test 和故障注入。

## 后续学习路线

1. vLLM scheduler 源码。
2. KV block manager / PagedAttention。
3. SGLang radix cache 对比。
4. TensorRT-LLM 部署和性能对比。
5. CUDA/Triton 小算子。
6. Nsight Systems / Nsight Compute。

