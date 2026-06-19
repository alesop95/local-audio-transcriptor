"""Sorgente: YouTube (video singolo o playlist) tramite yt-dlp.

Scarica l'audio migliore e restituisce MediaItem pronti per la pipeline. ffmpeg è preso da
ffmpeg_tools (sistema o bundle), quindi non serve installarlo manualmente.
"""

from __future__ import annotations

from pathlib import Path

from ..ffmpeg_tools import ffmpeg_exe
from .local import MediaItem, _sanitize


def _ydl_opts(work_dir: Path, archive: bool) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    opts: dict = {
        "format": "bestaudio/best",
        "outtmpl": str(work_dir / "%(playlist_index)s-%(id)s.%(ext)s"),
        "ffmpeg_location": str(Path(ffmpeg_exe()).parent),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "noprogress": True,
    }
    if archive:
        opts["download_archive"] = str(work_dir / "downloaded.txt")
    return opts


def _entry_to_item(info: dict) -> MediaItem | None:
    if not info:
        return None
    # yt-dlp restituisce il percorso effettivo del file scaricato in 'requested_downloads'.
    path = None
    downloads = info.get("requested_downloads")
    if downloads:
        path = downloads[0].get("filepath")
    if not path:
        return None
    index = info.get("playlist_index")
    return MediaItem(
        audio_path=Path(path),
        title=info.get("title") or info.get("id") or "youtube",
        index=index,
    )


def fetch(
    url: str,
    work_dir: Path,
    *,
    playlist_items: str | None = None,
    archive: bool = True,
) -> list[MediaItem]:
    """Scarica audio da un URL YouTube (video o playlist). Ritorna la lista di MediaItem."""
    import yt_dlp

    opts = _ydl_opts(work_dir, archive)
    if playlist_items:
        opts["playlist_items"] = playlist_items

    items: list[MediaItem] = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            return items
        entries = info.get("entries")
        if entries is not None:  # playlist
            for entry in entries:
                item = _entry_to_item(entry)
                if item:
                    items.append(item)
        else:  # video singolo
            item = _entry_to_item(info)
            if item:
                items.append(item)
    return items


def list_playlist(url: str) -> list[dict]:
    """Estrae solo i metadati della playlist (titoli/id) senza scaricare nulla."""
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = (info or {}).get("entries") or []
    return [
        {
            "index": e.get("playlist_index") or i + 1,
            "id": e.get("id"),
            "title": _sanitize(e.get("title") or e.get("id") or "?"),
        }
        for i, e in enumerate(entries)
    ]
