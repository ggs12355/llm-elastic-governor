# LLM-Elastic-Governor

基于 vLLM 与 Kubernetes 的大模型推理服务弹性调度与 GPU 资源治理学习型仓库。

这个项目不是只部署一个模型服务，而是围绕 LLM 在线推理里的真实工程矛盾做一条完整学习链路：

- 用 vLLM + Qwen 跑真实 OpenAI-compatible API 推理。
- 用自研 loadgen 采集 TTFT、TPOT、tokens/s、p95/p99 latency、错误率和超时率。
- 采集 GPU utilization、显存水位、功耗、温度等指标。
- 实现 queue、token、SLO、GPU memory 感知的弹性控制器，支持 dry-run 和 Kubernetes Deployment patch。
- 用模拟器补足单卡环境难以真实验证的多副本扩容、prefix cache locality、GPU topology、Kueue/Volcano 队列语义、多租户 token quota。

## 快速开始

本地核心逻辑不需要 GPU：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make test
make mock-controller
make sim-replicas
make sim-prefix-cache
make sim-tenant-quota
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
python -m controller.main --config configs/controller/policy_default.yaml --metrics-source mock --mode dry-run --iterations 5
```

## 真实 GPU 路径

推荐先在 GPU 云实例上跑 vLLM，再接 Kubernetes。单张 24 GB 4090 上，1.5B 模型可以先用保守参数稳定跑通链路：

```bash
pip install "vllm==0.10.2"
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.60 \
  --max-num-seqs 16 \
  --enforce-eager
```

验证：

```bash
curl http://127.0.0.1:8000/v1/models
python -m loadgen.runner \
  --profile configs/load_profiles/steady_short.yaml \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --output results/steady_short.jsonl
python -m loadgen.analyze --input results/steady_short.jsonl --output-dir results/analysis
```

## 验证快照

2026-07-03 在 RTX 4090 24 GB 云 GPU 上完成了第一版验证：

- 单元测试：`14 passed`。
- Controller dry-run：覆盖 NOOP、显存压力告警、SCALE_OUT、cooldown/HPA lag。
- 模拟器：多副本、prefix cache、topology、queue、tenant quota 全部跑通。
- 真实 vLLM：Qwen2.5-0.5B-Instruct 和 Qwen2.5-1.5B-Instruct 均完成 OpenAI-compatible API smoke/loadgen。
- 1.5B steady_short：120/120 成功，错误率 0，约 1.99 req/s，generation 154.92 tokens/s，latency p99 约 2.00 s，TTFT p99 约 56.61 ms。

完整结果见 [docs/validation_report.md](docs/validation_report.md)。

## 仓库结构

```text
configs/        模型、控制器、压测、模拟器配置
deploy/k8s/     Kubernetes Deployment/Service/RBAC/HPA/KEDA/Grafana 配置
docker/         controller/loadgen/vLLM 镜像示例
docs/           架构、部署、指标、实验、面试、简历材料
experiments/    可复现实验脚本
src/            controller、loadgen、metrics、simulator、common 代码
tests/          单元测试
results/        实验输出目录，默认不提交结果文件
```

## 推荐学习顺序

1. `docs/architecture.md`：理解系统边界和模块关系。
2. `docs/metrics.md`：掌握 TTFT、TPOT、KV Cache、queue time、GPU memory pressure。
3. `src/loadgen`：看请求级指标如何采集。
4. `src/controller/policy.py`：看 SLO-aware 决策如何写成可测试策略。
5. `src/simulator`：用模拟器观察多副本、缓存、拓扑、队列和 quota trade-off。
6. `docs/experiments.md`：按实验报告模板跑真实数据。
7. `docs/interview_notes.md`：准备面试深挖问题。

## 项目边界

真实实现：

- 单机单 GPU vLLM 推理。
- 请求级压测指标。
- GPU 指标采集。
- vLLM 参数调优。

半真实实现：

- Kubernetes 部署原型。
- Controller dry-run。
- Deployment patch。
- Prometheus/Grafana 可观测配置。

模拟实现：

- 多副本 scale-out/cold-start。
- prefix cache locality。
- GPU topology-aware scheduling。
- Kueue/Volcano 风格队列语义。
- 多租户 token-level quota。

第一版不声称生产级多节点 GPU 调度，不修改 vLLM 源码，不实现真实 Kueue/Volcano 插件。

## GitHub 上传

如果本机已经登录 GitHub CLI：

```bash
git init
git add .
git commit -m "init llm elastic governor learning repo"
gh repo create llm-elastic-governor --public --source . --remote origin --push
```

如果不用 GitHub CLI，可以手动创建空仓库后：

```bash
git remote add origin git@github.com:<your-name>/llm-elastic-governor.git
git branch -M main
git push -u origin main
```
