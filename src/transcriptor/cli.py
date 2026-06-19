"""Interfaccia a riga di comando (Typer)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import settings

app = typer.Typer(
    add_completion=False,
    help="Tool locale di trascrizione audio (file locali o YouTube), cross-platform.",
)
console = Console()


def _common_opts(
    model: str,
    language: Optional[str],
    device: Optional[str],
    diarize: bool,
    formats: str,
    out_dir: Path,
    min_speakers: Optional[int],
    max_speakers: Optional[int],
    summarize: bool = False,
    vad: str = "pyannote",
):
    from .pipeline import TranscribeOptions

    fmts = tuple(f.strip().lower() for f in formats.split(",") if f.strip())
    if summarize and "txt" not in fmts:
        fmts = fmts + ("txt",)  # la summarizzazione legge il .txt
    return TranscribeOptions(
        model=model or settings.model,
        language=language if language is not None else settings.language,
        device=device,
        vad_method=vad,
        batch_size=settings.batch_size,
        formats=fmts,
        diarize=diarize,
        hf_token=settings.resolved_hf_token(),
        min_speakers=min_speakers,
        max_speakers=max_speakers,
        out_dir=out_dir,
        summarize=summarize,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        llm_api_key=settings.llm_api_key,
    )


# Opzioni condivise tra i comandi
ModelOpt = typer.Option("small", "--model", "-m", help="Modello Whisper: tiny|base|small|medium|large-v3")
LangOpt = typer.Option(None, "--language", "-l", help="Lingua (es. 'it'). Vuoto = autodetect.")
DeviceOpt = typer.Option(None, "--device", help="Forza device: 'cuda' o 'cpu'. Vuoto = autodetect.")
DiarizeOpt = typer.Option(False, "--diarize/--no-diarize", help="Identifica i parlanti (richiede HF_TOKEN).")
FormatsOpt = typer.Option("txt,srt,vtt,json", "--formats", "-f", help="Formati separati da virgola.")
OutOpt = typer.Option(Path("out"), "--out", "-o", help="Cartella di output.")
MinSpkOpt = typer.Option(None, "--min-speakers", help="Numero minimo di parlanti (diarizzazione).")
MaxSpkOpt = typer.Option(None, "--max-speakers", help="Numero massimo di parlanti (diarizzazione).")
SummarizeOpt = typer.Option(False, "--summarize/--no-summarize", "-s", help="Genera note strutturate via LLM (Ollama).")
VadOpt = typer.Option("pyannote", "--vad", help="Metodo VAD: pyannote | silero (silero riduce le allucinazioni).")


def _summarize_written(written, opts):
    """Riassume i .txt prodotti, se richiesto. Best-effort: non interrompe la pipeline."""
    if not opts.summarize:
        return
    from .summarize import LLMError, summarize_file

    for path in written:
        if path.suffix.lower() != ".txt":
            continue
        try:
            md = summarize_file(
                path,
                base_url=opts.llm_base_url,
                model=opts.llm_model,
                api_key=opts.llm_api_key,
            )
            console.print(f"  [green]+[/] {md} [dim](sintesi)[/]")
        except LLMError as exc:
            console.print(f"  [yellow]Sintesi saltata:[/] {exc}")


def _run_items(items, opts):
    from .pipeline import build_transcriber, transcribe_item

    if not items:
        console.print("[yellow]Nessun elemento da trascrivere.[/]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Caricamento modello '{opts.model}'...[/]")
    transcriber, dev = build_transcriber(opts)
    console.print(f"[green]Device:[/] {dev.device} ({dev.compute_type})")

    for n, item in enumerate(items, start=1):
        console.print(f"\n[bold]({n}/{len(items)})[/] {item.title}")
        try:
            res = transcribe_item(item, opts, transcriber=transcriber)
        except Exception as exc:  # noqa: BLE001
            console.print(f"  [red]Errore:[/] {exc}")
            continue
        console.print(f"  lingua: {res.language or '?'}")
        for path in res.written:
            console.print(f"  [green]+[/] {path}")
        _summarize_written(res.written, opts)


@app.command()
def file(
    path: Path = typer.Argument(..., help="File audio/video locale da trascrivere."),
    model: str = ModelOpt,
    language: Optional[str] = LangOpt,
    device: Optional[str] = DeviceOpt,
    diarize: bool = DiarizeOpt,
    formats: str = FormatsOpt,
    out: Path = OutOpt,
    min_speakers: Optional[int] = MinSpkOpt,
    max_speakers: Optional[int] = MaxSpkOpt,
    summarize: bool = SummarizeOpt,
    vad: str = VadOpt,
):
    """Trascrive un file locale."""
    from .sources.local import resolve_local

    opts = _common_opts(model, language, device, diarize, formats, out, min_speakers, max_speakers, summarize, vad)
    item = resolve_local(path)
    _run_items([item], opts)


@app.command()
def youtube(
    url: str = typer.Argument(..., help="URL di un video YouTube."),
    model: str = ModelOpt,
    language: Optional[str] = LangOpt,
    device: Optional[str] = DeviceOpt,
    diarize: bool = DiarizeOpt,
    formats: str = FormatsOpt,
    out: Path = OutOpt,
    min_speakers: Optional[int] = MinSpkOpt,
    max_speakers: Optional[int] = MaxSpkOpt,
    summarize: bool = SummarizeOpt,
    vad: str = VadOpt,
):
    """Scarica e trascrive un singolo video YouTube."""
    from .sources import youtube as yt

    opts = _common_opts(model, language, device, diarize, formats, out, min_speakers, max_speakers, summarize, vad)
    console.print("[cyan]Download audio da YouTube...[/]")
    try:
        items = yt.fetch(url, settings.work_dir, archive=True)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Download fallito:[/] {exc}")
        raise typer.Exit(code=1)
    _run_items(items, opts)


@app.command()
def playlist(
    url: str = typer.Argument(..., help="URL di una playlist YouTube."),
    items: Optional[str] = typer.Option(None, "--items", help="Range, es. '1-3' o '1,4,7'."),
    model: str = ModelOpt,
    language: Optional[str] = LangOpt,
    device: Optional[str] = DeviceOpt,
    diarize: bool = DiarizeOpt,
    formats: str = FormatsOpt,
    out: Path = OutOpt,
    min_speakers: Optional[int] = MinSpkOpt,
    max_speakers: Optional[int] = MaxSpkOpt,
    summarize: bool = SummarizeOpt,
    vad: str = VadOpt,
):
    """Scarica e trascrive un'intera playlist YouTube (riprendibile)."""
    from .sources import youtube as yt

    opts = _common_opts(model, language, device, diarize, formats, out, min_speakers, max_speakers, summarize, vad)
    console.print("[cyan]Download audio della playlist...[/]")
    try:
        media = yt.fetch(url, settings.work_dir, playlist_items=items, archive=True)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Download fallito:[/] {exc}")
        raise typer.Exit(code=1)
    _run_items(media, opts)


