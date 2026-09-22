"""Indirizzo WebSocket e notifiche al server Go locale."""
import urllib.request
from flask import current_app


def url_websocket(codice):
    # Il codice proviene dal database ed è già composto da sei cifre.
    indirizzo = current_app.config['GO_WEBSOCKET_URL']
    return indirizzo + '/ws?stanza=' + codice


def notifica_stanza(codice):
    indirizzo = current_app.config['GO_HTTP_URL']
    url = indirizzo + '/notifica?stanza=' + codice

    # Solo i server conoscono questa chiave: non viene inviata al browser.
    chiave = current_app.config['SECRET_KEY']
    richiesta = urllib.request.Request(url, method='POST')
    richiesta.add_header('Authorization', 'Bearer ' + chiave)

    try:
        # Attendiamo al massimo un secondo per le operazioni di rete.
        with urllib.request.urlopen(richiesta, timeout=1) as risposta:
            risposta.read()
    except OSError:
        # Include gli errori di rete e HTTP: le modifiche al database restano valide.
        current_app.logger.warning('Go non raggiungibile: notifica della stanza non inviata.')
