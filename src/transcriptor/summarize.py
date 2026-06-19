"""Summarizzazione delle trascrizioni tramite un LLM locale (Ollama) o qualsiasi
endpoint OpenAI-compatibile (LM Studio, vLLM, OpenAI, ...).

Trasforma una trascrizione grezza in note strutturate utili come "fondamento di ricerca":
titolo, sintesi, punti chiave, glossario dei termini tecnici, domande aperte.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_SYSTEM_PROMPT = (
    "Sei un assistente di ricerca. Ricevi la trascrizione (eventualmente grezza, con errori "
    "di riconoscimento) di una lezione/video. Produci note strutturate in Markdown NELLA STESSA "
    "LINGUA della trascrizione. Struttura richiesta:\n"
    "# Titolo\n"
    "## Sintesi (3-5 frasi)\n"
    "## Punti chiave (elenco)\n"
    "## Concetti e termini tecnici (termine — definizione breve)\n"
    "## Domande aperte / approfondimenti\n"
    "Correggi gli errori evidenti di trascrizione quando il senso è chiaro. Sii fedele al contenuto."
)


DIGEST_SYSTEM_PROMPT = (
    "Sei un assistente di ricerca. Ricevi le sintesi di più video di una stessa playlist/corso. "
    "Produci un UNICO documento di sintesi consolidata in Markdown, NELLA STESSA LINGUA delle sintesi. "
    "Struttura richiesta:\n"
    "# Sintesi consolidata del corso\n"
    "## Panoramica (di cosa tratta il corso nel complesso)\n"
    "## Indice dei contenuti (un punto per video, in ordine)\n"
    "## Temi e fili conduttori (concetti che ricorrono tra i video)\n"
    "## Glossario unificato (termine — definizione)\n"
    "## Percorso di apprendimento suggerito / prossimi passi\n"
    "Collega i contenuti tra loro, evidenzia progressione e dipendenze. Sii sintetico ma completo."
)


class LLMError(RuntimeError):
    pass


def _chat(
    system_prompt: str,
    user_content: str,
    *,
    base_url: str,
    model: str,
    api_key: str | None,
    timeout: int = 600,
) -> str:
    """Chiamata a un endpoint chat-completions OpenAI-compatibile. Ritorna il contenuto."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "stream": False,
    }
    url = base_url.rstrip("/") + "/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise LLMError(
            f"Impossibile contattare l'LLM su {url}: {exc}. "
            "Avvia Ollama ('ollama serve') o configura TRANSCRIBE_LLM_BASE_URL."
        ) from exc

    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:  # pragma: no cover
        raise LLMError(f"Risposta LLM inattesa: {body}") from exc


def summarize_text(
    text: str,
    *,
    base_url: str,
    model: str,
    api_key: str | None = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_chars: int = 48000,
    timeout: int = 600,
) -> str:
    """Riassume un testo in note strutturate (Markdown)."""
    if not text.strip():
        raise LLMError("Trascrizione vuota: niente da riassumere.")
    # Tronca testi molto lunghi per restare nel contesto del modello (strategia semplice v1).
    content = text if len(text) <= max_chars else text[:max_chars] + "\n[...troncato...]"
    return _chat(system_prompt, content, base_url=base_url, model=model, api_key=api_key, timeout=timeout)


def consolidate_summaries(
    parts: list[tuple[str, str]],
    *,
    base_url: str,
    model: str,
    api_key: str | None = None,
    timeout: int = 600,
) -> str:
    """Sintesi consolidata da una lista di (titolo, sintesi_markdown)."""
    if not parts:
        raise LLMError("Nessuna sintesi da consolidare.")
    joined = "\n\n".join(f"## {title}\n{summary}" for title, summary in parts)
    return _chat(DIGEST_SYSTEM_PROMPT, joined, base_url=base_url, model=model, api_key=api_key, timeout=timeout)


def summarize_file(
    txt_path: str | Path,
    *,
    base_url: str,
    model: str,
    api_key: str | None = None,
) -> Path:
    """Riassume un file .txt e scrive '<nome>.summary.md' accanto. Ritorna il percorso creato."""
    txt_path = Path(txt_path)
    text = txt_path.read_text(encoding="utf-8")
    summary = summarize_text(text, base_url=base_url, model=model, api_key=api_key)
    out_path = txt_path.with_suffix(".summary.md")
    out_path.write_text(summary + "\n", encoding="utf-8")
    return out_path


def collect_transcripts(folder: str | Path) -> list[Path]:
    """Elenca i .txt di trascrizione di una cartella, in ordine (esclude i .summary)."""
    folder = Path(folder)
    return sorted(p for p in folder.glob("*.txt") if ".summary" not in p.name)


def make_digest(
    folder: str | Path,
    *,
    base_url: str,
    model: str,
    api_key: str | None = None,
    out_name: str = "_PLAYLIST_DIGEST.md",
    on_progress=None,
) -> Path:
    """Sintesi consolidata di tutte le trascrizioni in `folder` (map-reduce).

    1) riassume ogni .txt;  2) consolida le sintesi in un unico documento.
    `on_progress(i, total, name)` è chiamata, se fornita, prima di ogni sintesi.
    """
    files = collect_transcripts(folder)
    if not files:
        raise LLMError(f"Nessuna trascrizione .txt in {folder}.")

    parts: list[tuple[str, str]] = []
    for i, f in enumerate(files, start=1):
        if on_progress:
            on_progress(i, len(files), f.name)
        text = f.read_text(encoding="utf-8")
        summary = summarize_text(text, base_url=base_url, model=model, api_key=api_key)
        parts.append((f.stem, summary))

    digest = consolidate_summaries(parts, base_url=base_url, model=model, api_key=api_key)
    out_path = Path(folder) / out_name
    out_path.write_text(digest + "\n", encoding="utf-8")
    return out_path
