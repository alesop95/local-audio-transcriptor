"""Risoluzione di ffmpeg: usa quello di sistema se presente, altrimenti il binario bundle
(imageio-ffmpeg). Questo rende il tool autosufficiente su Windows e Linux senza
installazione manuale di ffmpeg."""

from __future__ import annotations

import functools
import shutil


@functools.lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    """Percorso assoluto all'eseguibile ffmpeg utilizzabile."""
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - dipende dall'ambiente
        raise RuntimeError(
            "ffmpeg non trovato. Installa ffmpeg di sistema "
            "(Windows: 'winget install Gyan.FFmpeg'; Linux: 'sudo apt install ffmpeg') "
            "oppure assicurati che il pacchetto 'imageio-ffmpeg' sia installato."
        ) from exc
