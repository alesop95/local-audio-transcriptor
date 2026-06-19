"""Test degli output writer e del formato timestamp (non richiedono lo stack ASR)."""

from pathlib import Path

from transcriptor.outputs import _fmt_ts, write_outputs


def test_fmt_ts_srt_and_vtt():
    assert _fmt_ts(3661.5, comma=True) == "01:01:01,500"
    assert _fmt_ts(3661.5, comma=False) == "01:01:01.500"
    assert _fmt_ts(0, comma=True) == "00:00:00,000"


def test_write_outputs_with_speakers(tmp_path: Path):
    result = {
        "language": "it",
        "segments": [
            {"start": 0.0, "end": 1.5, "text": "Ciao a tutti", "speaker": "SPEAKER_00"},
            {"start": 1.5, "end": 3.0, "text": "Benvenuti", "speaker": "SPEAKER_01"},
        ],
    }
    base = tmp_path / "out" / "001 - lezione"
    written = write_outputs(result, base, ["txt", "srt", "vtt", "json"])
    assert len(written) == 4

    txt = (tmp_path / "out" / "001 - lezione.txt").read_text(encoding="utf-8")
    assert "[SPEAKER_00] Ciao a tutti" in txt

    srt = (tmp_path / "out" / "001 - lezione.srt").read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,500" in srt

    vtt = (tmp_path / "out" / "001 - lezione.vtt").read_text(encoding="utf-8")
    assert vtt.startswith("WEBVTT")


def test_collect_transcripts_orders_and_excludes_summaries(tmp_path):
    from transcriptor.summarize import collect_transcripts

    (tmp_path / "002 - b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "001 - a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "001 - a.summary.md").write_text("s", encoding="utf-8")
    (tmp_path / "003 - c.summary.txt").write_text("s", encoding="utf-8")  # da escludere

    files = collect_transcripts(tmp_path)
    names = [p.name for p in files]
    assert names == ["001 - a.txt", "002 - b.txt"]


def test_fts_search_index_and_query(tmp_path):
    import json

    from transcriptor.search import build_index, search

    doc = {
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "Neural networks changed text to speech."},
            {"start": 2.0, "end": 4.0, "text": "Concatenative synthesis is an old method."},
        ],
    }
    (tmp_path / "001 - lezione.json").write_text(json.dumps(doc), encoding="utf-8")
    db, n = build_index(tmp_path)
    assert n == 2

    hits = search("neural", folder=tmp_path)
    assert len(hits) == 1
    assert "001 - lezione" in hits[0].source
    assert hits[0].start == 0.0
    assert "Neural" in hits[0].text


def test_rag_fts_query_drops_stopwords():
    from transcriptor.rag import _to_fts_query

    q = _to_fts_query("Come funziona il voice cloning?")
    assert '"voice"' in q and '"cloning"' in q
    assert "come" not in q.lower().replace('"', "")


def test_collect_stats(tmp_path):
    import json

    from transcriptor.stats import collect_stats, fmt_duration

    doc = {
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 3.0, "text": "one two three", "speaker": "SPEAKER_00"},
            {"start": 3.0, "end": 65.0, "text": "four five", "speaker": "SPEAKER_01"},
        ],
    }
    (tmp_path / "001 - lezione.json").write_text(json.dumps(doc), encoding="utf-8")
    stats = collect_stats(tmp_path)
    assert len(stats) == 1
    st = stats[0]
    assert st.words == 5
    assert st.segments == 2
    assert st.duration == 65.0
    assert st.speakers == 2
    assert fmt_duration(65.0) == "00:01:05"
