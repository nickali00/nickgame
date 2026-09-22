CREATE TABLE IF NOT EXISTS stanze (
    codice TEXT PRIMARY KEY NOT NULL
        CHECK (length(codice) = 6 AND codice NOT GLOB '*[^0-9]*')
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
