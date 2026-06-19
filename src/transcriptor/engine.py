"""Wrapper attorno a WhisperX: trascrizione -> allineamento word-level -> (opz.) diarizzazione.

Lo stack ASR (whisperx, torch, pyannote) è importato in modo lazy così la CLI e le funzioni
YouTube/ffmpeg restano usabili anche senza aver installato l'extra pesante ".[asr]".
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .device import DeviceConfig


class ASRNotInstalled(RuntimeError):
    """Sollevata quando lo stack di trascrizione non è installato."""


def _import_whisperx():
    try:
        import whisperx  # noqa: WPS433

        return whisperx
    except Exception as exc:  # pragma: no cover - dipende dall'ambiente
        raise ASRNotInstalled(
            'Stack di trascrizione non installato. Esegui:  uv pip install -e ".[asr]"'
        ) from exc


def _load_diarization_pipeline(whisperx, hf_token: str | None, device: str):
    """Carica la pipeline di diarizzazione gestendo le differenze di API tra versioni di whisperx."""
    # whisperx recenti: whisperx.diarize.DiarizationPipeline; più vecchi: whisperx.DiarizationPipeline
    pipeline_cls = None
    if hasattr(whisperx, "diarize") and hasattr(whisperx.diarize, "DiarizationPipeline"):
        pipeline_cls = whisperx.diarize.DiarizationPipeline
    elif hasattr(whisperx, "DiarizationPipeline"):
        pipeline_cls = whisperx.DiarizationPipeline
    if pipeline_cls is None:  # pragma: no cover
        raise ASRNotInstalled("Versione di whisperx senza supporto diarizzazione.")
    return pipeline_cls(use_auth_token=hf_token, device=device)


class Transcriber:
    def __init__(
        self,
        model: str,
        device_cfg: DeviceConfig,
        language: str | None = None,
        vad_method: str = "pyannote",
    ):
        self._wx = _import_whisperx()
        self.device_cfg = device_cfg
        self.language = language
        self.model = self._wx.load_model(
            model,
            device_cfg.device,
            compute_type=device_cfg.compute_type,
            language=language,
            vad_method=vad_method,
        )

    def transcribe(
        self,
        audio: np.ndarray,
        *,
        batch_size: int = 16,
        align: bool = True,
        diarize: bool = False,
        hf_token: str | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
    ) -> dict[str, Any]:
        wx = self._wx
        device = self.device_cfg.device

        result = self.model.transcribe(audio, batch_size=batch_size, language=self.language)
        detected_language = result.get("language", self.language)

        if align:
            try:
                model_a, metadata = wx.load_align_model(language_code=detected_language, device=device)
                aligned = wx.align(
                    result["segments"], model_a, metadata, audio, device, return_char_alignments=False
                )
                aligned["language"] = detected_language
                result = aligned
            except Exception:
                # L'allineamento è opzionale: se il modello di align non è disponibile per la
                # lingua, si prosegue con i timestamp a livello di segmento.
                result.setdefault("language", detected_language)

        if diarize:
            if not hf_token:
                raise RuntimeError(
                    "Diarizzazione richiesta ma HF_TOKEN mancante. Vedi .env.example."
                )
            diar_pipeline = _load_diarization_pipeline(wx, hf_token, device)
            diar_segments = diar_pipeline(audio, min_speakers=min_speakers, max_speakers=max_speakers)
            result = wx.assign_word_speakers(diar_segments, result)
            result.setdefault("language", detected_language)

        return result
