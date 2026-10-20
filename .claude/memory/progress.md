# Work-log

> Append-only, in ordine cronologico inverso (la voce più recente in alto). Ogni passo significativo di codice e ogni intervento manuale rilevante lascia una voce con data, file toccati, motivo e commit di riferimento. Qui confluisce anche il log di riconciliazione dei documenti `.docx`, con il nome del documento sorgente e l'esito, così la data di allineamento sopravvive a un clone.

## 2026-10-20 — Lo strumento di corsa entra nel progetto, perché stava solo sul disco che si stacca

Commit: nessuno. File toccati: `tools/Trascrivi-Cartella.ps1` e questo. Motivo: lo strumento che porta tutta la logica di ripresa, di verifica e di cancellazione verificata esisteva in una copia sola, dentro la cartella del corpus, su un disco esterno che va scollegato. Se quel disco si guasta, con il materiale se ne va anche lo strumento.

La copia versionata è generica e non nomina nessun corpus: la radice è obbligatoria e non ha valore predefinito, le sottocartelle di sorgente e di uscita hanno nomi neutri, e i comandi esterni si cercano nel percorso invece di essere inchiodati a un'installazione. Porta tutto ciò che è stato costruito oggi: esclusione dei file personali letta da un elenco e applicata prima di aprirli, ripresa che rivaluta la completezza invece di fidarsi dell'esistenza del file, verifica di copertura dei sottotitoli sulla durata del video prima di autorizzare la cancellazione, scelta obbligatoria fra rimozione normale e sovrascrittura, controllo della presenza del disco prima di ogni elemento e scrittura protetta del registro.

Verificato dopo la copia: nessun riferimento al corpus resta nel file, lo strumento si avvia su una radice qualunque, e i due controlli del progetto, quello sul contenuto trascritto nei file tracciati e quello sul formato dei comandi, passano puliti.

Nota sul versionamento di questo giro: l'albero di lavoro contiene anche modifiche di un allineamento dal template che non appartengono a questa sessione, quindi il commit va fatto nominando i file e non con `git add -A`, al contrario di quello precedente.

## 2026-10-20 — Lo strumento regge la sparizione del disco, e la ripresa non si fida dei file

Commit: nessuno. File toccati: questo e lo strumento di corsa nella cartella del corso. Motivo: il proprietario deve staccare il disco esterno alle 18:00 mentre la corsa è in esecuzione, e la ripresa deve riprendere esattamente da dove si era fermata.

C'erano due difetti, e il secondo era il più grave perché silenzioso. Il primo: con il disco staccato, lo strumento moriva con un errore di PowerShell illeggibile, perché sia la lettura dei video sia la scrittura del registro stanno su quel disco. Il secondo: la ripresa decideva che cosa fosse già fatto guardando se il file di testo esisteva, e un file di testo scritto a metà perché il disco è sparito durante la scrittura esiste eccome. Alla ripresa quella lezione sarebbe stata saltata per sempre, con una trascrizione monca che nessuno avrebbe più guardato.

Le correzioni sono tre. Prima di ogni lezione lo strumento controlla che la cartella delle registrazioni risponda ancora e, se non risponde, si ferma con un messaggio in chiaro invece di un errore. La scrittura del registro è protetta, così la mancanza del disco non diventa un'eccezione. E soprattutto la ripresa non si fida più dell'esistenza del file: rivaluta la completezza con lo stesso controllo usato per decidere la cancellazione del video, cioè testo sopra la soglia di sanità, sottotitoli presenti e copertura dell'ultimo sottotitolo almeno al 97 per cento della durata; se non passa, la lezione torna nell'elenco da fare con scritto accanto il perché.

La prova è stata fatta simulando il caso: un file di testo posticcio di duecento righe, senza sottotitoli accanto, nella cartella di destinazione della prima lezione. Lo strumento lo ha riconosciuto come incompleto, lo ha contato fra quelli da rifare e lo ha elencato con la ragione «manca il .srt» invece di saltarlo. Rimosso il posticcio, il piano torna a trenta da fare e zero da rifare.

Resta un consiglio operativo che nessun codice può imporre: prima di staccare il disco conviene fermare la corsa con Ctrl+C, così nessun file è a metà scrittura. Se ci si dimentica non si perde niente, perché la ripresa rifà da capo la lezione interrotta; si perde solo il tempo di quella lezione.

## 2026-10-20 — Tre chiusure prima di partire: locale, sovrascrittura, versionamento

Commit: nessuno. File toccati: `tools/sovrascrivi.py`, `tools/check-niente-trascritto.py`, `tools/trascritto-eccezioni.txt`, `.gitignore`, `.claude/memory/lezioni-template.md`, questo, e lo strumento di corsa nella cartella del corso. **Template:** L-001. Motivo: il proprietario chiede di chiudere tre questioni aperte prima di avviare la trascrizione, senza lasciare pezzi.

Primo, il difetto di lingua non riguarda questo progetto e la verifica lo dice invece di presumerlo: negli script PowerShell del progetto non esiste nessuna conversione numerica, e il codice Python usa `float()`, che non dipende dalla lingua del sistema. Il difetto stava solo nello script di corsa del corso, dove è stato corretto. Resta come lezione per il template, registrata come L-001.

Secondo, la sovrascrittura esiste ed è provata. `tools/sovrascrivi.py` riscrive i byte del file con dati casuali, lo tronca, lo rinomina e lo rimuove, così che nemmeno il nome resti nella cartella; rifiuta i collegamenti simbolici, le cartelle, i file inesistenti e tutto ciò che sta fuori da una radice dichiarata, e senza `--si` non tocca niente. Il suo `--autotest` supera sei controlli, fra cui che un file vicino resti intatto e che non restino residui. Lo strumento di corsa lo richiama al posto della rimozione normale, e soprattutto non parte se non si è scelto: con `-CancellaVideo` senza `-Sovrascrittura si|no` si ferma subito, perché la scelta si fa prima e non a corsa avviata. La catena intera è stata provata su un campione reale dentro la cartella del corso, con esito «completa, copertura 99,7 per cento; video sovrascritto e rimosso», e gli artefatti della prova sono stati tolti.

