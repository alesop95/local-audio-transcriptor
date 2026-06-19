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
