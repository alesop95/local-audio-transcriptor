#!/usr/bin/env python3
"""sovrascrivi.py - rimuove un file sovrascrivendone prima il contenuto.

Serve quando il materiale trascritto non deve restare recuperabile sul disco dopo la
trascrizione. Una rimozione normale scollega il file e lascia i blocchi dov'erano; qui i
blocchi vengono riscritti con byte casuali, il file viene troncato, rinominato e infine
rimosso, cosi' che nemmeno il nome resti nella directory.

Limite dichiarato, che nessuna implementazione in spazio utente puo' superare: su un disco
a stato solido il controllore rimappa i blocchi e la scrittura non cade necessariamente
dove stava il dato; su NTFS il journal, le copie shadow e i file residenti nella MFT
possono conservare frammenti. La sovrascrittura riduce la recuperabilita', non la azzera.
Dove serve una garanzia, la strada e' la cifratura del volume prima della scrittura.

Uso tipico, con la radice che delimita cio' che puo' essere toccato:
    python tools/sovrascrivi.py --radice "X:/corpus" --si "X:/corpus/registrazione.mp4"
    python tools/sovrascrivi.py --autotest
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import tempfile
from pathlib import Path

BLOCCO = 1 << 20  # un mebibyte per scrittura


class RifiutoSicurezza(Exception):
    """Il file non si tocca: la ragione e' nel messaggio."""


def _controlla(percorso: Path, radice: Path) -> Path:
    if percorso.is_symlink():
        raise RifiutoSicurezza(f"e' un collegamento simbolico: {percorso}")
    if not percorso.exists():
        raise RifiutoSicurezza(f"non esiste: {percorso}")
    if not percorso.is_file():
        raise RifiutoSicurezza(f"non e' un file regolare: {percorso}")
    vero = percorso.resolve(strict=True)
    base = radice.resolve(strict=True)
    if base not in vero.parents:
        raise RifiutoSicurezza(f"fuori dalla radice consentita {base}: {vero}")
    return vero


def sovrascrivi(percorso: Path, radice: Path, passate: int = 1, agisci: bool = False) -> dict:
    """Sovrascrive e rimuove `percorso`. Senza `agisci` non tocca nulla e descrive soltanto."""
    vero = _controlla(percorso, radice)
    dimensione = vero.stat().st_size
    esito = {"file": str(vero), "byte": dimensione, "passate": passate, "eseguito": agisci}
    if not agisci:
        esito["nota"] = "prova a vuoto: nessuna scrittura"
        return esito

    with open(vero, "r+b", buffering=0) as f:
        for _ in range(passate):
            f.seek(0)
            restanti = dimensione
            while restanti > 0:
                quanti = BLOCCO if restanti > BLOCCO else restanti
                f.write(secrets.token_bytes(quanti))
                restanti -= quanti
            f.flush()
            os.fsync(f.fileno())
        f.seek(0)
        f.truncate(0)
        f.flush()
        os.fsync(f.fileno())

    provvisorio = vero.with_name("zz" + secrets.token_hex(8))
    os.replace(vero, provvisorio)
    provvisorio.unlink()
    esito["nota"] = "sovrascritto, troncato, rinominato e rimosso"
    return esito


def autotest() -> int:
    """Prova i due rami che contano: quello che agisce e quelli che rifiutano."""
    fallimenti = []
    with tempfile.TemporaryDirectory() as tmp:
        radice = Path(tmp)
        bersaglio = radice / "bersaglio.bin"
        contenuto = b"PAROLA-SEGRETA-" * 5000
        bersaglio.write_bytes(contenuto)
        vicino = radice / "vicino.bin"
        vicino.write_bytes(b"questo resta")

        esito = sovrascrivi(bersaglio, radice, passate=1, agisci=False)
        if bersaglio.exists() is False or esito["eseguito"]:
            fallimenti.append("la prova a vuoto ha toccato il file")

        sovrascrivi(bersaglio, radice, passate=2, agisci=True)
        if bersaglio.exists():
            fallimenti.append("il file esiste ancora dopo la rimozione")
        if vicino.read_bytes() != b"questo resta":
            fallimenti.append("un file vicino e' stato alterato")
        residui = [p.name for p in radice.iterdir() if p.name != "vicino.bin"]
        if residui:
            fallimenti.append(f"residui nella cartella: {residui}")

        fuori = Path(tempfile.gettempdir()) / f"fuori-{secrets.token_hex(4)}.bin"
        fuori.write_bytes(b"x")
        try:
            sovrascrivi(fuori, radice, agisci=True)
            fallimenti.append("ha accettato un file fuori dalla radice")
        except RifiutoSicurezza:
            pass
        finally:
            fuori.unlink(missing_ok=True)

        cartella = radice / "cartella"
        cartella.mkdir()
        try:
            sovrascrivi(cartella, radice, agisci=True)
            fallimenti.append("ha accettato una cartella")
        except RifiutoSicurezza:
            pass

        mancante = radice / "non-esiste.bin"
        try:
            sovrascrivi(mancante, radice, agisci=True)
            fallimenti.append("ha accettato un file inesistente")
        except RifiutoSicurezza:
            pass

    for riga in fallimenti:
        print(f"FALLITO: {riga}")
    if fallimenti:
        return 1
    print("autotest: 6 controlli superati (prova a vuoto, rimozione, vicino intatto,")
    print("  nessun residuo, rifiuto fuori radice, rifiuto cartella e file mancante).")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sovrascrive e rimuove un file.")
    p.add_argument("file", nargs="*", help="File da sovrascrivere e rimuovere.")
    p.add_argument("--radice", help="Cartella che delimita cio' che si puo' toccare.")
    p.add_argument("--passate", type=int, default=1, help="Quante volte riscrivere (default 1).")
    p.add_argument("--si", action="store_true", help="Agisce davvero; senza, e' una prova a vuoto.")
    p.add_argument("--autotest", action="store_true", help="Esegue la prova integrata ed esce.")
    a = p.parse_args(argv)

    if a.autotest:
        return autotest()
    if not a.file or not a.radice:
        p.error("servono almeno un file e --radice (oppure --autotest)")
    if a.passate < 1:
        p.error("--passate deve essere almeno 1")

    radice = Path(a.radice)
    usciti = 0
    for nome in a.file:
        try:
            esito = sovrascrivi(Path(nome), radice, a.passate, a.si)
            print(f"{esito['nota']}: {esito['file']} ({esito['byte']} byte)")
        except RifiutoSicurezza as exc:
            print(f"RIFIUTATO: {exc}", file=sys.stderr)
            usciti = 2
        except OSError as exc:
            print(f"ERRORE: {nome}: {exc}", file=sys.stderr)
            usciti = 3
    return usciti


if __name__ == "__main__":
    raise SystemExit(main())
