"""
Caminhos de dados e planilha — local, servidor ou Streamlit Cloud.

Variáveis de ambiente (ou secrets do Streamlit, injetadas em app.py):
  GRAMADOWAY_DATA_DIR  — pasta para usuários, histórico, registry
  GRAMADOWAY_PLANILHA  — caminho absoluto do .xlsx
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent


def data_root() -> Path:
    env = os.environ.get("GRAMADOWAY_DATA_DIR", "").strip()
    if env:
        p = Path(env).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return p
    p = _APP_DIR / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def inject_streamlit_secrets_into_environ() -> None:
    """Chame no início do app Streamlit para secrets.toml virarem env."""
    try:
        import streamlit as st

        sec = getattr(st, "secrets", None)
        if not sec:
            return
        for key in (
            "GRAMADOWAY_DATA_DIR",
            "GRAMADOWAY_PLANILHA",
            "GRAMADOWAY_PRIORIDADE_PRODUTOS",
            "GRAMADOWAY_API_URL",
            "GRAMADOWAY_API_KEY",
            "GRAMADOWAY_DATABASE_URL",
            "SUPABASE_DB_URL",
        ):
            if key in sec:
                val = sec[key]
                if val is not None and str(val).strip():
                    os.environ.setdefault(key, str(val).strip())
    except Exception:
        pass


def migrate_legacy_pedidos_folder() -> None:
    """Se existir pasta antiga pedidos/ com dados, copia para data/ uma vez."""
    legacy = _APP_DIR / "pedidos"
    target = data_root()
    if not legacy.exists() or not legacy.is_dir():
        return
    marker = target / ".migrated_from_pedidos"
    if marker.exists():
        return
    # Só migra se data estiver vazia (exceto .gitkeep)
    existing = [x for x in target.iterdir() if x.name not in (".gitkeep", ".migrated_from_pedidos")]
    if existing:
        return
    try:
        for item in legacy.iterdir():
            dest = target / item.name
            if item.is_dir():
                if dest.exists():
                    continue
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        marker.write_text("ok", encoding="utf-8")
    except OSError:
        pass