Il limite dello strumento è scritto dentro lo strumento e non va taciuto: su un disco a stato solido il controllore rimappa i blocchi e la riscrittura non cade necessariamente dove stava il dato, e su NTFS journal, copie shadow e file residenti nella tabella dei file possono conservare frammenti. La sovrascrittura riduce la recuperabilità, non la azzera; la garanzia vera è cifrare il volume prima di scriverci.

Terzo, il versionamento. Le regole di esclusione erano strette: coprivano le cartelle di uscita e alcuni formati audio, non i video, non i database, non le note di sintesi. Ora coprono tutti i formati audio e video usati, i sottotitoli nelle tre forme, i file di sintesi e di digest e i database, e la verifica è stata fatta con `git check-ignore` su quattro casi. Resta deliberatamente fuori `*.txt`, perché il progetto traccia file di testo dei modelli: le trascrizioni in testo semplice sono coperte dalla cartella di uscita, che è ignorata.

Perché quella deliberazione non diventi un buco, esiste ora `tools/check-niente-trascritto.py`, che cerca nei file tracciati l'impronta del parlato trascritto, cioè la riga di sottotitolo con inizio e fine oppure tre o più marcatori temporali, e fallisce se la trova. Alla prima corsa ha trovato un caso, `tests/test_outputs.py`, che è un falso positivo legittimo perché i marcatori lì sono costruiti a mano per provare il formato: è stato messo in `tools/trascritto-eccezioni.txt` con il motivo scritto accanto, non silenziato nel codice. Sul repository il controllo ora passa pulito.

Resta un lavoro per il proprietario che il controllo non può fare da sé: la citazione di parlato che avevo scritto nel work-log sta ancora nei tre commit più recenti, quindi la storia pubblica non è pulita e va riscritta come già fatto una volta.

## 2026-10-20 — Cancellazione automatica dei video dopo verifica, provata su un caso reale

Commit: nessuno. File toccati: questo e lo strumento di corsa nella cartella del corso. Motivo: richiesta del proprietario di liberare spazio cancellando ogni registrazione appena il suo contenuto è trascritto, con il vincolo che nessuna traccia esca dalla cartella del corso.

Lo strumento cancella il video solo dopo quattro condizioni, tutte necessarie: esito zero del comando, esistenza del testo con dimensione sopra una soglia di sanità, esistenza dei sottotitoli, e copertura dell'ultimo sottotitolo pari almeno al 97 per cento della durata del video letta con ffprobe. Se una qualunque non regge, il video resta e il registro scrive perché. In particolare, se la durata del video non è leggibile la trascrizione non si dichiara completa: nel dubbio si conserva.

La prova è stata fatta su materiale reale dentro la cartella del corso, e ha trovato due cose. Primo, il percorso che rifiuta funziona: su un campione di sessanta secondi il testo risultava sotto la soglia di sanità e il video è stato conservato. Secondo, e questo è il motivo per cui la prova andava fatta davvero, c'era un difetto che nessuna lettura del codice avrebbe mostrato: ffprobe scrive la durata con il punto decimale, e in locale italiano il punto è il separatore delle migliaia, quindi «300.012000» veniva letto come trecento milioni e la copertura risultava dello zero per cento. L'effetto era conservativo, cioè nessun video sarebbe mai stato cancellato, ma la causa è la stessa che in un altro verso produrrebbe una cancellazione sbagliata. Corretto imponendo la cultura invariante nella conversione. Dopo la correzione, su un campione di cinque minuti, la copertura misurata è 99,7 per cento e il video è stato rimosso: entrambi i rami sono quindi provati, quello che accetta e quello che rifiuta. Gli artefatti della prova sono stati rimossi.

Sul vincolo delle tracce, quattro fatti verificati e non dedotti. L'audio non viene mai scritto su disco: `src/transcriptor/audio.py` lo decodifica con ffmpeg e lo legge da una pipe come array in memoria. Le uscite vanno solo nella cartella del corso. Nessuna chiamata raggiunge la macchina di inferenza, perché il ramo della sintesi ritorna prima di importare il modulo che parla con il modello. E sono stati rimossi i due residui prodotti da questa sessione fuori da quella cartella, cioè il campione audio con le sue trascrizioni nello scratchpad e le due citazioni di parlato finite nel work-log, che è tracciato in un repository pubblico.

Resta un fatto tecnico da sapere e non è una riserva sul lavoro: la cancellazione di un file lo scollega, non sovrascrive i blocchi. Se il requisito fosse la cancellazione sicura servirebbe uno strumento di sovrascrittura, che è un'altra cosa e non è stata chiesta.

## 2026-10-20 — Conferma indipendente dal progetto di verifica qualità, e un limite utile all'invalidazione

Commit: nessuno. File toccati: questo e la scheda del progetto di rete. Motivo: il progetto di verifica qualità ha risposto all'avviso con una misura propria e con un dato che corregge in meglio ciò che avevamo scritto.

La loro misura, presa dal loro punto e non dal nostro, concorda: 10,12 GB di memoria video occupata e 47,2 token al secondo alle 11:05, contro 0 GB e circa 2,5 token al secondo alle 10:20. I nostri 43,99 contro 1,91 sono coerenti, e la differenza fra 47,2 e 43,99 si spiega con prompt e condizioni diverse. La riparazione regge da due punti di osservazione indipendenti, che è più di quanto dicesse la nostra misura sola.

