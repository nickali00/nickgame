# Nickgame

Progetto per il corso di Advanced Programming Languages.

## Descrizione

Da definire: scopo del gioco e funzionalità principali.

## Struttura

- `docs/`: requisiti e diario di sviluppo locali, esclusi dal repository.
- `cpp/`: componente C++, responsabilità da definire.
- `csharp/`: componente C#, responsabilità da definire.
- `python/`: interfaccia Flask e primo flusso di creazione/accesso alle stanze con SQLite.
- `go/`: server WebSocket per notificare gli aggiornamenti delle stanze.
- `dati/`: dati di esempio per provare il progetto.

## Avvio con un solo comando

Dalla cartella `nickgame`:

```bash
./run.sh
```

Avvia Flask sulla porta **50010** e Go sulla **50011**.
Apri http://127.0.0.1:50010. **Ctrl+C ferma entrambi**; se uno dei server si
arresta, lo script chiude anche l'altro. Ferma prima eventuali server già avviati
nei vecchi terminali: lo script non interrompe programmi che occupano le porte.

Servono Python con Flask installato e Go. Se esiste `python/.venv`, lo script usa
quel Python; altrimenti usa `python3`. Il binario Go viene compilato in
`go/build/`, esclusa da Git. Per porte diverse si possono impostare
`NICKGAME_PY_PORT` e `NICKGAME_GO_PORT` prima del comando.

## Avvio manuale e installazione delle dipendenze

