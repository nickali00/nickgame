"""Catalogo e scelta delle tre parti dell'avatar."""
import secrets

from connessione import transazione
import repository
import repository_avatar
import repository_economia

def catalogo(username):
    parti = {'testa': [], 'corpo': [], 'piedi': []}
    for articolo in repository_economia.catalogo(username):
        if articolo['posseduto']:
            parti[articolo['parte']].append(articolo['immagine'])
    return parti


def verifica(utente):
    attuale = repository.trova_utente(utente['username'])
    if attuale is None or attuale['accesso_id'] != utente['accesso_id']:
        raise ValueError('Accesso scaduto.')


def carica(utente):
    with transazione():
        verifica(utente)
        parti = repository_avatar.leggi(utente['username'])
        opzioni = catalogo(utente['username'])
        if parti is None or any(parti[c] not in opzioni[c] for c in opzioni):
            parti = dict(testa=secrets.choice(['ragazzo', 'ragazza']),
                         corpo='felpa-arancione', piedi='jeans-blu')
            repository_avatar.salva(utente['username'], parti)
    return parti


def salva(utente, parti):
    with transazione():
        verifica(utente)
        for categoria, opzioni in catalogo(utente['username']).items():
            if parti.get(categoria) not in opzioni:
                raise ValueError('Devi prima acquistare questo oggetto premendo il lucchetto.')
        repository_avatar.salva(utente['username'], parti)