Il dato che corregge noi è questo: a temperatura zero e con input identico la risposta del modello è la stessa sulla scheda e sul processore, verificato su undici frasi di una coppia di lingue con esito, severità e tipo di problema identici nelle due condizioni. Ne segue che delle misure prese nella finestra del guasto si butta il tempo e non il giudizio. La formulazione che avevo scritto nella scheda del progetto di rete, cioè che ogni decisione presa su quei numeri andasse ricontrollata, era più larga del vero: è stata ristretta alle sole misure di durata e di costo, con la distinzione scritta per esteso perché vale per ogni guasto che degradi la prestazione senza toccare il risultato.

Un dato operativo che spiega una cosa osservata durante la diagnosi: quel progetto chiedeva una permanenza del modello di trenta minuti, il che teneva 10,12 GB di memoria video occupati per mezz'ora dopo ogni loro lavoro, ed è anche la ragione delle connessioni attive che vedevo dall'esterno. L'hanno portata a cinque minuti e la inviano esplicitamente a ogni richiesta invece di lasciarla al valore predefinito del servizio condiviso.

Alla loro domanda sul riavvio è stato risposto che non ne è pianificato nessuno e che la decisione è di non forzarlo, quindi non hanno finestre da evitare ma nemmeno una data in cui il difetto verrebbe scoperto; e che il presidio migliore è quello che hanno già messo nel banco, cioè la memoria video a zero su un modello residente, perché non dipende dal sapere quando qualcuno ha riavviato.

## 2026-10-20 — Consegnati i tre avvisi, e garanzia verificata sulla trascrizione

Commit: nessuno. File toccati: questo e una scheda nel progetto gemello che legge libri. Motivo: chiusura della sessione, con la consegna di quanto appreso agli altri progetti e la garanzia richiesta sul vincolo delle tracce.

Le tre consegne sono fatte e sono di tre forme diverse, perché diverse erano le situazioni. Il progetto di rete aveva già assorbito da sé il documento scritto stamattina: il suo indice lo elenca e ne è nata una decisione numerata sul monitoraggio che deve guardare la prestazione e non la sola raggiungibilità, quindi lì non è stato aggiunto altro. Al progetto di verifica qualità, che aveva una sessione viva, l'avviso è stato mandato come messaggio fra sessioni, con il rimando alla scheda scritta stamattina. Al progetto gemello che legge libri è stata scritta una scheda nuova sulla contesa della memoria video, perché la riparazione di oggi cambia le condizioni in cui il suo servizio isolato parte: la scheda ha circa 16 GB, un modello denso da quattordici miliardi ne occupa 10,12 e il servizio condiviso lo tiene residente cinque minuti, quindi due modelli di quella taglia non coesistono.

La garanzia chiesta sul vincolo delle tracce è verificata nel codice e non per ragionamento: in `src/transcriptor/cli.py` il ramo della sintesi comincia con un ritorno anticipato se l'opzione non è stata chiesta, e il modulo che parla con il modello viene importato soltanto dopo quel ritorno. Lo strumento di corsa non passa mai quell'opzione e non passa nessun indirizzo di endpoint. Ne segue che durante la trascrizione nessun byte raggiunge la macchina con la scheda, e la garanzia vale per costruzione e non per configurazione. L'unico comando del progetto che contatta quell'endpoint senza chiederlo è la diagnostica di ambiente, che la corsa non esegue.

## 2026-10-20 — Il vincolo delle zero tracce si attua riusando uno strumento che esiste già

Commit: nessuno. File toccati: questo. Motivo: correzione a quanto scritto nella voce precedente, dove avevo concluso che replicare l'isolamento del progetto gemello fosse lavoro vero e che la via praticabile fosse rinunciare alla scheda. Lo strumento è parametrizzato e riusabile, quindi la conclusione era sbagliata.

Lo strumento del progetto gemello, prima di avviare il modello, legge quattro proprietà sul processo vivo e fallisce se una non regge: `memory.swap.max` del proprio cgroup uguale a zero, `memory.swap.current` uguale a zero, un inibitore di sospensione di tipo blocco tenuto da sé e non ereditato, e la cartella di lavoro su tmpfs. Confina poi il processo con Landlock e gli assegna `HOME` e `TMPDIR` in memoria, e viene eseguito attraverso SSH senza essere scritto sul disco dell'host. Accetta `--models` e `--port`, quindi non ha niente di specifico di quel progetto.

Con `memory.swap.max` a zero il kernel non può scrivere su disco una pagina di quel processo, che è esattamente il vettore da chiudere. Si aggiunge un secondo vettore rilevato oggi e prima non collegato: sulla macchina sono abilitati i servizi di sospensione e ibernazione del fornitore della scheda, che in sospensione copiano su disco il contenuto della memoria video, dove risiede il modello; l'inibitore di sonno serve a quello.

Per usarlo sul materiale del corpus mancano tre cose piccole: una porta diversa da quella del progetto gemello, un tunnel SSH perché l'istanza isolata si lega a `127.0.0.1` sull'host e non è raggiungibile dalla rete, e un involucro che avvii, usi, spenga e rilegga la prova dello spegnimento. Non serve ora: la trascrizione non invia niente, e questo pezzo entra in gioco alla fase di sintesi, dove il motore locale a esperti resta come ripiego.

Residuo che nessun impianto cancella e che va detto: la metadata delle richieste nel giornale del servizio condiviso, cioè data, indirizzo del chiamante, percorso ed esito. Il contenuto dei prompt invece non è registrato, verificato oggi cercando la frase esatta delle prove. L'istanza isolata non passa dal servizio condiviso e quindi non lascia nemmeno quella.

## 2026-10-20 — Tracce sulla macchina di inferenza: che cosa resta davvero, verificato

Commit: nessuno. File toccati: questo. Motivo: il proprietario pone come vincolo che il materiale inviato da fuori non lasci artefatti sulla macchina con la scheda, a prescindere dalla porta usata, come già stabilito per il progetto gemello che legge libri.

