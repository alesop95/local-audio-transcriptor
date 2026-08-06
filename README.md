# Local Audio Transcriptor

Strumento **locale e cross-platform (Windows + Linux)** per trasformare audio in conoscenza: **trascrive → cerca → interroga → traduce → riassume**, tutto offline.

- Motore: [WhisperX](https://github.com/m-bain/whisperX) (backend faster-whisper / CTranslate2)
- Sorgenti: file locali e [YouTube](https://github.com/yt-dlp/yt-dlp) (video/playlist); ffmpeg incluso (`imageio-ffmpeg`, nessuna installazione manuale)
- Auto-rilevamento **GPU (CUDA) / CPU**; VAD `pyannote`/`silero`
- Diarizzazione (chi parla), sintesi LLM, ricerca full-text, Q&A (RAG) e traduzione offline
- Interfacce: **CLI** e **GUI** (Gradio)

### Comandi

| Comando | Cosa fa |
|---|---|
| `file` / `youtube` / `playlist` | Trascrive un file locale / un video / un'intera playlist |
| `stats` | Panoramica trascrizioni: durata, parole, lingua, speaker |
| `index` / `search` | Indicizza (SQLite FTS5) e cerca passaggi con timestamp |
| `ask` | Q&A in linguaggio naturale sulle trascrizioni (RAG), con citazioni |
| `summarize` / `digest` | Note strutturate per-file / sintesi consolidata dell'intero corpus |
| `translate` | Traduzione offline mantenendo i timestamp (SRT bilingue) |
| `info` | Elenca i video di una playlist senza scaricare |
| `gui` | Avvia l'interfaccia grafica locale |
| `doctor` | Diagnostica ambiente (ffmpeg, ASR, device, LLM, extra) |

Output: `txt`, `srt`, `vtt`, `json` (+ `.summary.md`, `_PLAYLIST_DIGEST.md`, `.<lang>.srt`).

## Installazione

Richiede Python 3.10–3.12. Consigliato [uv](https://github.com/astral-sh/uv).

### Installazione pulita (consigliata)

Installa `transcribe` come **comando globale isolato** (via `uv tool`), senza toccare il Python di sistema. Gli script installano anche `uv` se manca.

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```
```bash
# Linux / macOS
bash scripts/install.sh
```

Dopo l'installazione il comando `transcribe` è disponibile ovunque. Verifica con `transcribe doctor`. Per disinstallare: `uv tool uninstall local-audio-transcriptor`.

### Installazione da wheel

```bash
uv build                         # genera dist/*.whl e *.tar.gz
uv tool install "dist/local_audio_transcriptor-0.1.0-py3-none-any.whl[asr,gui]"
```

### Installazione di sviluppo (editable)

```bash
uv venv --python 3.11
# Attiva: Windows -> .venv\Scripts\activate ; Linux -> source .venv/bin/activate
uv pip install -e ".[asr,gui]"   # base + trascrizione + GUI
```

> **GPU NVIDIA**: per l'accelerazione CUDA installa il `torch` corretto per la tua versione di CUDA seguendo https://pytorch.org/get-started/locally/ prima di `".[asr]"`. Senza GPU il tool usa automaticamente la CPU (più lento ma funziona ovunque).

Verifica l'ambiente:

```bash
transcribe doctor
```

## Uso

```bash
# File locale
transcribe file "audio.mp3" --language it

# Video YouTube
transcribe youtube "https://www.youtube.com/watch?v=4Lbox-d0UcE" -l it

# Intera playlist (riprendibile: ri-eseguendo salta ciò che è già fatto)
transcribe playlist "https://www.youtube.com/playlist?list=PL-wATfeyAMNorsfMFg0ISfD0rPDpMHA4R" -l it

# Solo i primi 3 video della playlist
transcribe playlist "<url>" --items 1-3 -l it

# Interfaccia grafica locale (browser)
transcribe gui            # apre http://127.0.0.1:7860

# Con diarizzazione (richiede HF_TOKEN, vedi sotto)
transcribe file "intervista.wav" --diarize --min-speakers 2 --max-speakers 2

# VAD Silero per ridurre le allucinazioni di Whisper
transcribe youtube "<url>" --vad silero

# Elenca i video di una playlist senza scaricare
transcribe info "<url-playlist>"
```

Le trascrizioni vengono salvate in `out/`, i download temporanei in `work/`.

## Summarizzazione (note di ricerca via LLM)

Trasforma le trascrizioni in **note strutturate** (titolo, sintesi, punti chiave, glossario, domande aperte) usando un LLM **locale** via [Ollama](https://ollama.com) o qualsiasi endpoint OpenAI-compatibile (LM Studio, vLLM, OpenAI).

```bash
# 1) Avvia un LLM locale
ollama serve            # in un altro terminale
ollama pull llama3.1

# 2a) Trascrivi e riassumi in un colpo solo
transcribe youtube "<url>" --summarize

# 2b) Oppure riassumi trascrizioni già fatte (file o intera cartella)
transcribe summarize out/

# 2c) Sintesi CONSOLIDATA: un unico documento che collega tutti i video
transcribe digest out/        # -> out/_PLAYLIST_DIGEST.md
```

## Ricerca e Q&A sul materiale

```bash
# Indicizza (FTS5) e cerca passaggi con timestamp, offline, nessuna dipendenza extra
transcribe index out/
transcribe search "voice cloning"
# -> 003 - How Voice Cloning Works @ 00:00:17 ...

# Q&A in linguaggio naturale (RAG: retrieval FTS5 + LLM), con citazioni delle fonti
transcribe ask "Come funziona il voice cloning?"
```

## Traduzione offline

Traduce le trascrizioni mantenendo i timestamp, 100% offline con [argos-translate](https://github.com/argosopentech/argos-translate) (`uv pip install -e ".[translate]"`).

```bash
transcribe translate "out/003 - How Voice Cloning Works_ Explained EASILY.json" --to it
transcribe translate out/ --to it --bilingual    # tutta la cartella, testo orig.+tradotto
```

Configurabile via env / `.env`: `TRANSCRIBE_LLM_BASE_URL` (default `http://localhost:11434/v1`), `TRANSCRIBE_LLM_MODEL` (default `llama3.1`), `TRANSCRIBE_LLM_API_KEY`.

## Diarizzazione (chi parla)

1. Crea un token: https://huggingface.co/settings/tokens
2. Accetta i termini dei modelli:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
3. Copia `.env.example` in `.env` e incolla il token in `HF_TOKEN`.

## Caso d'uso: estrarre la playlist di riferimento

La playlist *Text-to-Speech & Voice Cloning Course* (6 video) può essere trascritta in blocco per ottenere il testo da usare come materiale di ricerca.

> **Nota verificata**: nonostante titolo/descrizione in italiano, l'audio dei video è in **inglese**. Lascia quindi l'**autodetect** della lingua (niente `--language`). Forzare la lingua sbagliata manda Whisper in loop di allucinazioni. Usa un modello `small`/`medium` per una buona qualità.

```bash
transcribe playlist "https://www.youtube.com/playlist?list=PL-wATfeyAMNorsfMFg0ISfD0rPDpMHA4R" \
    --formats txt,json --model medium
```

I file `out/NNN - <titolo>.txt` conterranno il contenuto testuale di ogni lezione.

### Suggerimenti di qualità
- **Lingua**: ometti `--language` (autodetect) salvo che tu sia certo della lingua dell'audio.
- **Modello**: `tiny` è veloce ma impreciso; `small`/`medium` sono il buon compromesso; `large-v3` il massimo.
- **CPU vs GPU**: senza GPU il tool usa `cpu`/`int8` (più lento). Con GPU NVIDIA + `torch` CUDA passa a `cuda`/`float16` automaticamente.

## Struttura

```
src/transcriptor/
  cli.py        comandi CLI (Typer): file|youtube|playlist|index|search|ask|
                summarize|digest|translate|info|gui|doctor
  config.py     impostazioni (env / .env): modello, lingua, LLM, HF token
  device.py     autodetect GPU/CPU
  ffmpeg_tools  risoluzione ffmpeg (sistema o bundle imageio-ffmpeg)
  audio.py      decodifica audio -> array 16kHz mono
  engine.py     wrapper WhisperX (transcribe / align / diarize / VAD)
  outputs.py    writer txt/srt/vtt/json
  pipeline.py   orchestrazione sorgente -> audio -> engine -> output
  summarize.py  sintesi LLM per-file + consolidata (Ollama/OpenAI-compat)
  stats.py      statistiche trascrizioni (durata/parole/lingua/speaker)
  search.py     indice full-text SQLite FTS5 + ricerca
  rag.py        Q&A (retrieval FTS5 + generazione LLM con citazioni)
  translate.py  traduzione offline (argos-translate)
  gui.py        interfaccia Gradio
  sources/      local.py, youtube.py (yt-dlp)
```

Extra di installazione: `.[asr]` (trascrizione), `.[gui]` (interfaccia), `.[translate]` (traduzione).

## Verso un'app completa (roadmap)

Progetti open-source di riferimento studiati per estendere il tool:

- [awesome-whisper](https://github.com/sindresorhus/awesome-whisper): indice dell'ecosistema Whisper.
- [Whishper](https://github.com/pluja/whishper): web UI 100% locale con editor sottotitoli (riferimento GUI).
- [ownscribe](https://github.com/paberr/ownscribe): trascrizione + summary LLM (Ollama/LM Studio).
- [Ollama-Transcriber](https://github.com/chumphrey-cmd/Ollama-Transcriber): Whisper + Ollama.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) / [WhisperX](https://github.com/m-bain/whisperX): motori.

Completato:
- ✅ Trascrizione file/YouTube/playlist con allineamento e diarizzazione
- ✅ GUI Gradio (`transcribe gui`): tab File / YouTube / Playlist
- ✅ Packaging: `scripts/install.{ps1,sh}` (install pulita via `uv tool`) + `uv build`
- ✅ Sintesi LLM (per-file e consolidata), ricerca full-text (FTS5), Q&A (RAG)
- ✅ Traduzione offline (argos-translate), VAD Silero anti-allucinazioni
- ✅ CI GitHub Actions (test su Linux + Windows)

Idee future: retrieval semantico (embeddings) per il Q&A, export PDF/EPUB (pandoc), TTS delle sintesi (Piper/Coqui), modalità server (API), esportazione Obsidian/Notion.

## Note legali

Scarica/trascrivi contenuti YouTube solo per uso personale e di ricerca, nel rispetto dei Termini di servizio della piattaforma e del diritto d'autore.
