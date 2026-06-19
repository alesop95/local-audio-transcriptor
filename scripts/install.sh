#!/usr/bin/env bash
# Installer pulito per Linux/macOS — installa "transcribe" come comando globale isolato (uv tool).
# Uso:  bash scripts/install.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Progetto: $PROJECT_DIR"

# 1) Assicura uv
if ! command -v uv >/dev/null 2>&1; then
    echo "Installo uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2) Installa il tool con gli extra ASR (trascrizione) e GUI
echo "Installo 'transcribe' (puo' richiedere qualche minuto: scarica torch/whisperx)..."
uv tool install --force --python 3.11 "${PROJECT_DIR}[asr,gui]"

echo ""
echo "Fatto. Comando disponibile: transcribe"
echo "Verifica:  transcribe doctor"
echo "ffmpeg: incluso (imageio-ffmpeg). In alternativa: sudo apt install ffmpeg"
echo "GPU NVIDIA? installa torch CUDA: https://pytorch.org/get-started/locally/"
