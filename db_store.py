"""
Persistência em PostgreSQL (Supabase, Neon, RDS, etc.) para usuários e JSON por login.

Ative com variável de ambiente ou Streamlit Secret:
  GRAMADOWAY_DATABASE_URL  — URI completa (recomendado)
  SUPABASE_DB_URL          — alias aceito

Exemplo Supabase (Settings → Database → Connection string → URI):
  postgresql://postgres.[ref]:[PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any, Optional

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore
    Json = None  # type: ignore


def _url() -> str:
    a = os.environ.get("GRAMADOWAY_DATABASE_URL", "").strip()
    b = os.environ.get("SUPABASE_DB_URL", "").strip()
    return a or b


def db_enabled() -> bool:
    return bool(_url())


@contextmanager
def get_conn():
    if not db_enabled():
        raise RuntimeError("Database URL não configurada.")
    if psycopg2 is None:
        raise RuntimeError("Instale psycopg2-binary para usar GRAMADOWAY_DATABASE_URL.")
    conn = psycopg2.connect(_url())
    try:
        _ensure_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS gramadoway_users (
                login TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt_hex TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
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
            """
        )


def registry_load() -> dict:
    """Retorna {'version': 1, 'users': [{'login','hash','salt_hex'}, ...]}."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT login, password_hash, salt_hex FROM gramadoway_users ORDER BY login"
            )
            rows = cur.fetchall()
    users = [
        {"login": r[0], "hash": r[1], "salt_hex": r[2]}
        for r in rows
    ]
    return {"version": 1, "users": users}


def registry_sync_users(users: list[dict]) -> None:
    """Substitui estado de usuários na BD para refletir a lista completa (como registry.json)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT login FROM gramadoway_users")
            existing = {r[0] for r in cur.fetchall()}
            wanted = {u.get("login") for u in users if u.get("login")}
            to_remove = existing - wanted
            for lg in to_remove:
                cur.execute("DELETE FROM gramadoway_users WHERE login = %s", (lg,))
            for u in users:
                lg = u.get("login")
                if not lg:
                    continue
                cur.execute(
                    """
                    INSERT INTO gramadoway_users (login, password_hash, salt_hex)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (login) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        salt_hex = EXCLUDED.salt_hex
                    """,
                    (lg, u.get("hash", ""), u.get("salt_hex", "")),
                )


def doc_get(login: str, doc_key: str) -> Any:
    """Lê JSON (lista ou objeto). doc_key: historico | clientes | rascunho."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload FROM gramadoway_user_docs
                WHERE login = %s AND doc_key = %s
                """,
                (login, doc_key),
            )
            row = cur.fetchone()
    if not row:
        return None
    val = row[0]
    if val is None:
        return None
    if isinstance(val, (list, dict)):
        return val
    return val


def doc_set(login: str, doc_key: str, payload: Any) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gramadoway_user_docs (login, doc_key, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (login, doc_key) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    updated_at = NOW()
                """,
                (login, doc_key, Json(payload)),
            )


def doc_delete(login: str, doc_key: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM gramadoway_user_docs WHERE login = %s AND doc_key = %s",
                (login, doc_key),
            )
