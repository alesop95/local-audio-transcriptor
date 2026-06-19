"""Scrittura dei risultati di trascrizione in txt, srt, vtt, json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_FORMATS = ("txt", "srt", "vtt", "json")


def _fmt_ts(seconds: float, *, comma: bool) -> str:
    if seconds is None or seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    h, millis = divmod(millis, 3_600_000)
    m, millis = divmod(millis, 60_000)
    s, millis = divmod(millis, 1000)
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{millis:03d}"


def _segment_text(seg: dict[str, Any]) -> str:
    text = (seg.get("text") or "").strip()
    speaker = seg.get("speaker")
    if speaker:
        return f"[{speaker}] {text}"
    return text


def _write_txt(segments: list[dict], path: Path) -> None:
    lines = [_segment_text(s) for s in segments if (s.get("text") or "").strip()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_srt(segments: list[dict], path: Path) -> None:
    blocks = []
    for i, seg in enumerate(segments, start=1):
        text = _segment_text(seg)
        if not text:
            continue
        start = _fmt_ts(seg.get("start", 0.0), comma=True)
        end = _fmt_ts(seg.get("end", 0.0), comma=True)
        blocks.append(f"{i}\n{start} --> {end}\n{text}\n")
    path.write_text("\n".join(blocks), encoding="utf-8")


def _write_vtt(segments: list[dict], path: Path) -> None:
    blocks = ["WEBVTT\n"]
    for seg in segments:
        text = _segment_text(seg)
        if not text:
            continue
        start = _fmt_ts(seg.get("start", 0.0), comma=False)
        end = _fmt_ts(seg.get("end", 0.0), comma=False)
        blocks.append(f"{start} --> {end}\n{text}\n")
    path.write_text("\n".join(blocks), encoding="utf-8")


def _write_json(result: dict, path: Path) -> None:
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def write_outputs(result: dict, out_base: Path, formats: list[str]) -> list[Path]:
    """Scrive i formati richiesti usando `out_base` come prefisso (senza estensione).

    Ritorna la lista dei file creati.
    """
    out_base.parent.mkdir(parents=True, exist_ok=True)
    segments = result.get("segments", [])
    written: list[Path] = []
    for fmt in formats:
        fmt = fmt.lower()
        # Aggiunge l'estensione (NON with_suffix): preserva tag come ".it" e nomi con punti.
        path = out_base.parent / f"{out_base.name}.{fmt}"
        if fmt == "txt":
            _write_txt(segments, path)
        elif fmt == "srt":
            _write_srt(segments, path)
        elif fmt == "vtt":
            _write_vtt(segments, path)
        elif fmt == "json":
            _write_json(result, path)
        else:
            continue
        written.append(path)
    return written