Primo fatto, ed è quello che sposta la domanda: la trascrizione non invia niente a quella macchina. WhisperX gira sulla CPU locale e legge i video dal disco J, quindi nella fase in corso il vincolo è soddisfatto per costruzione e non per configurazione. Il rischio esiste solo nella fase successiva, la sintesi, che manda il testo delle trascrizioni a un modello.

Secondo fatto, verificato sul giornale del servizio: il contenuto dei prompt non viene registrato. Una ricerca della frase esatta usata nelle prove di oggi non trova nessuna occorrenza. Resta invece la metadata di ogni richiesta, cioè data, indirizzo del chiamante, verbo, percorso, codice di esito e durata, che persiste in journald. Chi ha chiamato e quando si sa; che cosa ha chiesto no.

Terzo fatto, ed è quello che impedisce di dichiarare il vincolo soddisfatto: la macchina ha una partizione di scambio attiva da 29,8 GB, con 1 GB già in uso, su 15 GB di memoria di sistema. Testo di prompt e di risposta transita per la memoria di sistema, e sotto pressione una pagina può finire scritta sul disco senza che nessuna impostazione dell'applicazione lo impedisca. È esattamente la ragione per cui il progetto gemello, nella sua decisione del 2026-10-14, stabilisce che negare le scritture all'applicazione non prova l'assenza di persistenza, e verifica anche i meccanismi del kernel. Con la scheda ora in uso il modello risiede in memoria video e la pressione sulla memoria di sistema cala, il che riduce l'esposizione ma non la annulla.

Nessuna cartella di cronologia o di cache è presente accanto ai modelli: sotto la radice comune del pacchetto c'è soltanto la cartella dei modelli.

Decisione che ne discende per questo progetto, da confermare: la sintesi del materiale del corpus non va sull'endpoint di rete ma sul motore locale a esperti dentro WSL, che non manda niente fuori da questa macchina. Costa velocità, circa 2,81 parole al secondo contro 43,99, ma soddisfa il vincolo senza dipendere da una verifica sulla macchina altrui. L'endpoint con la scheda resta appropriato per il lavoro che non ha questo vincolo. Questo supera ADR-003 limitatamente al materiale soggetto al vincolo, e va scritto come decisione quando il proprietario conferma.

## 2026-10-20 — Chiusa la parentesi infrastrutturale, avviata la trascrizione del corpus

Commit: nessuno. File toccati: questo. Motivo: il proprietario chiede di chiudere la deviazione sull'infrastruttura e tornare allo scopo del progetto, che è trascrivere.

Stato finale della parentesi. La scheda della macchina di inferenza è utilizzabile e misurata, la correzione è installata, e l'unica cosa non provata resta il comportamento all'accensione a freddo. Si è deciso di non forzare un riavvio per provarlo: l'host è condiviso, il prossimo riavvio naturale farà da prova, e il sintomo è riconoscibile da qualunque client senza accedere alla macchina, perché un modello caricato con memoria video a zero significa che il difetto è tornato. Il controllo costa una chiamata e sta scritto nei contesti degli altri due progetti.

Un rischio nuovo, nato proprio dalla riparazione, va registrato perché prima non esisteva: la scheda ha 16 GB e il servizio condiviso tiene un modello residente per cinque minuti dopo l'ultima richiesta, impostazione predefinita `OLLAMA_KEEP_ALIVE` a 5m0s. Un modello denso da quattordici miliardi ne occupa 10,12, quindi due progetti che carichino ciascuno il proprio modello non ci stanno insieme. Finché la macchina serviva in CPU la contesa non si vedeva, perché la memoria di sistema è più abbondante e nessuno veniva escluso; da oggi un secondo caricamento può fallire o ripiegare sul processore senza dirlo. Mitigazione a costo nullo per chi chiama: passare `keep_alive` nella richiesta invece di lasciare il valore predefinito, così la memoria si libera subito dopo l'uso.

Sulla scelta per il corpus: la trascrizione non tocca né la scheda né il modello locale, perché WhisperX gira sulla CPU di questa macchina; la scheda serve solo alla sintesi che verrà dopo, dove vale ADR-003, cioè endpoint di rete come primario e motore locale a esperti come riserva.

La corsa sulle trenta lezioni è partita con modello `medium` e VAD `silero`, dopo aver rimosso i tre file del pilota prodotti con `small`, che altrimenti avrebbero fatto saltare la prima lezione. Stima dalle misure di oggi: circa ventuno ore di calcolo, in corse riprendibili.

## 2026-10-20 — Riparato: la GPU della macchina di inferenza è tornata, misurata prima e dopo

Commit: nessuno. File toccati: questo, `.claude/memory/decisions.md`, e i due contesti anonimizzati negli altri due progetti. Motivo: il proprietario ha eseguito il comando con i privilegi e la correzione va misurata, non dichiarata.

Il frammento di configurazione è installato come `attesa-gpu.conf` accanto all'override esistente, il servizio è ripartito alle 10:49:00 e due secondi dopo il suo giornale scriveva «inference compute ... library=CUDA ... NVIDIA GeForce RTX 5060 Ti ... total 15.9 GiB», dove cinque giorni prima scriveva «library=cpu».

La misura, presa con lo stesso modello e lo stesso prompt di quella precedente, è questa. Prima: 1,91 parole al secondo in decodifica, 105,89 secondi di caricamento, memoria video occupata 0,00 GB. Dopo: 43,99 parole al secondo, 3,99 secondi di caricamento, memoria video occupata 10,12 GB su 10,12 di modello, cioè interamente residente. Il guadagno è un fattore 23 sulla generazione e 26 sul caricamento. Perimetro: un solo modello, `qwen3:14b`, una chiamata per condizione, macchina non sotto carico di altri al momento della seconda misura.

Resta non provato ciò che il riavvio del servizio non può provare, e cioè che al prossimo riavvio della macchina la corsa non si ripeta. Quello che si sa oggi è che il passo di attesa è registrato nell'unità con l'esito ignorato e che, a scheda già pronta, non ritarda l'avvio di un secondo. La prova vera è un riavvio pianificato della macchina con la lettura della riga del giornale subito dopo, e va concordata perché l'host è condiviso.