@app.command()
def summarize(
    path: Path = typer.Argument(..., help="File .txt o cartella di trascrizioni da riassumere."),
    model: str = typer.Option(None, "--llm-model", help="Modello LLM (default da config: llama3.1)."),
    base_url: str = typer.Option(None, "--llm-url", help="Endpoint OpenAI-compatibile (default Ollama)."),
):
    """Genera note strutturate (Markdown) dai .txt usando un LLM locale (Ollama) o OpenAI-compatibile."""
    from .summarize import LLMError, summarize_file

    base = base_url or settings.llm_base_url
    mdl = model or settings.llm_model
    key = settings.llm_api_key

    if path.is_dir():
        targets = sorted(p for p in path.glob("*.txt") if not p.name.endswith(".summary.txt"))
    else:
        targets = [path]
    if not targets:
        console.print("[yellow]Nessun .txt trovato.[/]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Sintesi via[/] {mdl} @ {base}")
    for p in targets:
        console.print(f"  {p.name}")
        try:
            md = summarize_file(p, base_url=base, model=mdl, api_key=key)
            console.print(f"  [green]+[/] {md}")
        except LLMError as exc:
            console.print(f"  [red]Errore:[/] {exc}")


@app.command()
def digest(
    folder: Path = typer.Argument(Path("out"), help="Cartella con le trascrizioni .txt."),
    model: str = typer.Option(None, "--llm-model", help="Modello LLM (default da config)."),
    base_url: str = typer.Option(None, "--llm-url", help="Endpoint OpenAI-compatibile (default Ollama)."),
):
    """Sintesi consolidata: un unico documento Markdown che collega tutte le trascrizioni."""
    from .summarize import LLMError, make_digest

    base = base_url or settings.llm_base_url
    mdl = model or settings.llm_model
    console.print(f"[cyan]Sintesi consolidata via[/] {mdl} @ {base}")

    def _progress(i, total, name):
        console.print(f"  [{i}/{total}] {name}")

    try:
        out = make_digest(folder, base_url=base, model=mdl, api_key=settings.llm_api_key, on_progress=_progress)
    except LLMError as exc:
        console.print(f"[red]Errore:[/] {exc}")
        raise typer.Exit(code=1)
    console.print(f"[green]+[/] {out}")


