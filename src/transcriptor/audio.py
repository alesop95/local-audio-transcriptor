"""Decodifica di qualsiasi file audio/video in un array float32 mono 16 kHz, usando ffmpeg.

Decodificando noi stessi l'audio ed esponendolo come ndarray, WhisperX/faster-whisper non
hanno bisogno di trovare 'ffmpeg' nel PATH: basta il binario risolto da ffmpeg_tools.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from .ffmpeg_tools import ffmpeg_exe

SAMPLE_RATE = 16000


def load_audio(path: str | Path, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Carica `path` come waveform float32 normalizzata in [-1, 1], mono, a `sample_rate` Hz."""
    cmd = [
        ffmpeg_exe(),
        "-nostdin",
        "-threads", "0",
        "-i", str(path),
        "-f", "f32le",
        "-ac", "1",
        "-acodec", "pcm_f32le",
        "-ar", str(sample_rate),
        "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        stderr = exc.stderr.decode("utf-8", "ignore") if exc.stderr else ""
        raise RuntimeError(f"ffmpeg non è riuscito a decodificare {path}:\n{stderr}") from exc
    return np.frombuffer(proc.stdout, np.float32).copy()