Dalla cartella `nickgame`:

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run --port 50010
```

Lascia aperto questo terminale. In un secondo terminale, dalla cartella `nickgame`:

```bash
cd go
go run .
```

Serve Go 1.22 o successivo. Il primo avvio scarica la dipendenza
`github.com/gorilla/websocket`. Avvia Flask almeno una volta prima di Go:
crea la chiave locale condivisa tra i due servizi.

Apri http://127.0.0.1:50010. Per simulare un secondo utente usa un altro browser
oppure una finestra privata. I nuovi ingressi aggiornano automaticamente
l'elenco dei partecipanti. Dopo aver installato questa versione, riavvia Flask
e ricarica una volta le pagine già aperte per caricare il nuovo JavaScript.

SQLite è incluso in Python. Al primo avvio vengono creati il database
`python/instance/nickgame.sqlite` e la chiave locale che firma le sessioni.
Questa cartella è esclusa da Git. Gli avvii successivi conservano i dati.

## Stanze disponibili

Sotto il form di accesso compaiono codice, admin e numero di partecipanti delle
stanze disponibili. Inserisci lo username e premi “Entra” sulla stanza scelta:
il codice viene compilato automaticamente e viene inviato il normale form.
Rimane disponibile anche l'accesso inserendo manualmente il codice.

Il canale WebSocket pubblico `lobby` aggiorna la lista quando una stanza viene
creata o chiusa e quando qualcuno entra o esce. Il browser legge `/api/stanze`
solo alla connessione, agli eventi o dopo un errore; non c'è polling periodico
quando la connessione funziona. Lo username digitato viene conservato durante
gli aggiornamenti. La lista è visibile anche prima del login.

## Dati e regole attuali

- `stanze`: `codice` è una chiave primaria testuale di 6 cifre.
- `utenti`: `username` è la chiave primaria; `stanza_codice` collega la stanza;
  `is_admin` vale 1 per il creatore e 0 per gli altri partecipanti.
  `accesso_id` distingue ogni nuova registrazione, anche quando uno username viene riutilizzato.
- Ogni utente appartiene a una sola stanza. Un indice impedisce due admin nella stessa stanza.
- Gli username sono globalmente univoci e distinguono maiuscole e minuscole.
- Il server assegna il ruolo admin; il form non può sceglierlo.
- È un accesso con nickname, senza password: uno username occupato non può
  essere recuperato da un altro browser. La sessione corrente permette di ritornare
  nella propria stanza. Il recupero account non è ancora implementato.
- “Esci dalla stanza” elimina l'utente e libera lo username.
- “Esci e chiudi stanza”, disponibile all'admin, elimina la stanza e tutti i suoi utenti.
  Go notifica il cambiamento; i browser dei partecipanti ricevono HTTP 401 da Flask
  e tornano automaticamente al login. Le altre stanze restano attive.
- I vecchi cookie non tornano validi quando uno username viene riutilizzato:
  Flask controlla anche `accesso_id`. Il database esistente viene aggiornato
  automaticamente senza cancellare utenti o stanze.
- Il controllo dei campi avviene sul server. Il form usa `novalidate` per evitare
  che un codice incompleto blocchi anche il pulsante “Crea stanza”.

## Verifica

I test sono conservati solo localmente in `python/tests/` e non sono inclusi
nel repository. Nella copia di sviluppo, dalla cartella `python`, con l'ambiente
virtuale attivo:

```bash
python -m unittest discover -s tests -v
```

I test usano database temporanei e controllano creazione, ingresso, admin,
errori di input, collisioni dei codici, sessioni e conservazione dei dati
quando lo schema viene inizializzato nuovamente.

## Riferimento per lo studio

[Flask: connessione a SQLite e gestione della connessione](https://flask.palletsprojects.com/en/stable/tutorial/database/).

## Organizzazione del codice Python

- `app.py`: legge il form, gestisce sessioni, pagine HTML e API.
- `configurazione.py`: prepara percorsi, chiave locale e impostazioni di Flask.
- `sincronizzazione.py`: invia gli avvisi a Go e costruisce l’indirizzo WebSocket.
- `servizi.py`: controlla le regole di accesso, genera i codici e assegna l'admin.
- `repository.py`: contiene le query SQL per leggere e scrivere utenti e stanze.
- `connessione.py`: apre e chiude la connessione, inizializza lo schema e gestisce commit/rollback.
- `schema.sql`: definisce tabelle e vincoli del database.

Il servizio esegue creazione della stanza e inserimento dell'admin nella stessa
transazione: un errore annulla entrambe le modifiche. Il repository non fa commit
per ogni query. Le letture delle pagine passano direttamente dal repository.
Questa separazione è volutamente semplice; il collegamento al database usa ancora
il contesto Flask, tramite `current_app` e `g`.

Se la porta 5000 è occupata, dalla cartella `python` avvia con:

```bash
python3 -m flask --app app run --port 5001
```

Poi apri http://127.0.0.1:5001.

## Organizzazione del codice Go

- `main.go`: configurazione, registrazione degli indirizzi e avvio del server.
- `connessioni.go`: struttura del server, mappa, mutex, apertura e chiusura dei WebSocket.
- `notifiche.go`: ricezione degli avvisi da Flask e invio ai browser della stanza.

I tre file appartengono a `package main`: condividono funzioni e tipi senza
importarsi tra loro. Ogni file importa solo i pacchetti che usa direttamente.
Avvia l'intero package con `go run .` dalla cartella `go`.

## Sincronizzazione in tempo reale

1. Flask salva l'ingresso in SQLite e, dopo il commit, avvisa Go tramite HTTP.
2. Go invia un evento WebSocket ai browser collegati alla stanza interessata
   e un evento `stanze_aggiornate` ai browser sulla pagina di accesso.
3. `python/static/stanza.js` riceve l'evento e legge l'elenco aggiornato da Flask.
4. Il browser aggiorna solo l'elenco, senza ricaricare la pagina.

Go non accede a SQLite. Le API Flask ricavano la stanza dalla sessione e
non accettano dal browser il codice di una stanza arbitraria.
Il WebSocket locale riceve il codice della stanza senza un permesso firmato:
chi conosce un codice può ascoltarne gli avvisi di cambiamento, ma questi non
contengono nomi o altri dati. Per leggere i partecipanti serve la sessione Flask
della propria stanza. Le notifiche HTTP da Flask a Go richiedono invece la chiave
locale condivisa, che non viene inviata al browser.

Questa versione è configurata per l'uso sul computer locale: Go ascolta su
`127.0.0.1:50011` e accetta origini browser locali. Per un deployment remoto
servono anche autenticazione dei canali WebSocket, configurazione degli indirizzi,
origini autorizzate e TLS.

Se Go è fermo, gli ingressi restano salvati e il browser tenta la riconnessione
in background, senza mostrare messaggi tecnici nella pagina.
Il browser riprova ogni tre secondi e recupera l'elenco alla nuova connessione.
La versione Go usa una mappa e un mutex: gli invii sono sequenziali e un browser
lento può ritardare gli altri. Senza ping periodici, una connessione interrotta
senza chiusura esplicita può essere rimossa solo quando una lettura o un invio
rilevano il problema.
Le notifiche non sono persistenti: un singolo avviso perso mentre il socket
resta connesso può richiedere una riconnessione o un aggiornamento manuale.
L'elenco rappresenta gli utenti registrati nella stanza, non la presenza online:
chiudere una scheda non rimuove l'utente; occorre usare il pulsante di uscita.
Se Go è fermo, il logout degli altri partecipanti viene riconosciuto alla prossima
richiesta a Flask o alla riconnessione, anziché tramite una notifica immediata.

Configurazioni opzionali:

- Go: `NICKGAME_GO_PORT` (default `50011`) e `NICKGAME_SECRET_FILE`
  (default `../python/instance/secret.key`, relativo alla cartella di avvio).
- Flask: `NICKGAME_GO_HTTP_URL` (default `http://127.0.0.1:50011`) e
  `NICKGAME_GO_WS_URL` (default `ws://127.0.0.1:50011`).
- Se cambi la porta di Go, aggiorna anche i due indirizzi di Flask.

Riferimenti: [Gorilla WebSocket](https://pkg.go.dev/github.com/gorilla/websocket)
e [WebSocket nel browser](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket).
