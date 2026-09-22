# Nickgame

Progetto per il corso di Advanced Programming Languages.

## Descrizione

Da definire: scopo del gioco e funzionalità principali.

## Struttura

- `docs/`: requisiti e diario di sviluppo locali, esclusi dal repository.
- `cpp/`: componente C++, responsabilità da definire.
- `csharp/`: componente C#, responsabilità da definire.
- `python/`: interfaccia Flask e primo flusso di creazione/accesso alle stanze con SQLite.
- `go/`: componente Go, responsabilità da definire.
- `dati/`: dati di esempio per provare il progetto.

## Esecuzione

Dalla cartella `nickgame`:

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Apri http://127.0.0.1:5000. Per simulare un secondo utente usa un altro browser
oppure una finestra privata. Ricarica la pagina della stanza per vedere i nuovi utenti.

SQLite è incluso in Python. Al primo avvio vengono creati il database
`python/instance/nickgame.sqlite` e la chiave locale che firma le sessioni.
Questa cartella è esclusa da Git. Gli avvii successivi conservano i dati.

## Dati e regole attuali

- `stanze`: `codice` è una chiave primaria testuale di 6 cifre.
- `utenti`: `username` è la chiave primaria; `stanza_codice` collega la stanza;
  `is_admin` vale 1 per il creatore e 0 per gli altri partecipanti.
- Ogni utente appartiene a una sola stanza. Un indice impedisce due admin nella stessa stanza.
- Gli username sono globalmente univoci e distinguono maiuscole e minuscole.
- Il server assegna il ruolo admin; il form non può sceglierlo.
- È un accesso con nickname, senza password: uno username occupato non può
  essere recuperato da un altro browser. La sessione corrente permette di ritornare
  nella propria stanza. Uscita, recupero account e cancellazione stanze sono da implementare.
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

- `app.py`: configura Flask, legge il form, gestisce sessioni e risposte HTML.
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
