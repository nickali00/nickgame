import sqlite3
from flask import current_app, g


def get_db():
    # Apre la connessione solo se questa richiesta non ne ha già una.
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        # Permette di leggere le colonne per nome, per esempio riga['username'].
        g.db.row_factory = sqlite3.Row
        # Fa rispettare i collegamenti tra utenti e stanze.
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    # Flask passa l'eventuale errore e chiama questa funzione anche se la richiesta fallisce.
    if 'db' in g:
        g.db.close()
        del g.db


def init_db():
    # root_path è la cartella dell'app, indipendentemente da dove viene avviata.
    with open(current_app.root_path + '/schema.sql', encoding='utf-8') as file:
        get_db().executescript(file.read())


def transazione():
    db = get_db()
    # Riserva la scrittura prima di controllare username e codice stanza.
    db.execute('BEGIN IMMEDIATE')
    # Usata con "with", la connessione conferma le modifiche o le annulla se c'è un errore.
    return db


def init_app(app):
    app.teardown_appcontext(close_db)
    # Rende disponibili current_app e g durante l'inizializzazione.
    with app.app_context():
        init_db()
