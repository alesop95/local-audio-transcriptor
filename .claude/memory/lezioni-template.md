# Lezioni per il template

> Le lezioni nate in questo progetto che valgono oltre il progetto, cioè che passano le due domande della sezione 16 di `.claude/PROJECT-SYSTEM.md`: restano vere tolti i nomi propri, e non sono già nella testa di chi lavora bene. Una voce per lezione, creata con `python .claude/templates/tools/lezioni-template.py nuova` nel giro di lavoro in cui la lezione nasce. Lo stato non si scrive qui: una lezione è recepita quando il template la elenca in `.claude/templates/lezioni-recepite.json`, che arriva con l'allineamento.

Adottato il: 2026-10-20

## L-001 - 2026-10-20 - Un parsing numerico in PowerShell impone la cultura invariante

Uno script che legge un numero dall'uscita di un programma, per esempio la durata di un video da ffprobe, deve convertirlo con la cultura invariante e non con quella di sistema. In locale italiano il punto e' il separatore delle migliaia, quindi 300.012000 viene letto come trecento milioni: la conversione riesce, nessun errore viene sollevato, e il valore sbagliato prosegue. Il difetto non si vede leggendo il codice ne' provando su una macchina in inglese, e si manifesta come un rapporto assurdo a valle. Si scopre solo provando la catena intera sulla macchina vera, ed e' la ragione per cui una soglia calcolata su un numero letto da un programma esterno va provata nei due rami, quello che accetta e quello che rifiuta.