Conseguenza sul piano del corpus: la metà linguistica cambia ordine di grandezza. A 44 parole al secondo la sintesi di una lezione da due ore e mezza passa dall'ora scarsa a qualche minuto, e `summarize` più `digest` su trenta lezioni diventano un lavoro da una sera invece che da una settimana.

## 2026-10-20 — Anonimizzazione: indirizzi reali finiti in un repository pubblico, e come sono stati tolti

Commit: nessuno. File toccati: questo e `.claude/memory/decisions.md`. Motivo: un difetto introdotto da questa sessione, dichiarato qui perché la regola chiede di dichiararlo e non di correggerlo in silenzio.

Le voci del work-log scritte oggi contenevano l'indirizzo reale della macchina di inferenza, quello di un client della LAN e i nomi degli alias SSH. Questo repository è pubblico su GitHub, e la regola di anonimizzazione del sistema vuole che in un file tracciato compaiano segnaposto e non valori reali. Le voci erano già state committate e spinte, quindi i valori stanno nella storia pubblica e non solo nella copia di lavoro: toglierli dal file corrente non li toglie dai commit precedenti, e la rimozione dalla storia è una riscrittura con pubblicazione forzata, che è una decisione del proprietario e non un'operazione da fare di propria iniziativa.

Nella copia di lavoro i valori sono stati sostituiti con `<host-inferenza>`, `<client-della-lan>` e `<alias-ssh-inferenza>`, e la verifica è una ricerca che non trova più né indirizzi né nomi host nel file. La lezione generale, che vale oltre questo progetto: una misura presa su una macchina altrui porta con sé il suo indirizzo, e il momento in cui si scrive la misura è il momento in cui si decide se quel repository è pubblico, non il momento del commit.

## 2026-10-20 — Il pilota su una lezione intera rovescia la stima: 17 ore, non 41

Commit: nessuno. File toccati: questo, e fuori dal repository la prima trascrizione del corso. Motivo: validare la catena su un file vero invece che su un campione.

La lezione «La costruzione del piano strategico - Lez. 1» dura 10.002 secondi, cioè 2 ore 46 minuti, ed è stata trascritta con il modello `small` in 2.079 secondi, cioè 34 minuti e 39 secondi. Il rapporto è 0,208, cioè 4,8 volte più veloce del tempo reale, mentre il campione di cinque minuti dava 0,40, cioè 2,5 volte. La differenza è il costo di caricamento del modello, che sul campione pesava per metà della corsa e su una lezione intera si spalma. Ne segue che la stima di stamattina era pessimistica di un fattore due: le 80 ore di corso valgono circa 17 ore di calcolo con `small`, e per estrapolazione circa 21 con `medium` e silero, applicando il rapporto 1,27 misurato fra i due sul campione. Il numero per `medium` resta estrapolato e non misurato finché non gira una lezione intera con quella combinazione.

La catena è validata sul disco esterno, percorsi con apostrofo compresi, uscita nella cartella del modulo giusto, tre formati prodotti, 116 KB di testo su 1.307 righe, e la riga nel registro delle corse.

Sulla qualità emerge un difetto che il campione non poteva mostrare, e che riguarda i nomi propri del dominio: il modello `small` storpia sistematicamente la sigla della scuola, rendendola con una parola italiana di suono simile. Un errore così non si corregge leggendo meglio, si ripete identico in tutte le trenta lezioni, e inquina ogni cosa costruita sopra, dalle sintesi alle skill. Due contromisure, non alternative: salire a `medium`, che sui nomi fa meglio, e prevedere comunque una passata di sostituzione dei termini ricorrenti del dominio sulle trascrizioni finite, che costa pochi secondi ed è deterministica.

Conseguenza operativa: quel `.txt` è stato prodotto con `small`, quindi se si adotta `medium` va cancellato prima della corsa vera, altrimenti lo script salta quella lezione perché la vede già fatta.

## 2026-10-20 — Trovata la causa: Ollama su 11500 ha perso la GPU al riavvio del 15 ottobre

Commit: nessuno. File toccati: questo. Motivo: capire perché il servizio di inferenza in rete macina in CPU, con accesso SSH autorizzato dal proprietario. L'alias che funziona è `<alias-ssh-inferenza>`, non `<alias-errato>`: quest'ultimo non risolve da questa macchina, e la mappatura corretta sta in la documentazione di rete di un progetto gemello e la sua configurazione privata.

La scheda è sana e libera. `nvidia-smi` riporta una RTX 5060 Ti con 16.311 MiB, dei quali 34 usati, utilizzo a zero e nessun processo di calcolo; driver 595.99.02, CUDA 13.2, modulo kernel della stessa versione della libreria utente. Una prova diretta con `cuInit` restituisce 0 e `cuDeviceGetCount` vede un dispositivo. Cade quindi l'ipotesi che un altro progetto tenga occupata la VRAM: non la occupa nessuno.

La macchina ha due installazioni di Ollama, ed è la radice dell'equivoco. Lo snap, versione 0.34.0, ascolta solo su `127.0.0.1:11434`. Il binario nativo `/usr/local/bin/ollama`, avviato da `ollama.service` come utente `ollama` con `OLLAMA_HOST=0.0.0.0:11500`, è quello che serve tutta la rete ed è quello che misuriamo noi.

La causa è un avvio in corsa, documentata dal suo stesso giornale. Al penultimo avvio, il 15 ottobre alle 11:24:24, `ollama.service` scriveva «inference compute ... library=CUDA ... NVIDIA GeForce RTX 5060 Ti ... total 15.9 GiB», con una scoperta durata 818 millisecondi. La macchina si è riavviata alle 12:20:47, il servizio è ripartito alle 12:20:59, la scoperta è durata fra 35 e 90 millisecondi e ha concluso «inference compute id=cpu library=cpu». Stessa configurazione, stesso ambiente, esito opposto: il servizio è partito prima che lo stack NVIDIA fosse pronto, e Ollama interroga le schede una volta sola all'avvio. Da cinque giorni serve in CPU. Nello stesso minuto lo snap registrava un fallimento di snapd nel montare `/usr/share/nvidia` nel proprio spazio dei nomi, che è lo stesso sintomo visto dall'altro lato.

