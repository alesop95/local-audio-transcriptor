# RESUME-PROMPT — Local Audio Transcriptor

> Incolla/leggi questo file all'inizio di una nuova sessione di Claude Code per riprendere il
> progetto con tutto il contesto. Aggiornato: 2026-06-19.

## Cos'è il progetto

Strumento **locale, cross-platform (Windows + Linux)** per trasformare audio in conoscenza:
**trascrive → cerca → interroga (RAG) → traduce → riassume**, tutto offline.
Nato per estrarre il contenuto della playlist YouTube *Text-to-Speech & Voice Cloning Course*
(6 video, parlati in **inglese**) come fondamento di ricerca.

- Repo GitHub: `https://github.com/alesop95/local-audio-transcriptor`
- Remote SSH via alias macchina: `git@github-personal:alesop95/local-audio-transcriptor.git`
- Stato: commit iniziale `867215e` pushato su `main`. **I commit/push li fa SEMPRE l'utente, manualmente.**

## Stack

Python 3.11 (venv via `uv`). Motore **WhisperX** (faster-whisper) + allineamento + diarizzazione
(pyannote). Download **yt-dlp**; ffmpeg incluso (`imageio-ffmpeg`). Sintesi/RAG via **LLM
OpenAI-compatibile** (Ollama). Ricerca **SQLite FTS5**. Traduzione **argos-translate**. GUI **Gradio**.

## Stato dell'ambiente su QUESTA macchina (Windows 11)

- **Nessuna GPU** → device `cpu` / `int8` (più lento ma funziona).
- `.venv/` esiste ma è **gitignored**: se manca, va ricreata (vedi sotto).
- **Ollama NON installato** → `summarize`, `digest`, `ask` falliscono finché non si avvia un LLM
  (`ollama serve` + `ollama pull llama3.1`). Tutto il resto funziona senza.
- **HF_TOKEN assente** → la diarizzazione (`--diarize`) richiede il token (vedi `.env.example`).
- I modelli argos (traduzione) si scaricano alla prima esecuzione.
- `out/` contiene già le **6 trascrizioni** (.txt/.json) + `index.db` (gitignored, dati locali).

## Ricreare l'ambiente (se serve)

```powershell
uv venv --python 3.11
uv pip install -e ".[asr,gui,translate]"   # tutto; pesante (torch ecc.)
.\.venv\Scripts\python.exe -m transcriptor.cli doctor
```
Oppure installazione pulita globale: `powershell -ExecutionPolicy Bypass -File scripts\install.ps1`.

## Comandi (CLI `transcribe ...`)

| Comando | Cosa fa |
|---|---|
| `file` / `youtube` / `playlist` | Trascrive file locale / video / playlist (riprendibile) |
| `stats` | Panoramica: durata, parole, lingua, speaker (per file e totali) |
| `index` / `search "<q>"` | Indice FTS5 e ricerca con timestamp |
| `ask "<domanda>"` | Q&A RAG con citazioni (serve LLM) |
| `summarize <path>` / `digest <dir>` | Note per-file / sintesi consolidata (serve LLM) |
| `translate <json> --to it [--bilingual]` | Traduzione offline mantenendo i timestamp |
| `info <url>` | Elenca i video di una playlist |
| `gui` | Interfaccia Gradio locale |
| `doctor` | Diagnostica ambiente |

Opzioni utili: `--model small|medium|large-v3`, lingua in **autodetect** (NON forzare: l'audio è
inglese; forzando si hanno allucinazioni), `--vad silero` (anti-allucinazioni), `--device cpu|cuda`.

## Verifica rapida

```powershell
.\.venv\Scripts\python.exe -m pytest -q        # 5 test, devono passare
.\.venv\Scripts\python.exe -m transcriptor.cli doctor
.\.venv\Scripts\python.exe -m transcriptor.cli search "voice cloning" --folder out
```

## Cosa è già fatto (✅)

Trascrizione file/YouTube/playlist · allineamento · diarizzazione · auto GPU/CPU · output
txt/srt/vtt/json · sintesi LLM (per-file + consolidata) · ricerca FTS5 · RAG Q&A · traduzione
offline · VAD Silero · CLI + GUI · packaging (`uv tool`, wheel) · CI GitHub Actions (Linux+Windows).

## Idee / prossimi passi (non ancora fatti)

1. **Retrieval semantico** per il Q&A (embeddings via Ollama `/v1/embeddings` o sentence-transformers)
   al posto del solo keyword-match FTS5.
2. **Esporre le nuove funzioni nella GUI** (tab Ricerca / Q&A / Traduzione — ora la GUI fa solo trascrizione).
3. **Export** PDF/EPUB (pandoc), Obsidian/Notion.
4. **TTS** delle sintesi (Piper/Coqui) — a tema col corso.
5. **Modalità server/API** (stile faster-whisper-server).
6. Eventuale rerun della playlist con `--model medium` per qualità superiore.

## Workflow git (importante)

L'utente fa i commit a mano per capire ogni passo. Claude prepara le modifiche e mostra
`git status`, ma **non committa né pusha** salvo richiesta esplicita.

### Identità git (configurata)

Questo repo usa un'identità **personale LOCALE** (la globale resta quella di lavoro):
- `git config --local user.name` → `alesop95`
- `git config --local user.email` → `alessio.sopranzi.95@gmail.com`
- Remote SSH via alias `github-personal` (push con questa chiave).

Tutti i commit futuri in questo repo usano automaticamente l'identità personale. Se in futuro
comparisse di nuovo un autore di lavoro, ricontrolla `git config --local user.email`.
