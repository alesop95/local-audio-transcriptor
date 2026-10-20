#!/usr/bin/env python3
"""check-niente-trascritto.py - impedisce che contenuto trascritto entri nel repository.

Il repository e' pubblico e il materiale trascritto non deve finirci, ne' come file ne'
dentro la documentazione. Le regole di `.gitignore` coprono i formati e le cartelle di
uscita; questo controllo copre il caso che quelle regole non vedono, cioe' un file
tracciato che contiene parlato trascritto: una nota, una scheda di memoria, un esempio
incollato in un README.

Riconosce due impronte. La prima e' il marcatore temporale dei sottotitoli, nella forma
`00:01:02,345`, che nessun testo scritto a mano produce. La seconda e' la stringa di
separazione dei formati di uscita del progetto. Esce con codice 1 se trova qualcosa.

    python tools/check-niente-trascritto.py
    python tools/check-niente-trascritto.py --autotest
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TIMESTAMP = re.compile(r"\b\d{2}:\d{2}:\d{2}[,.]\d{3}\b")
FRECCIA = re.compile(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}")
ESTENSIONI = {".md", ".txt", ".json", ".py", ".ps1", ".sh", ".yml", ".yaml"}
SALTA = ("/.venv/", "/node_modules/", "/.git/")


def impronte(testo: str) -> list[str]:
    trovate = []
    if FRECCIA.search(testo):
        trovate.append("riga di sottotitolo con marcatore di inizio e fine")
    elif len(TIMESTAMP.findall(testo)) >= 3:
        trovate.append("tre o piu' marcatori temporali in formato sottotitolo")
    return trovate


def file_tracciati(radice: Path) -> list[Path]:
    out = subprocess.run(["git", "-C", str(radice), "ls-files"],
                         capture_output=True, text=True, check=True)
    percorsi = []
    for riga in out.stdout.splitlines():
        if not riga.strip():
            continue
        if any(s.strip("/") in riga.split("/") for s in SALTA):
            continue
        p = radice / riga
        if p.suffix.lower() in ESTENSIONI and p.is_file():
            percorsi.append(p)
    return percorsi


def leggi_eccezioni(percorso: Path) -> set[str]:
    """Percorsi dichiarati innocui, uno per riga, con il motivo dopo un cancelletto."""
    if not percorso.is_file():
        return set()
    fuori = set()
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        testo = riga.split("#", 1)[0].strip()
        if testo:
            fuori.add(testo.replace("\\", "/"))
    return fuori


def controlla(radice: Path, eccezioni: set[str] | None = None) -> list[tuple[Path, str]]:
    eccezioni = eccezioni or set()
    riscontri = []
    for p in file_tracciati(radice):
        if p.name == Path(__file__).name:
            continue
        if p.relative_to(radice).as_posix() in eccezioni:
            continue
        try:
            testo = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for motivo in impronte(testo):
            riscontri.append((p, motivo))
    return riscontri


def autotest() -> int:
    fallimenti = []
    pulito = "Questa e' prosa normale, con un orario come 12:30 e una durata di 2h46."
    if impronte(pulito):
        fallimenti.append("ha segnalato un testo pulito")
    sporco = "29\n00:04:44,850 --> 00:04:59,700\nquindi quello che erano i concerti"
    if not impronte(sporco):
        fallimenti.append("non ha visto una riga di sottotitolo")
    tre = "00:00:01,000 poi 00:00:02,500 poi 00:00:03,900"
    if not impronte(tre):
        fallimenti.append("non ha visto tre marcatori temporali")
    with tempfile.TemporaryDirectory() as tmp:
        elenco = Path(tmp) / "ecc.txt"
        righe = ["tests/test_outputs.py  # motivo", "# commento", "", ""]
        elenco.write_text("\n".join(righe), encoding="utf-8")
        letto = leggi_eccezioni(elenco)
        if letto != {"tests/test_outputs.py"}:
            fallimenti.append(f"elenco delle eccezioni letto male: {letto}")
    for riga in fallimenti:
        print(f"FALLITO: {riga}")
    if fallimenti:
        return 1
    print("autotest: 4 controlli superati (prosa pulita, riga di sottotitolo,")
    print("  marcatori ripetuti, lettura dell'elenco delle eccezioni).")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Cerca contenuto trascritto nei file tracciati.")
    p.add_argument("--radice", default=".", help="Radice del repository (default: cartella corrente).")
    p.add_argument("--eccezioni", default="tools/trascritto-eccezioni.txt",
                   help="Elenco dei percorsi dichiarati innocui, con il motivo.")
    p.add_argument("--autotest", action="store_true", help="Esegue la prova integrata ed esce.")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    radice = Path(a.radice).resolve()
    eccezioni = leggi_eccezioni(radice / a.eccezioni)
    riscontri = controlla(radice, eccezioni)
    for percorso, motivo in riscontri:
        print(f"{percorso}: {motivo}", file=sys.stderr)
    if riscontri:
        print(f"{len(riscontri)} riscontri: contenuto trascritto in file tracciati.", file=sys.stderr)
        return 1
    print("nessun contenuto trascritto nei file tracciati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