Ne segue che il progetto gemello che legge in locale usa davvero la scheda e non si contraddice con questa misura: quel progetto non passa da 11500, apre via SSH una propria istanza isolata sulla porta 11501, che interroga la scheda al proprio avvio e la trova.

La correzione è un riavvio di `ollama.service`, più un vincolo d'ordine nel file di unità perché la corsa non si ripeta al prossimo riavvio. Non è stato eseguito: alle 10:33 una connessione da <client-della-lan> era attiva e il giornale mostra richieste `/api/chat` ogni pochi minuti, quindi qualcuno lo sta usando e il riavvio interromperebbe il suo lavoro. Serve il via libera del proprietario.

Sullo spazio disco, che era l'altra domanda: la radice ha 73 GB con 22 liberi. Un modello da diciotto gigabyte ne lascerebbe quattro, quindi non si scarica là. E se la scheda torna, con 16 GB di VRAM il modello giusto è un 14B denso, non un 30B a esperti, perché il collo di bottiglia non è più la lettura dei pesi.

## 2026-10-20 — Il VAD chiude la scelta, e la macchina in rete resta in CPU anche sotto carico altrui

Commit: nessuno. File toccati: questo e `<cartella-del-corpus>/TRASCRIZIONI/_strumenti/Trascrivi-Cartella.ps1`. Motivo: chiudere la scelta del modello di trascrizione e verificare una contestazione del proprietario sulla scheda grafica della macchina in rete.

Sul VAD la misura è netta e va contro l'intuizione: `medium` con `--vad silero` impiega 2 minuti e 32 secondi sul campione di cinque minuti, meno dei 3 minuti e 15 di `medium` con il VAD predefinito, e recupera l'attacco dell'audio che le altre due prove avevano inventato di sana pianta. Sulle 80 ore stimate significa circa 41 ore di calcolo. Il prezzo è che silero conserva le esitazioni del parlato. Scelta: `medium` con `silero`, e lo script ora porta il parametro `-Vad` con quel valore predefinito.

Correzione a un'affermazione precedente: il messaggio in cui dicevo di avere già aggiunto quel parametro allo script è stato scritto prima della modifica, che non c'era. La modifica è stata fatta dopo, verificata rileggendo le quattro righe toccate e rilanciando la pianificazione a vuoto, che ora dichiara `vad silero` e conta sempre trenta registrazioni da fare.

Sulla macchina in rete il proprietario ha contestato la conclusione, dicendo che altri progetti usano la scheda. La verifica ripetuta non la smentisce ma la circoscrive: alle 10:33 su quella porta era caricato `qwen3:14b` per uso altrui, con `size_vram` a 0, e una generazione cronometrata dà 1,91 token al secondo con 106 secondi di caricamento. Il rapporto con i 3,52 token al secondo del modello da 8 miliardi è quasi esattamente inverso al numero di parametri, che è la firma del calcolo in CPU; su scheda un 14B a quattro bit starebbe fra 30 e 60 token al secondo. La conclusione corretta non è che la macchina non abbia la scheda, ma che il servizio Ollama sulla porta 11500 non la sta usando, cosa compatibile con altri processi che la occupano. Le tre cause possibili, VRAM già occupata, contenitore senza accesso alla scheda, runtime non visto, si distinguono solo da un terminale su quella macchina.

L'accesso SSH non è riuscito da questa sessione: l'alias `<alias-errato>` non esiste nella configurazione SSH di questo utente Windows, né come sessione PuTTY, e `ssh ollama@<host-inferenza>` risponde «Permission denied (publickey,password)», cioè l'host c'è e la chiave di questo account non è autorizzata. La verifica resta da fare dal terminale del proprietario.

## 2026-10-20 — Scelta del modello di trascrizione: misurato `small` contro `medium`

Commit: nessuno. File toccati: questo. Motivo: la scelta del modello decide una trentina di ore di calcolo e non si fa a sensazione.

Stesso campione di cinque minuti estratto da una lezione del modulo 1, stessa lingua forzata, stesso formato. Il modello `small` impiega 2 minuti e 0 secondi, cioè 2,5 volte il tempo reale; il modello `medium` impiega 3 minuti e 15 secondi, cioè 1,54 volte il tempo reale. Sulle 80 ore stimate del corpus significa circa 32 ore di calcolo con `small` e circa 52 con `medium`: il divario è di un fattore 1,6 e non di un fattore tre come avevo ipotizzato prima di misurare.

Sulla qualità il confronto riga per riga non lascia dubbi e va a favore di `medium`: dove `small` scrive «e e tanti di fallimenti» e salda due periodi in uno, `medium` separa le frasi, chiude «e quindi ha detto andiamo a contattare direttamente gli utenti» che in `small` resta troncato, e corregge «quindi tutto venduto» in «Poi è tutto venduto». Entrambi inventano qualcosa sulla primissima riga, dove il campione taglia a metà di una parola: è il comportamento noto di Whisper su un attacco senza silenzio, e la contromisura prevista dal progetto è `--vad silero`, che è la prova successiva.

Decisione proposta, in attesa del consenso del proprietario: `medium` con `--vad silero`, perché le venti ore di calcolo in più si pagano una volta sola mentre la ruvidezza della trascrizione la ereditano tutti i passi successivi, cioè le sintesi, la documentazione e le skill.

## 2026-10-20 — Impianto della trascrizione dentro la cartella del corpus

