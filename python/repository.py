"""Query SQL per utenti e stanze, senza regole HTTP o gestione del form."""
from connessione import get_db


def trova_utente(username):
    row = get_db().execute(
        'SELECT * FROM utenti WHERE username = ?', (username,)
    ).fetchone()
    return dict(row) if row is not None else None


def stanza_esiste(codice):
    return get_db().execute(
        'SELECT 1 FROM stanze WHERE codice = ?', (codice,)
    ).fetchone() is not None


def inserisci_stanza(codice):
    get_db().execute('INSERT INTO stanze (codice) VALUES (?)', (codice,))


def inserisci_utente(username, codice, is_admin):
    get_db().execute(
        'INSERT INTO utenti (username, stanza_codice, is_admin) VALUES (?, ?, ?)',
        (username, codice, int(is_admin)),
    )


def partecipanti_stanza(codice):
    rows = get_db().execute(
        'SELECT username, is_admin FROM utenti WHERE stanza_codice = ? '
        'ORDER BY is_admin DESC, username', (codice,)
    ).fetchall()
    return [dict(row) for row in rows]
