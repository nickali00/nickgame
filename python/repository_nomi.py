"""Query SQL per Nomi, cose, città."""
from connessione import get_db


def partita(codice):
    row = get_db().execute('SELECT * FROM partite_nomi WHERE stanza_codice = ?', (codice,)).fetchone()
    return dict(row) if row is not None else None


def elimina(codice):
    get_db().execute('DELETE FROM partite_nomi WHERE stanza_codice = ?', (codice,))


def crea(codice, partita_id, lettera):
    elimina(codice)
    get_db().execute('INSERT INTO partite_nomi (stanza_codice, id, lettere) VALUES (?, ?, ?)',
                     (codice, partita_id, lettera))


def risposte(codice, turno):
    rows = get_db().execute(
        'SELECT * FROM risposte_nomi WHERE stanza_codice = ? AND turno = ? ORDER BY username, id',
        (codice, turno)
    ).fetchall()
    return [dict(row) for row in rows]


def inserisci_risposte(codice, username, turno, risposte):
    for categoria, testo in risposte.items():
        get_db().execute(
            'INSERT INTO risposte_nomi (stanza_codice, username, turno, categoria, testo) VALUES (?, ?, ?, ?, ?)',
            (codice, username, turno, categoria, testo)
        )


def assegna_punti(risposta_id, valida, punti):
    get_db().execute('UPDATE risposte_nomi SET valida = ?, punti = ? WHERE id = ?',
                     (int(valida), punti, risposta_id))


def conferma_valutazione(codice):
    get_db().execute('UPDATE partite_nomi SET valutato = 1 WHERE stanza_codice = ?', (codice,))


def avanza(codice, lettera):
    if lettera is None:
        get_db().execute('UPDATE partite_nomi SET finita = 1 WHERE stanza_codice = ?', (codice,))
    else:
        get_db().execute(
            'UPDATE partite_nomi SET turno = turno + 1, lettere = lettere || ?, valutato = 0 WHERE stanza_codice = ?',
            (lettera, codice)
        )


def imposta_sala(codice, in_sala):
    get_db().execute('UPDATE partite_nomi SET in_sala = ? WHERE stanza_codice = ?', (int(in_sala), codice))


def classifica(codice):
    rows = get_db().execute(
        'SELECT utenti.username, COALESCE(SUM(risposte_nomi.punti), 0) AS punti '
        'FROM utenti LEFT JOIN risposte_nomi ON risposte_nomi.username = utenti.username '
        'AND risposte_nomi.stanza_codice = utenti.stanza_codice '
        'WHERE utenti.stanza_codice = ? GROUP BY utenti.username ORDER BY punti DESC, utenti.username',
        (codice,)
    ).fetchall()
    return [dict(row) for row in rows]
