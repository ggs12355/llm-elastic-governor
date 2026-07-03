#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y python3-venv python3-pip git curl jq

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"

echo "Checking GPU..."
nvidia-smi

echo "Install vLLM separately if it is not preinstalled:"
echo '  pip install "vllm>=0.6.0"'

