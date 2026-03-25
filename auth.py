"""Autenticação local — senhas com PBKDF2 (stdlib), um diretório de dados por usuário."""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from pathlib import Path
from typing import Optional

from config_paths import data_root

_ITERATIONS = 310_000


def _base() -> Path:
    d = data_root() / "usuarios"
    d.mkdir(parents=True, exist_ok=True)
    return d


def registry_path() -> Path:
    return _base() / "registry.json"


def sanitize_login(login: str) -> str:
    s = (login or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{3,32}", s):
        raise ValueError(
            "Login: 3 a 32 caracteres, apenas letras minúsculas, números e sublinhado."
        )
    return s


def _load_registry() -> dict:
    p = registry_path()
    if not p.exists():
        return {"version": 1, "users": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("users"), list):
            return data
    except Exception:
        pass
    return {"version": 1, "users": []}


def _save_registry(data: dict) -> None:
    registry_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS, dklen=32
    )
    return dk.hex()


def tem_usuarios() -> bool:
    return len(_load_registry().get("users", [])) > 0


def contar_usuarios() -> int:
    return len(_load_registry().get("users", []))


def registrar_primeiro_usuario(login: str, password: str) -> None:
    if tem_usuarios():
        raise RuntimeError("Já existe usuário cadastrado.")
    if len(password) < 6:
        raise ValueError("Senha deve ter pelo menos 6 caracteres.")
    lg = sanitize_login(login)
    salt = secrets.token_bytes(16)
    user = {
        "login": lg,
        "hash": _hash_password(password, salt),
        "salt_hex": salt.hex(),
    }
    data = _load_registry()
    data["users"] = [user]
    _save_registry(data)


def registrar_usuario(login: str, password: str) -> None:
    if len(password) < 6:
        raise ValueError("Senha deve ter pelo menos 6 caracteres.")
    lg = sanitize_login(login)
    data = _load_registry()
    if any(u.get("login") == lg for u in data["users"]):
        raise ValueError("Este login já está em uso.")
    salt = secrets.token_bytes(16)
    data["users"].append(
        {
            "login": lg,
            "hash": _hash_password(password, salt),
            "salt_hex": salt.hex(),
        }
    )
    _save_registry(data)


def verificar_login(login: str, password: str) -> Optional[str]:
    try:
        lg = sanitize_login(login)
    except ValueError:
        return None
    data = _load_registry()
    for u in data.get("users", []):
        if u.get("login") != lg:
            continue
        try:
            salt = bytes.fromhex(u.get("salt_hex", ""))
        except ValueError:
            return None
        if _hash_password(password, salt) == u.get("hash"):
            return lg
    return None


SESSION_KEY = "gw_user"
