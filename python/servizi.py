"""Regole per creare stanze e partecipare, senza SQL né richieste HTTP."""
import secrets

import repository
from connessione import transazione


class ErroreAccesso(ValueError):
    """Errore previsto da mostrare all'utente nel form."""


def accedi(username, azione, codice=''):
    """Registra il partecipante e restituisce codice stanza e identificatore di accesso."""
    # Il form passa già lo username senza spazi iniziali e finali.
    lunghezza = len(username.strip())
    if lunghezza < 1 or lunghezza > 30:
        raise ErroreAccesso('Inserisci uno username da 1 a 30 caratteri.')
    if azione not in ('crea', 'entra'):
        raise ErroreAccesso('Scegli se creare una stanza o entrare.')
    # Il codice serve solo quando si entra in una stanza esistente.
    if azione == 'entra':
        if len(codice) != 6:
            raise ErroreAccesso('Il codice deve contenere esattamente 6 cifre.')
        for carattere in codice:
            if carattere not in '0123456789':
                raise ErroreAccesso('Il codice deve contenere esattamente 6 cifre.')

    # Il servizio decide i confini della transazione: stanza e admin sono un'operazione unica.
    with transazione():
        if repository.trova_utente(username):
            raise ErroreAccesso('Username già occupato. Scegline un altro.')
        if azione == 'entra' and not repository.stanza_esiste(codice):
            raise ErroreAccesso('Stanza non trovata. Controlla il codice.')
        if azione == 'crea':
            while True:
                numero = secrets.randbelow(1_000_000)
                codice = str(numero).zfill(6)
                if not repository.stanza_esiste(codice):
                    break
            repository.inserisci_stanza(codice)
        # Solo chi crea la stanza riceve il ruolo di admin.
        is_admin = azione == 'crea'
        accesso_id = secrets.token_hex(16)
        repository.inserisci_utente(username, codice, is_admin, accesso_id)
    return codice, accesso_id


def esci(username, accesso_id):
    """Elimina l'utente o, se è admin, tutta la stanza. Restituisce il codice da notificare."""
    with transazione():
        utente = repository.trova_utente(username)
        if utente is None or utente['accesso_id'] != accesso_id:
            return None

        codice = utente['stanza_codice']
        if utente['is_admin']:
            # Prima i partecipanti, poi la stanza: rispettiamo la chiave esterna.
            repository.elimina_utenti_stanza(codice)
            repository.elimina_stanza(codice)
        else:
            repository.elimina_utente(username)
    return codice
