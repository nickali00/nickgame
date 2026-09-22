"""Primo flusso di Nickgame: crea una stanza o partecipa con un nickname."""
from pathlib import Path
import secrets

from flask import Flask, redirect, render_template, request, session, url_for

import connessione
import repository
from servizi import ErroreAccesso, accedi

app = Flask(__name__)
instance = Path(app.instance_path)
instance.mkdir(exist_ok=True)

# La chiave locale firma i cookie: conservarla mantiene valide le sessioni.
key_file = instance / 'secret.key'
try:
    with key_file.open('x') as file:
        file.write(secrets.token_hex(32))
except FileExistsError:
    pass
app.config.update(
    SECRET_KEY=key_file.read_text(),
    DATABASE=instance / 'nickgame.sqlite',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)


connessione.init_app(app)


@app.route('/', methods=['GET', 'POST'])
def login():
    utente = repository.trova_utente(session.get('username'))
    if utente:
        return redirect(url_for('stanza'))

    errore = None
    username = ''
    codice = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        codice = request.form.get('codice', '').strip()
        azione = request.form.get('azione')
        try:
            accedi(username, azione, codice)
        except ErroreAccesso as error:
            errore = str(error)
        else:
            session.clear()
            session['username'] = username
            return redirect(url_for('stanza'))
    return render_template('login.html', errore=errore, username=username, codice=codice)


@app.get('/stanza')
def stanza():
    utente = repository.trova_utente(session.get('username'))
    if utente is None:
        return redirect(url_for('login'))
    partecipanti = repository.partecipanti_stanza(utente['stanza_codice'])
    return render_template('stanza.html', utente=utente, partecipanti=partecipanti)

if __name__ == '__main__':
    app.run()