@app.command()
def stats(folder: Path = typer.Argument(Path("out"), help="Cartella con i .json da analizzare.")):
    """Panoramica delle trascrizioni: durata, parole, lingua, speaker (per file e totali)."""
    from .stats import collect_stats, fmt_duration

    items = collect_stats(folder)
    if not items:
        console.print("[yellow]Nessuna trascrizione .json trovata.[/]")
        raise typer.Exit(code=1)

    table = Table(title=f"Statistiche: {len(items)} trascrizioni")
    table.add_column("#", justify="right")
    table.add_column("Sorgente")
    table.add_column("Lingua")
    table.add_column("Durata", justify="right")
    table.add_column("Parole", justify="right")
    table.add_column("Segm.", justify="right")
    table.add_column("Speaker", justify="right")

    tot_words = tot_dur = 0
    for i, s in enumerate(items, start=1):
        tot_words += s.words
        tot_dur += s.duration
        src = s.source if len(s.source) <= 48 else s.source[:45] + "..."
        table.add_row(str(i), src, s.language or "?", fmt_duration(s.duration),
                      f"{s.words:,}", str(s.segments), str(s.speakers) if s.speakers else "-")
    table.add_section()
    table.add_row("", "[bold]TOTALE[/]", "", f"[bold]{fmt_duration(tot_dur)}[/]", f"[bold]{tot_words:,}[/]", "", "")
    console.print(table)


@app.command()
def index(folder: Path = typer.Argument(Path("out"), help="Cartella con i .json da indicizzare.")):
    """Costruisce l'indice full-text (SQLite FTS5) delle trascrizioni."""
    from .search import build_index

    db, n = build_index(folder)
    console.print(f"[green]Indice creato:[/] {db} ({n} segmenti)")


@app.command()
def search(
    query: str = typer.Argument(..., help="Testo da cercare (sintassi FTS5)."),
    folder: Path = typer.Option(Path("out"), "--folder", help="Cartella delle trascrizioni."),
    limit: int = typer.Option(20, "--limit", "-n", help="Numero massimo di risultati."),
):
    """Ricerca full-text nelle trascrizioni (con timestamp)."""
    from .search import search as run_search

    hits = run_search(query, folder=folder, limit=limit)
    if not hits:
        console.print("[yellow]Nessun risultato.[/]")
        raise typer.Exit(code=1)
    for h in hits:
        console.print(f"[cyan]{h.location()}[/]")
        console.print(f"  {h.snippet}", markup=False)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Domanda in linguaggio naturale sul materiale."),
    folder: Path = typer.Option(Path("out"), "--folder", help="Cartella delle trascrizioni."),
    llm_model: str = typer.Option(None, "--llm-model", help="Modello LLM (default da config)."),
    llm_url: str = typer.Option(None, "--llm-url", help="Endpoint OpenAI-compatibile (default Ollama)."),
):
    """RAG Q&A: risponde a una domanda usando le trascrizioni, citando le fonti."""
    from .rag import ask as run_ask
    from .summarize import LLMError

    try:
        answer, hits = run_ask(
            question,
            folder=folder,
            base_url=llm_url or settings.llm_base_url,
            model=llm_model or settings.llm_model,
            api_key=settings.llm_api_key,
        )
    except LLMError as exc:
        console.print(f"[red]Errore:[/] {exc}")
        raise typer.Exit(code=1)
    console.print(answer)
    console.print("\n[dim]Fonti:[/]")
    for h in hits:
        console.print(f"[dim]- {h.location()}[/]")