Commit: nessuno. File toccati: questo, e fuori dal repository `<cartella-del-corpus>/TRASCRIZIONI/_strumenti/Trascrivi-Cartella.ps1` e `esclusi-personali.txt`. Motivo: su richiesta del proprietario la trascrizione del corso si fa ignorando i file personali e lasciando sorgenti e uscite dentro la cartella del corso.

L'uscita rispecchia l'albero delle registrazioni: `TRASCRIZIONI/` accanto a `REC LEZIONI/`, con una sottocartella per ciascuno dei cinque moduli e gli strumenti in `TRASCRIZIONI/_strumenti/`. Niente esce dalla cartella del corso e niente entra nel repository, che resta lo strumento e non il magazzino.

L'esclusione dei personali è scritta nello strumento e non nella memoria di chi lo lancia, come prescrive `.claude/rules/documenti-personali.md`: lo script legge `esclusi-personali.txt`, confronta ogni schema con il percorso completo prima di aprire il file, e dichiara nel riepilogo quanti ne ha esclusi. L'elenco è stato provato sull'intero corpus prima dell'uso, come la regola chiede: su 177 file ne esclude esattamente due, cioè l'attestato con il codice fiscale nel nome e il modulo compilato, e ne tiene 175, quindi nessun falso positivo su questo corpus. Sulle sole registrazioni gli esclusi sono zero, perché i due personali sono PDF e stanno fuori da `REC LEZIONI`.

Lo script è riprendibile per costruzione: salta un video se il `.txt` atteso esiste già nella cartella di destinazione, e il nome atteso replica la funzione `_sanitize` di `src/transcriptor/sources/local.py`, cioè caratteri vietati sostituiti e taglio a 120 caratteri. Ha una modalità `-SoloPiano` che elenca senza eseguire e un `-Quanti` che limita la corsa. La corsa a vuoto del 2026-10-20 conta trenta registrazioni trovate, zero escluse, zero già fatte, trenta da fare.

Sul modello linguistico della macchina in rete: Ollama non ospita modelli di riconoscimento del parlato, quindi per la trascrizione non esiste là un modello specializzato da scaricare; il salto di qualità su quel lato sarebbe far vedere la scheda grafica a WhisperX, non cambiare modello. Sul lato testuale, su una macchina che serve in CPU, la famiglia giusta è quella a esperti con pochi parametri attivi, cioè lo stesso principio di colibri, e il candidato è `qwen3:30b-a3b`; la ricerca web del 2026-10-20 non ha trovato nessuna misura su sola CPU per quel modello, quindi la scelta va misurata là e non dedotta. Nota utile per il corpus: `rag.py` recupera con FTS5 e non con vettori, quindi il `bge-m3` già presente su quella macchina non è usato da questo progetto e resta la via se si vorrà una ricerca semantica su ottanta ore di parlato.

## 2026-10-20 — Ricognizione del corpus su disco esterno in vista di un progetto a sé

Commit: nessuno. File toccati: questo. Motivo: valutare la fattibilità di trascrivere il corpus e di ricavarne documentazione LaTeX e skill, prima di impegnarsi.

Il corpus di `<cartella-del-corpus>` conta 177 file per 15 GB: 124 PDF, 30 MP4, 5 PPTX, 4 XLSX, 2 DOCX, 8 TXT e 4 immagini, organizzati in cinque moduli di lezione, una cartella `REC LEZIONI` con le registrazioni divise per modulo, un `SYLLABUS` di diciotto file e una cartella `Documentations`. Le registrazioni misurate con ffprobe sono venti e valgono 53,89 ore, con una media di 2 ore e 42 minuti; le altre dieci non si sono lette per un problema di citazione del percorso, non perché manchino, e il totale stimato per dimensione è intorno alle 80 ore. Perimetro: misura presa con `ffprobe` sui soli `.mp4`, la stima delle dieci restanti è proporzionale ai byte e non è una misura.

La velocità di trascrizione sulla CPU di questa macchina è stata misurata e non stimata: cinque minuti di audio estratti da una lezione del modulo 1, modello `small`, lingua forzata a `it`, formato `txt`, sono stati trascritti in 2 minuti e 0 secondi, cioè circa due volte e mezzo il tempo reale. Ne segue che le 80 ore stimate del corpus valgono all'incirca 32 ore di calcolo con lo stesso modello, da spezzare in più corse riprendibili. Il testo prodotto è leggibile e in italiano, ma con `small` resta ruvido su un parlato di aula con riverbero: va bene per cercare e per indicizzare, non per citare alla lettera. Salire a `medium` migliora la resa e moltiplica il tempo, e la scelta del modello è la prima decisione da prendere prima di avviare il lotto.

Su sei PDF campionati con `pdftotext` limitato alle prime tre pagine, cinque restituiscono testo estraibile fra 498 e 2.031 caratteri, quindi il corpus documentale è in larga parte nativo e non richiede OCR.

Due file portano nel nome la natura personale e vanno nell'elenco di esclusione prima di qualunque ingestione, secondo `.claude/rules/documenti-personali.md`: un attestato di frequenza che ha il codice fiscale nel nome, e un modulo compilato. Sul secondo la sonda di estrazione è stata eseguita prima di riconoscerlo e ha restituito zero caratteri, trattandosi di una scansione: nessun contenuto è quindi entrato in contesto, e il fatto si dichiara qui perché la regola chiede di dichiararlo invece di verificarlo riaprendo il file.

Gli strumenti per il seguito esistono già nel template: il pacchetto `latex` per l'ambiente di build, con TeX Live 2026 e pandoc 3.12 già installati sulla macchina; `book-to-skill` con la skill `book-digest`, che da un PDF genera una skill con capitoli caricati a richiesta; `knowledge-wiki` per il collegamento fra concetti; `lavoro-a-lotti` per rendere riprendibile un lavoro più grande di una sessione; `doc-ingest` per l'indice di Livello 1 sul corpus; `academic-researcher` e `fonti-non-recuperabili` per la parte di ricerca web; `anonymization` prima di pubblicare qualunque cosa.

