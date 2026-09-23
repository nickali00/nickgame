"""Creazione e accesso ai profili, indipendenti dalle stanze."""
import hmac
import secrets
import time

from flask import current_app
from connessione import transazione
import repository_profili


def impronta(codice):
    # Nel DB conserviamo un'impronta, non il codice personale in chiaro.
    chiave = current_app.config['SECRET_KEY'].encode()
    return hmac.new(chiave, codice.encode(), 'sha256').hexdigest()


def nuovo_codice():
    # Chiamata dentro una transazione: due profili non ricevono lo stesso codice.
    for _ in range(1000):
        codice = str(secrets.randbelow(1_000_000)).zfill(6)
        if repository_profili.da_codice(impronta(codice)) is None:
            return codice
    raise ValueError('Impossibile generare un codice. Riprova più tardi.')


def crea(username):
    username = username.strip()
    if not 1 <= len(username) <= 30:
        raise ValueError('Inserisci uno username da 1 a 30 caratteri.')
    with transazione():
        if repository_profili.trova(username):
            raise ValueError('Username già registrato. Accedi con il tuo codice o scegli un altro nome.')
        codice = nuovo_codice()
        repository_profili.inserisci(username, impronta(codice))
    return username, codice


def accedi(codice, indirizzo):
    # Cinque errori consecutivi bloccano i tentativi dallo stesso indirizzo per un minuto.
    ora = time.time()
    with transazione():
        precedente = repository_profili.tentativi(indirizzo)
        numero = precedente['numero'] if precedente and ora - precedente['ultimo'] < 60 else 0
        if numero >= 5:
            raise ValueError('Troppi tentativi. Attendi un minuto prima di riprovare.')
        valido = len(codice) == 6 and all(c in '0123456789' for c in codice)
        profilo = repository_profili.da_codice(impronta(codice)) if valido else None
        if profilo:
            repository_profili.azzera_tentativi(indirizzo)
        else:
            repository_profili.registra_errore(indirizzo, numero + 1, ora)
    # Fuori dalla transazione, così il tentativo fallito rimane registrato.
    if profilo is None:
        raise ValueError('Codice personale non valido.')
    return profilo


def completa_vecchio_profilo(username):
    # Solo una sessione stanza già verificata può recuperare il suo vecchio avatar.
    with transazione():
        if repository_profili.senza_codice(username):
            codice = nuovo_codice()
            repository_profili.assegna_codice(username, impronta(codice))
            return codice
    return None
