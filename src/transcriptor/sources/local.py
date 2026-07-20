"""Sorgente: file audio/video locali."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MediaItem:
    """Un elemento multimediale pronto per la pipeline."""

    audio_path: Path
    title: str
    index: int | None = None  # posizione nella playlist, se applicabile

    def output_stem(self) -> str:
        """Nome file di output ripulito (con eventuale numerazione playlist)."""
        safe = _sanitize(self.title)
        if self.index is not None:
            return f"{self.index:03d} - {safe}"
        return safe


def _sanitize(name: str) -> str:
    bad = '<>:"/\\|?*'
    cleaned = "".join("_" if c in bad else c for c in name).strip()
    return cleaned[:120] or "transcript"


def resolve_local(path: str | Path) -> MediaItem:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"File non trovato: {p}")
    if not p.is_file():
        raise ValueError(f"Non è un file: {p}")
    return MediaItem(audio_path=p, title=p.stem)


# Estensioni audio/video che ffmpeg sa decodificare, usate per filtrare una cartella.
MEDIA_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma",
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv",
}


def resolve_folder(path: str | Path) -> list[MediaItem]:
    """Elenca i file audio/video di una cartella (non ricorsivo), in ordine alfabetico."""
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Cartella non trovata: {p}")
    if not p.is_dir():
        raise ValueError(f"Non è una cartella: {p}")
    files = sorted(
        f for f in p.iterdir() if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS
    )
    return [MediaItem(audio_path=f, title=f.stem, index=i) for i, f in enumerate(files, start=1)]
