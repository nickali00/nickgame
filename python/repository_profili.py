"""Query dei profili permanenti e dei tentativi di accesso."""
from connessione import get_db


def trova(username):
    riga = get_db().execute('SELECT username FROM profili WHERE username = ?', (username,)).fetchone()
    return dict(riga) if riga else None


def da_codice(impronta):
    riga = get_db().execute('SELECT username FROM profili WHERE codice_hash = ?', (impronta,)).fetchone()
    return dict(riga) if riga else None


def inserisci(username, impronta):
    get_db().execute('INSERT INTO profili (username, codice_hash) VALUES (?, ?)', (username, impronta))


def senza_codice(username):
    return get_db().execute(
        'SELECT 1 FROM profili WHERE username = ? AND codice_hash IS NULL', (username,)
    ).fetchone() is not None


def assegna_codice(username, impronta):
    get_db().execute('UPDATE profili SET codice_hash = ? WHERE username = ?', (impronta, username))


def tentativi(indirizzo):
    return get_db().execute('SELECT * FROM tentativi_accesso WHERE indirizzo = ?', (indirizzo,)).fetchone()


def registra_errore(indirizzo, numero, ora):
    get_db().execute(
        'INSERT INTO tentativi_accesso VALUES (?, ?, ?) '
        'ON CONFLICT(indirizzo) DO UPDATE SET numero=excluded.numero, ultimo=excluded.ultimo',
        (indirizzo, numero, ora)
    )


def azzera_tentativi(indirizzo):
    get_db().execute('DELETE FROM tentativi_accesso WHERE indirizzo = ?', (indirizzo,))
