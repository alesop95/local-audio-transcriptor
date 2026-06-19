"""Statistiche sulle trascrizioni: durata, parole, lingua, speaker per file e totali.

Legge i .json prodotti dalla trascrizione; nessuna dipendenza esterna.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


def fmt_duration(seconds: float) -> str:
    s = int(seconds or 0)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass
class FileStats:
    source: str
    language: str | None
    segments: int
    words: int
    duration: float
    speakers: int


def collect_stats(folder: str | Path) -> list[FileStats]:
    """Calcola le statistiche per ogni .json in `folder` (in ordine)."""
    folder = Path(folder)
    out: list[FileStats] = []
    for jf in sorted(folder.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        segs = data.get("segments", [])
        words = sum(len((s.get("text") or "").split()) for s in segs)
        duration = max((float(s.get("end", 0.0) or 0.0) for s in segs), default=0.0)
        speakers = {s.get("speaker") for s in segs if s.get("speaker")}
        out.append(
            FileStats(
                source=jf.stem,
                language=data.get("language"),
                segments=len(segs),
                words=words,
                duration=duration,
                speakers=len(speakers),
            )
        )
    return out
