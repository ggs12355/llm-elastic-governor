#!/usr/bin/env bash
set -euo pipefail
python -m simulator.queue_scheduler --config configs/simulation/queues.yaml --output-dir results/sim_queue

