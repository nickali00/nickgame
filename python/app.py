"""Pagine e API web di Nickgame."""
import flask

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
        return flask.render_template('login.html', errore=None, username='', codice='')

    username = flask.request.form.get('username', '').strip()
    codice = flask.request.form.get('codice', '').strip()
    azione = flask.request.form.get('azione')

    try:
        codice, accesso_id = servizi.accedi(username, azione, codice)
    except servizi.ErroreAccesso as errore:
        return flask.render_template(
            'login.html', errore=str(errore), username=username, codice=codice
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


@app.get('/stanza')
def stanza():
    utente = utente_corrente()
    if utente is None:
        return flask.redirect(flask.url_for('login'))

    elenco = repository.partecipanti_stanza(utente['stanza_codice'])
    return flask.render_template('stanza.html', utente=utente, partecipanti=elenco)


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
