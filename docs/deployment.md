# 部署指南

## 1. GPU 机器准备

推荐 Ubuntu 22.04、NVIDIA Driver、CUDA runtime、Docker、NVIDIA Container Toolkit。

检查 GPU：

```bash
nvidia-smi
```

安装 Python 依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## 2. 启动 vLLM

小模型验证：

```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --enable-prefix-caching
```

验证 API：

```bash
curl http://127.0.0.1:8000/v1/models
```

## 3. 跑压测

```bash
python -m loadgen.runner \
  --profile configs/load_profiles/steady_short.yaml \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --output results/steady_short.jsonl

python -m loadgen.analyze \
  --input results/steady_short.jsonl \
  --output-dir results/steady_short_analysis
```

## 4. 采集 GPU 指标

没有 Prometheus 时先用 fallback：

```bash
python -m metrics.gpu_collector --interval 2 --duration 120 --output results/gpu_metrics.jsonl
```

有 Prometheus + DCGM Exporter 时，controller 直接读取 PromQL。

## 5. Kubernetes 原型

单 GPU 环境优先验证单副本真实推理和 mock patch：

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/vllm-deployment.yaml
kubectl apply -f deploy/k8s/vllm-service.yaml
kubectl get pods -n llm-serving
kubectl port-forward -n llm-serving svc/vllm-qwen 8000:8000
```

Controller dry-run：

```bash
python -m controller.main \
  --config configs/controller/policy_default.yaml \
  --metrics-source mock \
  --mode dry-run \
  --iterations 5
```

Active patch 需要 kubeconfig 或 in-cluster RBAC：

```bash
python -m controller.main \
  --config configs/controller/policy_default.yaml \
  --prometheus-url http://127.0.0.1:9090 \
  --mode active
```

