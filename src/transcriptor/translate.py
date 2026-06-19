"""Traduzione offline delle trascrizioni con argos-translate (modelli NMT locali).

Traduce i segmenti mantenendo i timestamp, quindi genera SRT/TXT/VTT tradotti (o bilingue).
Lo stack di traduzione è importato in modo lazy: extra ".[translate]".
"""

from __future__ import annotations

import json
from pathlib import Path

from .outputs import write_outputs


class TranslateError(RuntimeError):
    pass


def _import_argos():
    try:
        import argostranslate.package as package
        import argostranslate.translate as translate

        return package, translate
    except Exception as exc:  # pragma: no cover - dipende dall'ambiente
        raise TranslateError(
            'Stack di traduzione non installato. Esegui:  uv pip install -e ".[translate]"'
        ) from exc


def ensure_pair(from_code: str, to_code: str) -> None:
    """Assicura che la coppia linguistica from->to sia installata (la scarica se manca)."""
    package, translate = _import_argos()

    langs = translate.get_installed_languages()
    from_l = next((l for l in langs if l.code == from_code), None)
    to_l = next((l for l in langs if l.code == to_code), None)
    if from_l and to_l and from_l.get_translation(to_l):
        return

    package.update_package_index()
    available = package.get_available_packages()
    match = next((p for p in available if p.from_code == from_code and p.to_code == to_code), None)
    if match is None:
        raise TranslateError(f"Coppia linguistica {from_code}->{to_code} non disponibile in argos.")
    package.install_from_path(match.download())


def translate_text(text: str, from_code: str, to_code: str) -> str:
    _, translate = _import_argos()
    ensure_pair(from_code, to_code)
    return translate.translate(text, from_code, to_code)


def translate_json(
    json_path: str | Path,
    to_code: str,
    *,
    from_code: str | None = None,
    bilingual: bool = False,
    formats: list[str] | None = None,
) -> list[Path]:
    """Traduce un transcript .json e scrive '<nome>.<to>.{srt,txt,vtt}'. Ritorna i file creati."""
    _, translate = _import_argos()
    json_path = Path(json_path)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    src = from_code or data.get("language") or "en"
    ensure_pair(src, to_code)

    out_segments = []
    for seg in data.get("segments", []):
        original = (seg.get("text") or "").strip()
        if not original:
            continue
        translated = translate.translate(original, src, to_code).strip()
        text = f"{original}\n{translated}" if bilingual else translated
        out_segments.append({"start": seg.get("start", 0.0), "end": seg.get("end", 0.0), "text": text,
                             **({"speaker": seg["speaker"]} if seg.get("speaker") else {})})

    result = {"language": to_code, "segments": out_segments}
    out_base = json_path.with_suffix("")  # rimuove .json
    out_base = out_base.with_name(out_base.name + f".{to_code}")
    return write_outputs(result, out_base, formats or ["srt", "txt", "vtt"])
