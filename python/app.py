"""Pagine e API web di Nickgame."""
import flask

import forza4
import configurazione
import connessione
import repository
import servizi
import sincronizzazione

app = flask.Flask(__name__)
configurazione.configura(app)
connessione.init_app(app)


def utente_corrente():
    # La sessione contiene lo username del browser che sta facendo la richiesta.
    username = flask.session.get('username')
    utente = repository.trova_utente(username)
    # Il valore predefinito mantiene valide le sessioni precedenti all'aggiornamento.
    accesso_id = flask.session.get('accesso_id', username)
    if utente is None or utente['accesso_id'] != accesso_id:
        flask.session.clear()
        return None
    return utente


@app.route('/', methods=['GET', 'POST'])
def login():
    if utente_corrente() is not None:
        return flask.redirect(flask.url_for('stanza'))

    # GET: mostra il form vuoto. POST: elabora i dati inviati dal form.
    if flask.request.method != 'POST':
        return flask.render_template(
            'login.html', errore=None, username='', codice='',
            stanze=repository.stanze_disponibili()
        )

    username = flask.request.form.get('username', '').strip()
    codice = flask.request.form.get('codice', '').strip()
    azione = flask.request.form.get('azione')

    try:
        codice, accesso_id = servizi.accedi(username, azione, codice)
    except servizi.ErroreAccesso as errore:
        return flask.render_template(
            'login.html', errore=str(errore), username=username, codice=codice,
            stanze=repository.stanze_disponibili()
        )

    # Il servizio ha salvato i dati: ricordiamo l'utente e avvisiamo Go.
    flask.session.clear()
    flask.session['username'] = username
    flask.session['accesso_id'] = accesso_id
    sincronizzazione.notifica_stanza(codice)
    return flask.redirect(flask.url_for('stanza'))


@app.post('/logout')
def logout():
    username = flask.session.get('username')
    accesso_id = flask.session.get('accesso_id', username)
    codice = servizi.esci(username, accesso_id)
    flask.session.clear()
    if codice is not None:
        sincronizzazione.notifica_stanza(codice)
    return flask.redirect(flask.url_for('login'))


def stato_gioco(utente):
    stato = forza4.stato(utente['stanza_codice'])
    stato['gioco_corrente'] = repository.gioco_selezionato(utente['stanza_codice'])
    stato['minimo_giocatori'] = 2
    return stato


@app.post('/seleziona-gioco')
def seleziona_gioco():
    utente = utente_corrente()
    if utente is None:
        return flask.redirect(flask.url_for('login'))
    if not utente['is_admin']:
        flask.abort(403)
    gioco_id = flask.request.form.get('gioco_id', type=int)
    if gioco_id is None or not 1 <= gioco_id <= 2147483647:
        flask.abort(400)
    try:
        codice = servizi.scegli_gioco(utente['username'], utente['accesso_id'], gioco_id)
    except servizi.ErroreGioco as errore:
        flask.flash(str(errore))
    else:
        sincronizzazione.notifica_stanza(codice)
    return flask.redirect(flask.url_for('stanza'))


@app.get('/stanza')
def stanza():
    utente = utente_corrente()
    if utente is None:
        return flask.redirect(flask.url_for('login'))

    elenco = repository.partecipanti_stanza(utente['stanza_codice'])
    return flask.render_template(
        'stanza.html', utente=utente, partecipanti=elenco,
        giochi=repository.giochi_disponibili(utente['stanza_codice']),
        **stato_gioco(utente)
    )


@app.get('/stanza/giochi')
def elenco_giochi():
    utente = utente_corrente()
    if utente is None:
        return '', 401
    risposta = flask.make_response(flask.render_template(
        'giochi.html', utente=utente,
        giochi=repository.giochi_disponibili(utente['stanza_codice']),
        **stato_gioco(utente)
    ))
    risposta.headers['Cache-Control'] = 'no-store'
    return risposta


@app.get('/stanza/partita')
def pannello_partita():
    utente = utente_corrente()
    if utente is None:
        return '', 401
    risposta = flask.make_response(flask.render_template(
        'partita.html', utente=utente, **stato_gioco(utente)
    ))
    risposta.headers['Cache-Control'] = 'no-store'
    return risposta


@app.post('/forza4/<azione>')
def azione_forza4(azione):
    utente = utente_corrente()
    if utente is None:
        return flask.redirect(flask.url_for('login'))
    try:
        if azione == 'avvia':
            codice = forza4.avvia(utente['username'], utente['accesso_id'])
        elif azione in ('stanza', 'riprendi'):
            codice = forza4.cambia_vista(utente['username'], utente['accesso_id'], azione == 'stanza')
        elif azione == 'muovi':
            codice = forza4.muovi(
                utente['username'], utente['accesso_id'],
                flask.request.form.get('colonna', type=int),
                flask.request.form.get('partita_id'),
                flask.request.form.get('griglia')
            )
        else:
            flask.abort(404)
    except servizi.ErroreGioco as errore:
        flask.flash(str(errore))
    else:
        sincronizzazione.notifica_stanza(codice)
    return flask.redirect(flask.url_for('stanza') + '#partita')


@app.post('/partita/<azione>')
def cambia_vista(azione):
    utente = utente_corrente()
    if utente is None:
        return flask.redirect(flask.url_for('login'))
    if azione not in ('stanza', 'riprendi'):
        flask.abort(404)
    try:
        codice = forza4.cambia_vista(utente['username'], utente['accesso_id'], azione == 'stanza')
    except servizi.ErroreGioco as errore:
        flask.flash(str(errore))
    else:
        sincronizzazione.notifica_stanza(codice)
    return flask.redirect(flask.url_for('stanza'))


@app.get('/api/stanze')
def elenco_stanze():
    # La lista è visibile prima dell'accesso, come la pagina di login.
    risposta = flask.jsonify(repository.stanze_disponibili())
    risposta.headers['Cache-Control'] = 'no-store'
    return risposta


@app.get('/api/partecipanti')
def partecipanti():
    utente = utente_corrente()
    if utente is None:
        return flask.jsonify(errore='Accesso richiesto'), 401

    elenco = repository.partecipanti_stanza(utente['stanza_codice'])
    risposta = flask.jsonify(elenco)
    risposta.headers['Cache-Control'] = 'no-store'
    return risposta


@app.get('/api/sincronizzazione')
def collegamento():
    utente = utente_corrente()
    if utente is None:
        return flask.jsonify(errore='Accesso richiesto'), 401

    indirizzo = sincronizzazione.url_websocket(utente['stanza_codice'])
    risposta = flask.jsonify(url=indirizzo)
    risposta.headers['Cache-Control'] = 'no-store'
    return risposta


if __name__ == '__main__':
    app.run()
