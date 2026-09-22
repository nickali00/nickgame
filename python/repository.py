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


def inserisci_utente(username, codice, is_admin, accesso_id):
    get_db().execute(
        'INSERT INTO utenti (username, stanza_codice, is_admin, accesso_id) VALUES (?, ?, ?, ?)',
        (username, codice, int(is_admin), accesso_id),
    )


def partecipanti_stanza(codice):
    rows = get_db().execute(
        'SELECT username, is_admin FROM utenti WHERE stanza_codice = ? '
        'ORDER BY is_admin DESC, username', (codice,)
    ).fetchall()
    return [dict(row) for row in rows]


def elimina_utente(username):
    get_db().execute('DELETE FROM utenti WHERE username = ?', (username,))


def elimina_utenti_stanza(codice):
    get_db().execute('DELETE FROM utenti WHERE stanza_codice = ?', (codice,))


def elimina_stanza(codice):
    get_db().execute('DELETE FROM stanze WHERE codice = ?', (codice,))


def stanze_disponibili():
    rows = get_db().execute(
        'SELECT stanze.codice, admin.username AS admin, COUNT(utenti.username) AS partecipanti '
        'FROM stanze '
        'JOIN utenti AS admin ON admin.stanza_codice = stanze.codice AND admin.is_admin = 1 '
        'LEFT JOIN utenti ON utenti.stanza_codice = stanze.codice '
        'GROUP BY stanze.codice, admin.username ORDER BY stanze.codice'
    ).fetchall()
    return [dict(row) for row in rows]