@app.command()
def translate(
    path: Path = typer.Argument(..., help="File .json (o cartella) da tradurre."),
    to: str = typer.Option("it", "--to", help="Lingua di destinazione (es. it)."),
    source: str = typer.Option(None, "--from", help="Lingua di origine (default: dal json)."),
    bilingual: bool = typer.Option(False, "--bilingual", help="Mantieni anche il testo originale."),
    formats: str = typer.Option("srt,txt", "--formats", "-f", help="Formati di output."),
):
    """Traduce le trascrizioni offline (argos-translate), mantenendo i timestamp."""
    from .translate import TranslateError, translate_json

    fmts = [f.strip() for f in formats.split(",") if f.strip()]
    targets = sorted(path.glob("*.json")) if path.is_dir() else [path]
    if not targets:
        console.print("[yellow]Nessun .json trovato.[/]")
        raise typer.Exit(code=1)

    for jf in targets:
        console.print(f"[cyan]Traduco[/] {jf.name} -> {to}")
        try:
            written = translate_json(jf, to, from_code=source, bilingual=bilingual, formats=fmts)
        except TranslateError as exc:
            console.print(f"  [red]Errore:[/] {exc}")
            continue
        for p in written:
            console.print(f"  [green]+[/] {p}")


@app.command()
def info(url: str = typer.Argument(..., help="URL di una playlist YouTube.")):
    """Elenca i video di una playlist senza scaricare nulla."""
    from .sources import youtube as yt

    try:
        entries = yt.list_playlist(url)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Impossibile leggere la playlist:[/] {exc}")
        console.print("[yellow]Se è un 429 (Too Many Requests), riprova più tardi o usa un VPN/cookies.[/]")
        raise typer.Exit(code=1)
    table = Table(title=f"Playlist: {len(entries)} video")
    table.add_column("#", justify="right")
    table.add_column("ID")
    table.add_column("Titolo")
    for e in entries:
        table.add_row(str(e["index"]), e["id"] or "?", e["title"])
    console.print(table)


@app.command()
def gui(
    host: str = typer.Option("127.0.0.1", "--host", help="Indirizzo del server."),
    port: int = typer.Option(7860, "--port", help="Porta del server."),
    share: bool = typer.Option(False, "--share", help="Crea un link pubblico Gradio temporaneo."),
):
    """Avvia l'interfaccia grafica locale (Gradio)."""
    try:
        from .gui import launch
    except ImportError:
        console.print('[red]Gradio non installato.[/] Esegui:  uv pip install -e ".[gui]"')
        raise typer.Exit(code=1)
    console.print(f"[cyan]Avvio GUI su[/] http://{host}:{port}")
    launch(server_name=host, server_port=port, share=share)


@app.command()
def doctor():
    """Verifica l'ambiente: ffmpeg, stack ASR, device, token HF."""
    table = Table(title=f"local-audio-transcriptor {__version__}")
    table.add_column("Componente")
    table.add_column("Stato")

    # ffmpeg
    try:
        from .ffmpeg_tools import ffmpeg_exe

        table.add_row("ffmpeg", f"[green]ok[/] ({ffmpeg_exe()})")
    except Exception as exc:  # noqa: BLE001
        table.add_row("ffmpeg", f"[red]mancante[/] {exc}")

    # yt-dlp
    try:
        import yt_dlp

        table.add_row("yt-dlp", f"[green]ok[/] ({yt_dlp.version.__version__})")
    except Exception:
        table.add_row("yt-dlp", "[red]mancante[/]")

    # stack ASR + device
    try:
        from .device import detect_device

        import whisperx  # noqa: F401

        dev = detect_device()
        table.add_row("whisperx", "[green]ok[/]")
        table.add_row("device", f"{dev.device} ({dev.compute_type})")
    except Exception:
        table.add_row("whisperx", r'[yellow]non installato[/] (uv pip install -e ".\[asr]")')
        table.add_row("device", "n/d")

    # traduzione (argos-translate)
    try:
        import argostranslate  # noqa: F401

        table.add_row("argos-translate", "[green]ok[/]")
    except Exception:
        table.add_row("argos-translate", '[yellow]non installato[/] (uv pip install -e ".\\[translate]")')

    # HF token
    token = settings.resolved_hf_token()
    table.add_row("HF_TOKEN", "[green]presente[/]" if token else "[yellow]assente[/] (serve per --diarize)")

    # LLM (summarizzazione)
    try:
        import urllib.request

        models_url = settings.llm_base_url.rstrip("/") + "/models"
        with urllib.request.urlopen(models_url, timeout=2):
            table.add_row("LLM", f"[green]raggiungibile[/] ({settings.llm_base_url}, {settings.llm_model})")
    except Exception:
        table.add_row("LLM", f"[yellow]non raggiungibile[/] ({settings.llm_base_url}) — avvia 'ollama serve'")

    console.print(table)


if __name__ == "__main__":
    app()
