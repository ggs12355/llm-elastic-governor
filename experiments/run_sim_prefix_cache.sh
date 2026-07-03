#!/usr/bin/env bash
set -euo pipefail
python -m simulator.prefix_cache --config configs/simulation/prefix_cache.yaml --output-dir results/sim_prefix_cache

