.PHONY: install format lint test serve-vllm loadgen analyze plot mock-controller controller-dryrun controller-active deploy-vllm deploy-controller experiment-static experiment-hpa experiment-controller experiment-token-shift experiment-long-context experiment-multi-tenant sim-replicas sim-prefix-cache sim-topology sim-queue sim-tenant-quota clean-results

PYTHON ?= python
MODEL ?= Qwen/Qwen2.5-1.5B-Instruct
VLLM_BASE_URL ?= http://127.0.0.1:8000
PROMETHEUS_URL ?= http://127.0.0.1:9090
OUT ?= results

install:
	$(PYTHON) -m pip install -e ".[dev]"

format:
	$(PYTHON) -m ruff check src tests --fix

lint:
	$(PYTHON) -m ruff check src tests

test:
	$(PYTHON) -m pytest -q

serve-vllm:
	$(PYTHON) -m vllm.entrypoints.openai.api_server --model $(MODEL) --host 0.0.0.0 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.90 --enable-prefix-caching

loadgen:
	$(PYTHON) -m loadgen.runner --profile configs/load_profiles/steady_short.yaml --base-url $(VLLM_BASE_URL) --model $(MODEL) --output $(OUT)/steady_short.jsonl

analyze:
	$(PYTHON) -m loadgen.analyze --input $(OUT)/steady_short.jsonl --output-dir $(OUT)/analysis

plot:
	$(PYTHON) experiments/plot_results.py --results-dir $(OUT)

mock-controller:
	$(PYTHON) -m controller.main --config configs/controller/policy_default.yaml --metrics-source mock --mode dry-run --iterations 5

controller-dryrun:
	$(PYTHON) -m controller.main --config configs/controller/policy_default.yaml --prometheus-url $(PROMETHEUS_URL) --mode dry-run

controller-active:
	$(PYTHON) -m controller.main --config configs/controller/policy_default.yaml --prometheus-url $(PROMETHEUS_URL) --mode active

deploy-vllm:
	kubectl apply -f deploy/k8s/namespace.yaml
	kubectl apply -f deploy/k8s/vllm-deployment.yaml
	kubectl apply -f deploy/k8s/vllm-service.yaml

deploy-controller:
	kubectl apply -f deploy/k8s/controller-rbac.yaml
	kubectl apply -f deploy/k8s/controller-deployment.yaml

experiment-static:
	bash experiments/run_static_baseline.sh

experiment-hpa:
	bash experiments/run_hpa_baseline.sh

experiment-controller:
	bash experiments/run_controller_dryrun.sh

experiment-token-shift:
	bash experiments/run_token_shift.sh

experiment-long-context:
	bash experiments/run_long_context_mix.sh

experiment-multi-tenant:
	bash experiments/run_multi_tenant.sh

sim-replicas:
	$(PYTHON) -m simulator.multi_replica --config configs/simulation/replicas.yaml --output-dir $(OUT)/sim_replicas

sim-prefix-cache:
	$(PYTHON) -m simulator.prefix_cache --config configs/simulation/prefix_cache.yaml --output-dir $(OUT)/sim_prefix_cache

sim-topology:
	$(PYTHON) -m simulator.topology_scheduler --config configs/simulation/topology.yaml --output-dir $(OUT)/sim_topology

sim-queue:
	$(PYTHON) -m simulator.queue_scheduler --config configs/simulation/queues.yaml --output-dir $(OUT)/sim_queue

sim-tenant-quota:
	$(PYTHON) -m simulator.tenant_quota --config configs/simulation/tenants.yaml --output-dir $(OUT)/sim_tenant_quota

clean-results:
	$(PYTHON) -c "import shutil, pathlib; p=pathlib.Path('results'); shutil.rmtree(p, ignore_errors=True); p.mkdir(exist_ok=True); (p/'.gitkeep').touch()"

