#!/usr/bin/env bash
set -euo pipefail
python -m simulator.topology_scheduler --config configs/simulation/topology.yaml --output-dir results/sim_topology

