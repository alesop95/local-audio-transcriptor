"""Configurazione centrale del tool (default + override da env/.env)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Impostazioni globali, sovrascrivibili via variabili d'ambiente (prefisso TRANSCRIBE_) o .env."""

    model_config = SettingsConfigDict(env_prefix="TRANSCRIBE_", env_file=".env", extra="ignore")

    # Modello Whisper: tiny, base, small, medium, large-v3.
    model: str = "small"
    # Lingua forzata (None = autodetect). Per la playlist di riferimento: "it".
    language: str | None = None
    # Device: None = autodetect (cuda se disponibile, altrimenti cpu).
    device: str | None = None
    # Batch size per la trascrizione (whisperx).
    batch_size: int = 16
    # Formati di output da generare.
    formats: list[str] = ["txt", "srt", "vtt", "json"]
    # Cartelle di lavoro.
    out_dir: Path = Path("out")
    work_dir: Path = Path("work")
    # Token HuggingFace per la diarizzazione (pyannote). Caricato anche da HF_TOKEN.
    hf_token: str | None = None

    # --- Summarizzazione via LLM (Ollama o endpoint OpenAI-compatibile) ---
    # Ollama espone un'API OpenAI-compatibile su /v1.
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.1"
    llm_api_key: str | None = None  # "ollama" per Ollama; la vera chiave per OpenAI
    # Finestra di contesto (token) da richiedere al modello. None = non specificata (comportamento
    # di default del server). Su Ollama il default runtime e' spesso molto piu' piccolo del massimo
    # supportato dal modello: con input lunghi (es. digest di molte trascrizioni) va alzata esplicitamente.
    llm_num_ctx: int | None = None
    # Se True, chiama l'endpoint nativo Ollama (/api/chat) invece del layer OpenAI-compatibile
    # (/v1/chat/completions). Verificato empiricamente: su alcune versioni di Ollama il layer
    # OpenAI-compatibile NON rispetta num_ctx e tronca silenziosamente gli input lunghi, mentre
    # l'endpoint nativo lo rispetta correttamente. Da attivare solo se il backend e' Ollama
    # (non e' compatibile con un vero endpoint OpenAI/LM Studio/vLLM).
    llm_ollama_native: bool = False

    def resolved_hf_token(self) -> str | None:
        import os

        return self.hf_token or os.environ.get("HF_TOKEN")


settings = Settings()
