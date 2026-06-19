"""Rilevamento automatico del device (GPU/CPU) e del relativo compute_type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceConfig:
    device: str  # "cuda" oppure "cpu"
    compute_type: str  # "float16" su GPU, "int8" su CPU


def _cuda_available() -> bool:
    try:
        import torch  # importato solo se lo stack ASR è installato

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def detect_device(prefer: str | None = None) -> DeviceConfig:
    """Sceglie il device. `prefer` ("cuda"/"cpu") forza la scelta; None = autodetect."""
    if prefer == "cpu":
        return DeviceConfig("cpu", "int8")
    if prefer == "cuda":
        return DeviceConfig("cuda", "float16")
    if _cuda_available():
        return DeviceConfig("cuda", "float16")
    return DeviceConfig("cpu", "int8")
