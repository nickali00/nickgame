"""Regole di Nomi, cose, città: tre manche, con valutazione dell'admin."""
import secrets
import economia
import unicodedata

from connessione import transazione
import repository
import repository_nomi as dati
from servizi import ErroreGioco, prepara_gioco

CATEGORIE = {'nomi': 'Nomi', 'cose': 'Cose', 'citta': 'Città'}
LETTERE = 'ABCDEFGILMNOPRSTV'


def normalizza(testo):
    # Ignora maiuscole, accenti e spazi ripetuti nel confronto tra risposte.
    testo = unicodedata.normalize('NFD', testo.casefold())
    testo = ''.join(c for c in testo if not unicodedata.combining(c))
    return ' '.join(testo.split())


def lettera_casuale(usate=''):
    return secrets.choice([lettera for lettera in LETTERE if lettera not in usate])


def stato(utente):
    codice = utente['stanza_codice']
    partita = dati.partita(codice)
    totale = repository.conta_partecipanti(codice)
    contesto = dict(nomi_selezionato=True, partita=partita, numero_partecipanti=totale, categorie=CATEGORIE)
    if partita is not None:
        risposte = dati.risposte(codice, partita['turno'])
        ricevute = {r['username'] for r in risposte}
        lettera = partita['lettere'][-1]
        for risposta in risposte:
            risposta['ammissibile'] = normalizza(risposta['testo']).startswith(lettera.lower())
        contesto.update(
            lettera=lettera, ha_risposto=utente['username'] in ricevute,
            risposte_ricevute=len(ricevute), tutti_pronti=len(ricevute) == totale,
            # Prima dell'invio di tutti nessuna risposta altrui arriva al template.
            risposte=risposte if len(ricevute) == totale or partita['valutato'] else [],
            classifica=dati.classifica(codice)
        )
    return contesto


def verifica_utente(username, accesso_id, admin=False):
    utente = repository.trova_utente(username)
    if utente is None or utente['accesso_id'] != accesso_id:
        raise ErroreGioco('Accesso non valido.')
    if admin and not utente['is_admin']:
        raise ErroreGioco('Questa azione è riservata all’admin.')
    codice = utente['stanza_codice']
    gioco = repository.gioco_selezionato(codice)
    if gioco is None or gioco['nome'] != 'Nomi, cose, città':
        raise ErroreGioco('Nomi, cose, città non è attivo nella stanza.')
    if not 2 <= repository.conta_partecipanti(codice) <= gioco['max_giocatori']:
        raise ErroreGioco('Servono da 2 a 8 giocatori.')
    return codice


def verifica_turno(codice, partita_id, turno):
    partita = dati.partita(codice)
    if partita is None or partita['id'] != partita_id or partita['turno'] != turno:
        raise ErroreGioco('La manche è cambiata. Riprova.')
    if partita['finita'] or partita['in_sala']:
        raise ErroreGioco('La partita è terminata o è in pausa.')
    return partita


def avvia(username, accesso_id):
    with transazione():
        prepara_gioco(username, accesso_id, 'Nomi, cose, città')
        codice = verifica_utente(username, accesso_id, admin=True)
        partita = dati.partita(codice)
        if partita is not None and not partita['finita']:
            raise ErroreGioco('La partita è già in corso.')
        dati.crea(codice, secrets.token_hex(16), lettera_casuale())
    return codice


def rispondi(username, accesso_id, partita_id, turno, risposte):
    with transazione():
        codice = verifica_utente(username, accesso_id)
        partita = verifica_turno(codice, partita_id, turno)
        if partita['valutato'] or any(r['username'] == username for r in dati.risposte(codice, turno)):
            raise ErroreGioco('Hai già inviato le risposte di questa manche.')
        testi = {categoria: risposte.get(categoria, '').strip() for categoria in CATEGORIE}
        if any(len(testo) > 60 for testo in testi.values()):
            raise ErroreGioco('Ogni risposta può contenere al massimo 60 caratteri.')
        dati.inserisci_risposte(codice, username, turno, testi)
    return codice


def valuta(username, accesso_id, partita_id, turno, accettate):
    with transazione():
        codice = verifica_utente(username, accesso_id, admin=True)
        partita = verifica_turno(codice, partita_id, turno)
        risposte = dati.risposte(codice, turno)
        if partita['valutato']:
            raise ErroreGioco('La manche è già stata valutata.')
        if len({r['username'] for r in risposte}) != repository.conta_partecipanti(codice):
            raise ErroreGioco('Attendi le risposte di tutti.')
        valide = set(accettate)
        ammissibili = {str(r['id']) for r in risposte
                       if normalizza(r['testo']).startswith(partita['lettere'][-1].lower())}
        if not valide <= ammissibili:
            raise ErroreGioco('Puoi convalidare solo risposte che iniziano con la lettera estratta.')
        # Contiamo solo le risposte approvate, separatamente per categoria.
        frequenze = {}
        for risposta in risposte:
            if str(risposta['id']) in valide:
                chiave = (risposta['categoria'], normalizza(risposta['testo']))
                frequenze[chiave] = frequenze.get(chiave, 0) + 1
        for risposta in risposte:
            valida = str(risposta['id']) in valide
            punti = 0
            if valida:
                chiave = (risposta['categoria'], normalizza(risposta['testo']))
                punti = 5 if frequenze[chiave] > 1 else 10
            dati.assegna_punti(risposta['id'], valida, punti)
        dati.conferma_valutazione(codice)
    return codice


def prossima(username, accesso_id, partita_id, turno):
    with transazione():
        codice = verifica_utente(username, accesso_id, admin=True)
        partita = verifica_turno(codice, partita_id, turno)
        if not partita['valutato']:
            raise ErroreGioco('Convalida prima le risposte.')
        lettera = None if turno == 3 else lettera_casuale(partita['lettere'])
        dati.avanza(codice, lettera)
        if turno == 3:
            economia.premia_classifica(partita_id, 'Nomi, cose, città', dati.classifica(codice))
    return codice


def cambia_vista(username, accesso_id, in_sala):
    with transazione():
        codice = verifica_utente(username, accesso_id, admin=True)
        if dati.partita(codice) is None:
            raise ErroreGioco('Nessuna partita da visualizzare.')
        dati.imposta_sala(codice, in_sala)
    return codice