## 2026-10-20 — Verificata dal vivo la sintesi sull'endpoint remoto, e misurata

Commit: nessuno. File toccati: questo. Motivo: la capacità dichiarata nel giro precedente andava provata invece che descritta, e la prova ha corretto due affermazioni.

Prima correzione: l'endpoint remoto non era da configurare, era già configurato. `transcribe doctor` riporta «LLM raggiungibile (http://<host-inferenza>:11500/v1, qwen3:14b)», quindi il `.env` locale, che non si legge per regola di permessi, punta già alla macchina in rete e non a `localhost`. Il valore predefinito del codice resta `http://localhost:11434/v1`; a non essere documentato è soltanto il `README.md`.

La prova è passata: `transcribe summarize` su una trascrizione di 3.883 parole, con `--llm-url http://<host-inferenza>:11500/v1` e `--llm-model llama3.1:8b-instruct-q4_K_M`, ha prodotto `out/006 - Let's Start The Monster Text to Speech & Voice Cloning Course.summary.md`, 1.885 byte, in italiano e con le quattro sezioni previste dal prompt. Tempo totale 9 minuti e 32 secondi.

Seconda correzione, ed è la misura che conta per pianificare: quella macchina serve Ollama sulla CPU, non sulla GPU. A vuoto, `/api/generate` con lo stesso modello dà 3,52 parole al secondo in decodifica (158 token in 44,8 secondi, caricamento 0,12 secondi), e `/api/ps` riporta `size_vram` a 0,00 GB su 5,15 GB di modello residente. L'endpoint è quindi utile e affidabile, ma non è accelerazione: è circa la stessa velocità del colibri locale misurato il 2026-10-19 a 2,81 parole al secondo. Perimetro della misura: un solo modello, `llama3.1:8b-instruct-q4_K_M`, due chiamate, macchina altrimenti scarica.

Sulla trascrizione la macchina locale non ha GPU: `transcribe doctor` dice `device cpu (int8)` e `nvidia-smi` non esiste. Il resto dell'ambiente è a posto: ffmpeg, yt-dlp 2026.07.04, whisperx e argos-translate sono ok, `HF_TOKEN` manca e serve solo per `--diarize`.

## 2026-10-20 — Ricognizione: sorgenti YouTube, GPU e modelli locali della macchina

Commit: nessuno (giro di sola lettura sul codice del progetto, scritture solo fuori dal repository). File toccati: `E:/windows-status/docs/09_TOOLCHAIN_DA_ALTRI_PROGETTI.md`, `E:/windows-status/docs/11_ORCHESTRAZIONE_AGENTI_SU_WINDOWS.md`, `E:/windows-status/CLAUDE.local.md`. Motivo: tre domande sul perimetro del progetto, verificate sul codice e sulla macchina invece che sulla memoria.

Scaricare da YouTube è una capacità già presente e non da aggiungere: `yt-dlp` è fra le dipendenze obbligatorie di `pyproject.toml`, `imageio-ffmpeg` porta ffmpeg senza installazione manuale, e la CLI espone `youtube`, `playlist` e `info`, con i download temporanei in `work/` e gli output in `out/`.

Sulla GPU la risposta è doppia e va tenuta distinta per metà di pipeline. La trascrizione è solo locale: `src/transcriptor/device.py` sceglie `cuda`/`float16` oppure `cpu`/`int8` interrogando `torch.cuda.is_available()` sulla macchina che esegue il comando, e non esiste nessun modo di mandare l'ASR su un'altra macchina. La metà linguistica invece è già remotizzabile, perché `summarize`, `digest` e `ask` parlano con un endpoint compatibile con quello di OpenAI configurabile con `TRANSCRIBE_LLM_BASE_URL` o con l'opzione `--llm-url`, il cui valore predefinito punta a `http://localhost:11434/v1` ma non vincola a `localhost`. Sulla rete locale esiste una seconda macchina con GPU che espone Ollama, censita in `docs/09` sezione 4 di `windows-status` con l'indirizzo reale nel suo `CLAUDE.local.md`: è il bersaglio naturale di `--llm-url`. Il `README.md` di questo progetto non lo dice, e resta quindi una capacità presente ma non documentata.

Su colibri la verifica è stata fatta dentro WSL: la distribuzione `Ubuntu` ha il motore compilato, versione 2.0.0, con 47 GB di modelli a esperti nel filesystem ext4 e il servizio previsto sulla porta 8000. Non serve a questo progetto, perché gira su CPU e non accelera WhisperX, e perché i modelli che ospita sono generalisti e non acustici; l'uso per cui esiste è l'offload del lavoro meccanico a lotti del pacchetto `llm-local` del template. Potrebbe al più sostituire Ollama come endpoint di `summarize`, essendo compatibile con l'API di OpenAI, ma a 2,81 parole al secondo misurate il 2026-10-19 sul modello di riferimento sarebbe più lento della macchina con GPU.

Il censimento di macchina non conosceva colibri: `E:/windows-status` lo nominava solo dentro il pacchetto del template, non fra i componenti installati, perché non sta nel registro di Windows, non appartiene a WinGet e lo snapshot non guarda dentro le distribuzioni WSL. La lacuna è stata chiusa con la sezione 7 di `docs/09`, che registra la collocazione, la procedura di ripristino manuale e la verifica ancora aperta sulla copertura del disco virtuale di WSL da parte del backup Veeam.

## <YYYY-MM-DD> — Inizializzazione del sistema di progetto

Commit: <hash del commit corrente> File toccati: anatomia di `.claude`, `CLAUDE.md`, `.gitignore`, schede di `context/`. Motivo: installazione del sistema portabile di contesto, documentazione e version control descritto in `.claude/PROJECT-SYSTEM.md`. Schede create con struttura e frontmatter, da popolare leggendo il codice nelle sessioni successive.
