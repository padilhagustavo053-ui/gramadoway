-- Executar no Supabase: SQL Editor → New query → colar → Run
-- (As tabelas também são criadas automaticamente na primeira utilização da app.)

CREATE TABLE IF NOT EXISTS gramadoway_users (
    login TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt_hex TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gramadoway_user_docs (
    login TEXT NOT NULL,
    doc_key TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (login, doc_key),
    CONSTRAINT gramadoway_user_docs_login_fkey
        FOREIGN KEY (login)
        REFERENCES gramadoway_users (login)
        ON DELETE CASCADE,
    CONSTRAINT gramadoway_user_docs_key_check
        CHECK (doc_key IN ('historico', 'clientes', 'rascunho'))
);
