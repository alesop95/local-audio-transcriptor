# local-audio-transcriptor

> Istruzioni di progetto, versionate. Le preferenze personali vivono in `CLAUDE.local.md` (ignorato).

## Cos'e questo progetto

Strumento Python locale per la trascrizione di audio, con archivio su SQLite e comandi di analisi (tra cui una panoramica di durata, parole, lingua e speaker). Dettaglio operativo nel `README.md` e nei sorgenti `.py`.

## Dati sensibili e materiali

La configurazione passa da `.env` (gitignored); il riferimento versionato e `.env.example`, e allo stato attuale non esiste un `.env` reale. Audio di esempio (`.webm`) e database locale (`.db`) sono gestiti dal `.gitignore` del progetto.

## Sviluppo e identita

git locale gia configurato: identita utente `alesop95`, email `alessio.sopranzi.95@gmail.com`, alias SSH `github-personal`, remoto github.com/alesop95/local-audio-transcriptor. Impostato ora anche `core.sshCommand` all'OpenSSH di sistema. Commit e push manuali.

## Standard

Allineato in modo additivo a `.claude/PROJECT-SYSTEM.md`: regole, engine skills (sync-context, git-sync, repo-status, onboard), catalogo `PACKAGES.md`, schede `context` e `memory` scaffold da popolare e ancorabili con sync-context. Il `settings.local.json` esistente e preservato. Pacchetto code-context disponibile per mappare il codice.

Norme caricate su richiesta, una riga per situazione con le parole con cui si presenta, così che il caricamento non dipenda dal ricordare che la norma esista.

- `git worktree list` mostra più di un albero, se ne crea o se ne rimuove uno, si deve decidere da dove leggere la memoria versionata: skill `alberi-di-lavoro`.
- Un recupero web fallisce con 403 o con una pagina di verifica anti-bot, la fonte sta su Reddit o su Discord, serve la trascrizione di un video, si sta per annotare una fonte non letta: skill `fonti-non-recuperabili`.
- Si scrive o si valuta una prova automatica, si chiude un difetto, una verifica manuale smentisce una suite verde, si sta per dichiarare completo un intervento il cui scopo era un effetto misurabile: skill `prove-che-misurano`.
- Si inizializza o si allinea il progetto, oppure cambia il modo in cui si prova e si rilascia, e va deciso come separare test e produzione: skill `separazione-ambienti`.
