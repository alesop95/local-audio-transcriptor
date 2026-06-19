"""Interfaccia grafica locale (Gradio) per il tool di trascrizione.

Riusa la stessa pipeline della CLI. Avvio:  transcribe gui
"""

from __future__ import annotations

from pathlib import Path

from .config import settings

LANGUAGES = ["auto", "it", "en", "es", "fr", "de", "pt", "nl"]
DEVICES = ["auto", "cpu", "cuda"]
MODELS = ["tiny", "base", "small", "medium", "large-v3"]


def _opts(model, language, device, formats, diarize, summarize, out_dir):
    from .pipeline import TranscribeOptions

    fmts = tuple(f.strip().lower() for f in formats.split(",") if f.strip())
    if summarize and "txt" not in fmts:
        fmts = fmts + ("txt",)
    return TranscribeOptions(
        model=model,
        language=None if language in (None, "auto") else language,
        device=None if device in (None, "auto") else device,
        batch_size=settings.batch_size,
        formats=fmts,
        diarize=diarize,
        hf_token=settings.resolved_hf_token(),
        out_dir=Path(out_dir),
        summarize=summarize,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        llm_api_key=settings.llm_api_key,
    )


def _run(items, opts):
    """Trascrive gli items e ritorna (testo_preview, lista_file)."""
    from .pipeline import build_transcriber, transcribe_item
    from .summarize import LLMError, summarize_file

    if not items:
        return "Nessun elemento da trascrivere.", []

    transcriber, dev = build_transcriber(opts)
    preview_parts: list[str] = [f"Device: {dev.device} ({dev.compute_type})\n"]
    files: list[str] = []

    for n, item in enumerate(items, start=1):
        res = transcribe_item(item, opts, transcriber=transcriber)
        files.extend(str(p) for p in res.written)
        txt = next((p for p in res.written if p.suffix == ".txt"), None)
        if txt:
            content = Path(txt).read_text(encoding="utf-8")
            preview_parts.append(f"### ({n}) {item.title}  [lingua: {res.language or '?'}]\n{content}")
        if opts.summarize and txt:
            try:
                md = summarize_file(
                    txt, base_url=opts.llm_base_url, model=opts.llm_model, api_key=opts.llm_api_key
                )
                files.append(str(md))
            except LLMError as exc:
                preview_parts.append(f"_Sintesi saltata: {exc}_")

    return "\n\n".join(preview_parts), files


def _transcribe_file(audio, model, language, device, formats, diarize, summarize, out_dir):
    from .sources.local import resolve_local

    if not audio:
        return "Carica un file audio/video.", []
    opts = _opts(model, language, device, formats, diarize, summarize, out_dir)
    return _run([resolve_local(audio)], opts)


def _transcribe_youtube(url, model, language, device, formats, diarize, summarize, out_dir):
    from .sources import youtube as yt

    if not url:
        return "Inserisci un URL YouTube.", []
    opts = _opts(model, language, device, formats, diarize, summarize, out_dir)
    try:
        items = yt.fetch(url, settings.work_dir, archive=True)
    except Exception as exc:  # noqa: BLE001
        return f"Download fallito: {exc}", []
    return _run(items, opts)


def _transcribe_playlist(url, items_range, model, language, device, formats, diarize, summarize, out_dir):
    from .sources import youtube as yt

    if not url:
        return "Inserisci un URL playlist.", []
    opts = _opts(model, language, device, formats, diarize, summarize, out_dir)
    try:
        media = yt.fetch(url, settings.work_dir, playlist_items=items_range or None, archive=True)
    except Exception as exc:  # noqa: BLE001
        return f"Download fallito: {exc}", []
    return _run(media, opts)


def build_demo():
    import gradio as gr

    with gr.Blocks(title="Local Audio Transcriptor") as demo:
        gr.Markdown("# 🎙️ Local Audio Transcriptor\nTrascrizione locale da file o YouTube, con diarizzazione e sintesi LLM opzionali.")

        with gr.Accordion("Opzioni", open=True):
            with gr.Row():
                model = gr.Dropdown(MODELS, value=settings.model, label="Modello")
                language = gr.Dropdown(LANGUAGES, value="auto", label="Lingua")
                device = gr.Dropdown(DEVICES, value="auto", label="Device")
            with gr.Row():
                formats = gr.Textbox(value="txt,srt,vtt,json", label="Formati (csv)")
                out_dir = gr.Textbox(value="out", label="Cartella output")
            with gr.Row():
                diarize = gr.Checkbox(value=False, label="Diarizzazione (chi parla) — richiede HF_TOKEN")
                summarize = gr.Checkbox(value=False, label="Sintesi LLM (richiede Ollama)")

        with gr.Tab("File locale"):
            audio = gr.File(label="Audio/Video", type="filepath")
            btn_f = gr.Button("Trascrivi", variant="primary")
        with gr.Tab("YouTube (video)"):
            yt_url = gr.Textbox(label="URL video")
            btn_y = gr.Button("Scarica e trascrivi", variant="primary")
        with gr.Tab("YouTube (playlist)"):
            pl_url = gr.Textbox(label="URL playlist")
            pl_items = gr.Textbox(label="Range items (es. 1-3), vuoto = tutti")
            btn_p = gr.Button("Scarica e trascrivi", variant="primary")

        out_text = gr.Markdown(label="Trascrizione")
        out_files = gr.File(label="File generati", file_count="multiple")

        common = [model, language, device, formats, diarize, summarize, out_dir]
        btn_f.click(_transcribe_file, [audio, *common], [out_text, out_files])
        btn_y.click(_transcribe_youtube, [yt_url, *common], [out_text, out_files])
        btn_p.click(_transcribe_playlist, [pl_url, pl_items, *common], [out_text, out_files])

    return demo


def launch(server_name: str = "127.0.0.1", server_port: int = 7860, share: bool = False):
    demo = build_demo()
    demo.launch(server_name=server_name, server_port=server_port, share=share, inbrowser=True)
