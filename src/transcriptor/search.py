"""Ricerca full-text sulle trascrizioni, basata su SQLite FTS5 (zero dipendenze esterne).

Indicizza i segmenti dei file .json prodotti dalla trascrizione e permette ricerche per
parola/frase con timestamp, così da consultare rapidamente ore di materiale.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DB_NAME = "index.db"


def fmt_ts(seconds: float) -> str:
    s = int(seconds or 0)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass
class Hit:
    source: str
    start: float
    end: float
    speaker: str | None
    snippet: str
    text: str = ""

    def location(self) -> str:
        spk = f" {self.speaker}" if self.speaker else ""
        return f"{self.source} @ {fmt_ts(self.start)}{spk}"


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS seg USING fts5("
        "text, source UNINDEXED, start UNINDEXED, end UNINDEXED, speaker UNINDEXED)"
    )
    return conn


def build_index(folder: str | Path, db_path: Path | None = None) -> tuple[Path, int]:
    """(Ri)costruisce l'indice dai .json in `folder`. Ritorna (db_path, n_segmenti)."""
    folder = Path(folder)
    db_path = db_path or folder / DB_NAME
    if db_path.exists():
        db_path.unlink()

    conn = _connect(db_path)
    count = 0
    for jf in sorted(folder.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        rows = [
            (
                (seg.get("text") or "").strip(),
                jf.stem,
                float(seg.get("start", 0.0) or 0.0),
                float(seg.get("end", 0.0) or 0.0),
                seg.get("speaker"),
            )
            for seg in data.get("segments", [])
            if (seg.get("text") or "").strip()
        ]
        conn.executemany("INSERT INTO seg(text, source, start, end, speaker) VALUES (?,?,?,?,?)", rows)
        count += len(rows)
    conn.commit()
    conn.close()
    return db_path, count


def search(query: str, folder: str | Path = "out", db_path: Path | None = None, limit: int = 20) -> list[Hit]:
    """Cerca `query` nell'indice; lo costruisce al volo se manca. Ritorna i match ordinati."""
    folder = Path(folder)
    db_path = db_path or folder / DB_NAME
    if not db_path.exists():
        build_index(folder, db_path)

    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "SELECT source, start, end, speaker, snippet(seg, 0, '[', ']', ' … ', 12), text "
            "FROM seg WHERE seg MATCH ? ORDER BY bm25(seg) LIMIT ?",
            (query, limit),
        )
        return [
            Hit(source=r[0], start=r[1], end=r[2], speaker=r[3], snippet=r[4], text=r[5])
            for r in cur.fetchall()
        ]
    finally:
        conn.close()
