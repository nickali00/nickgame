CREATE TABLE IF NOT EXISTS giochi (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    max_giocatori INTEGER NOT NULL CHECK (max_giocatori > 0)
);

INSERT INTO giochi (nome, max_giocatori) VALUES ('Forza 4', 2)
    ON CONFLICT(nome) DO NOTHING;

CREATE TABLE IF NOT EXISTS stanze (
    codice TEXT PRIMARY KEY NOT NULL
        CHECK (length(codice) = 6 AND codice NOT GLOB '*[^0-9]*'),
    gioco_id INTEGER REFERENCES giochi(id)
);

CREATE TABLE IF NOT EXISTS utenti (
    username TEXT PRIMARY KEY NOT NULL
        CHECK (length(trim(username)) BETWEEN 1 AND 30),
    accesso_id TEXT NOT NULL,
    stanza_codice TEXT NOT NULL REFERENCES stanze(codice),
    is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1))
);

-- Una stanza può avere molti utenti, ma al massimo un admin.
CREATE UNIQUE INDEX IF NOT EXISTS un_admin_per_stanza
    ON utenti(stanza_codice) WHERE is_admin = 1;

-- Una partita per stanza. Se un giocatore esce, la partita viene cancellata.
CREATE TABLE IF NOT EXISTS partite_forza4 (
    stanza_codice TEXT PRIMARY KEY REFERENCES stanze(codice) ON DELETE CASCADE,
    id TEXT NOT NULL,
    rosso TEXT NOT NULL REFERENCES utenti(username) ON DELETE CASCADE,
    giallo TEXT NOT NULL REFERENCES utenti(username) ON DELETE CASCADE,
    griglia TEXT NOT NULL CHECK (length(griglia) = 42 AND griglia NOT GLOB '*[^012]*'),
    turno INTEGER NOT NULL CHECK (turno IN (1, 2)),
    in_sala INTEGER NOT NULL DEFAULT 0 CHECK (in_sala IN (0, 1)),
    risultato INTEGER NOT NULL CHECK (risultato BETWEEN 0 AND 3)
);
