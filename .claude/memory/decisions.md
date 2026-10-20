# Registro delle decisioni architetturali

> Convenzione ADR-lite, append-only. Ogni decisione architetturale non ovvia entra come voce numerata con data, stato, contesto, decisione, motivazione e conseguenze. Una decisione non si cancella e non si riscrive: quando viene superata, si aggiunge una nuova voce che dichiara di superare la precedente e ne cita il numero. Le inferenze non confermate si marcano come da verificare e si promuovono a decisione solo quando una fonte le conferma.

## ADR-001 — Adozione del sistema di progetto portabile

Data: <YYYY-MM-DD> Stato: accettata Contesto: il progetto necessita di uno stato interamente recuperabile da un clone e di documentazione che resti allineata al codice senza rilettura integrale a ogni sessione. Decisione: adottare il sistema descritto in `.claude/PROJECT-SYSTEM.md`, con motore di riconciliazione ancorato ai commit e doppio livello documentale tracciato/ignorato. Motivazione: persistenza strutturale su disco indipendente dalla sessione di chat, e controllo umano sul versionamento. Conseguenze: ogni passo significativo aggiorna schede, `last-verified-commit`, snapshot e work-log; commit e push restano manuali.

## ADR-003 — Superata ADR-002: la sintesi torna sull'endpoint di rete, ora che la scheda è verificata

Data: 2026-10-20 Stato: accettata, supera ADR-002 Contesto: ADR-002 sceglieva il modello locale perché l'endpoint di rete, pur stando su una macchina con scheda grafica, serviva sul processore per un difetto di avvio, e dichiarava di doversi rivedere quando l'accelerazione fosse stata verificata. La correzione è stata applicata il 2026-10-20 e la verifica c'è: stesso modello e stesso prompt, da 1,91 a 43,99 parole al secondo, caricamento da 105,89 a 3,99 secondi, memoria video occupata da 0,00 a 10,12 GB. Decisione: tornare all'endpoint di rete come scelta predefinita per `summarize`, `digest` e `ask`, tenendo il motore locale a esperti come riserva per quando la macchina non è raggiungibile o la sua scheda è occupata da un altro progetto. Motivazione: un fattore ventitré non si recupera con nessuna scelta di modello in CPU, e la risorsa è condivisa ma non esclusiva. Conseguenze: la configurazione resta quella già presente, perché puntava già a quell'endpoint; il modello consigliato diventa un modello denso da quattordici miliardi di parametri, che su scheda batte un modello a esperti, rovesciando la classifica valida in CPU; e accanto a ogni misura si continua a registrare se l'inferenza era su scheda o su processore, che è il presidio nato proprio da questo caso. Questa decisione si rivede se una misura futura mostra di nuovo memoria video a zero, che è il sintomo da cui tutto è partito.

## ADR-002 — La sintesi va a CPU per prima, sul modello locale, e l'endpoint di rete resta un'opzione

Data: 2026-10-20 Stato: accettata Contesto: la metà linguistica del progetto, cioè `summarize`, `digest` e `ask`, parla con un endpoint compatibile con quello di OpenAI, configurabile e non vincolato a `localhost`. Sulla rete esiste una macchina con scheda grafica che espone un servizio di inferenza, ma il 2026-10-20 si è accertato che quel servizio serve sul processore per un difetto di avvio, a 1,91 parole al secondo su un modello denso da 14,8 miliardi di parametri. Sulla stessa macchina di questo progetto, dentro WSL, esiste già un motore a esperti con un modello misurato a 2,81 parole al secondo e con correttezza piena su un banco di classificazione. Decisione: adottare il modello locale come scelta predefinita per la sintesi, e tenere l'endpoint di rete come alternativa da attivare quando la sua accelerazione è verificata, non presunta. Motivazione: a parità di velocità la via locale non dipende dalla rete, non contende una risorsa condivisa con altri progetti e non espone il contenuto delle trascrizioni a una macchina terza; e oggi la via locale è perfino più veloce. Conseguenze: la configurazione predefinita punta al motore locale; chi vuole l'endpoint di rete lo passa esplicitamente con `--llm-url`; e accanto a ogni misura di velocità si registra se l'inferenza è avvenuta su scheda o su processore, perché senza quel dato la misura non è ripetibile. Questa decisione si rivede se e quando la scheda della macchina in rete risulta davvero in uso, nel qual caso il confronto va rifatto da capo perché su scheda la classifica fra modelli densi e a esperti si rovescia.

<!-- ADR-002 — <titolo>
Data: <YYYY-MM-DD>
Stato: <proposta / accettata / superata da ADR-NNN>
Contesto: ...
Decisione: ...
Motivazione: ...
Conseguenze: ... -->
