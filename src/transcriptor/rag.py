"""RAG Q&A sulle trascrizioni: recupera i passaggi pertinenti (FTS5) e li passa all'LLM
per generare una risposta con citazioni (fonte @ timestamp).

Retrieval keyword-based via SQLite FTS5 (riusa search.py) → nessuna dipendenza vettoriale.
Generazione via LLM locale (Ollama / OpenAI-compatibile, riusa summarize._chat).
"""

from __future__ import annotations

import re
from pathlib import Path

from .search import Hit, search
from .summarize import LLMError, _chat

RAG_SYSTEM_PROMPT = (
    "Sei un assistente che risponde basandosi ESCLUSIVAMENTE sugli estratti di trascrizione forniti. "
    "Cita sempre le fonti nel formato (fonte @ timestamp) accanto alle affermazioni. "
    "Se gli estratti non contengono la risposta, dichiaralo apertamente. "
    "Rispondi nella stessa lingua della domanda, in modo chiaro e conciso."
)

_STOPWORDS = {
    "the", "and", "for", "what", "which", "that", "with", "how", "why", "does", "are", "is",
    "come", "cosa", "che", "quale", "quali", "per", "con", "del", "della", "delle", "dei", "uno",
    "una", "gli", "the", "this", "these", "those",
}


def _to_fts_query(question: str) -> str:
    """Converte una domanda in lingua naturale in una query FTS5 (OR di termini significativi)."""
    tokens = re.findall(r"\w+", question.lower())
    terms = [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]
    if not terms:
        terms = [t for t in tokens if len(t) > 2] or tokens
    return " OR ".join(f'"{t}"' for t in terms) if terms else question


def ask(
    question: str,
    *,
    folder: str | Path = "out",
    base_url: str,
    model: str,
    api_key: str | None = None,
    num_ctx: int | None = None,
    ollama_native: bool = False,
    k: int = 12,
) -> tuple[str, list[Hit]]:
    """Risponde a `question` usando le trascrizioni in `folder`. Ritorna (risposta, fonti)."""
    hits = search(_to_fts_query(question), folder=folder, limit=k)
    if not hits:
        raise LLMError("Nessun passaggio pertinente trovato nelle trascrizioni (indicizza prima con 'index').")

    context = "\n".join(f"[{h.location()}] {h.text or h.snippet}" for h in hits)
    user = f"ESTRATTI:\n{context}\n\nDOMANDA: {question}"
    answer = _chat(
        RAG_SYSTEM_PROMPT, user, base_url=base_url, model=model, api_key=api_key,
        num_ctx=num_ctx, ollama_native=ollama_native,
    )
    return answer, hits
