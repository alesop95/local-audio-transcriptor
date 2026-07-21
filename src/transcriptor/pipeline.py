"""Orchestrazione: sorgente -> audio -> trascrizione -> output.

Stessa pipeline per file locali e YouTube: lo strato `sources` normalizza l'input in MediaItem
con un percorso audio locale, poi qui si decodifica e si trascrive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .audio import load_audio
from .device import DeviceConfig, detect_device
from .engine import Transcriber
from .outputs import write_outputs
from .sources.local import MediaItem


@dataclass
class TranscribeOptions:
    model: str = "small"
    language: str | None = None
    device: str | None = None
    vad_method: str = "pyannote"  # "pyannote" o "silero" (anti-allucinazioni)
    batch_size: int = 16
    formats: tuple[str, ...] = ("txt", "srt", "vtt", "json")
    diarize: bool = False
    hf_token: str | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None
    out_dir: Path = Path("out")
    # Summarizzazione LLM post-trascrizione
    summarize: bool = False
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.1"
    llm_api_key: str | None = None
    llm_num_ctx: int | None = None
    llm_ollama_native: bool = False


@dataclass
class TranscribeResult:
    item: MediaItem
    written: list[Path]
    language: str | None


def build_transcriber(opts: TranscribeOptions) -> tuple[Transcriber, DeviceConfig]:
    dev = detect_device(opts.device)
    transcriber = Transcriber(opts.model, dev, language=opts.language, vad_method=opts.vad_method)
    return transcriber, dev


def transcribe_item(
    item: MediaItem,
    opts: TranscribeOptions,
    transcriber: Transcriber | None = None,
) -> TranscribeResult:
    """Trascrive un singolo MediaItem. Riusa `transcriber` se fornito (batch su playlist)."""
    if transcriber is None:
        transcriber, _ = build_transcriber(opts)

    audio = load_audio(item.audio_path)
    result = transcriber.transcribe(
        audio,
        batch_size=opts.batch_size,
        diarize=opts.diarize,
        hf_token=opts.hf_token,
        min_speakers=opts.min_speakers,
        max_speakers=opts.max_speakers,
    )
    out_base = opts.out_dir / item.output_stem()
    written = write_outputs(result, out_base, list(opts.formats))
    return TranscribeResult(item=item, written=written, language=result.get("language"))
