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

echo "Install vLLM separately if it is not preinstalled."
echo "Match the torch CUDA wheel to your NVIDIA driver. The RTX 4090 validation used:"
echo '  pip install "torch==2.8.0+cu128" "torchvision==0.23.0+cu128" "torchaudio==2.8.0+cu128" --index-url https://download.pytorch.org/whl/cu128'
echo '  pip install "vllm==0.10.2" "transformers==4.55.2" "tokenizers==0.21.4"'
