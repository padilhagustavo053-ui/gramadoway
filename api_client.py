"""Cliente HTTP da API Gramadoway (usado pelo Streamlit)."""
from __future__ import annotations

import os


def obter_url_api() -> str:
    return os.environ.get("GRAMADOWAY_API_URL", "").strip().rstrip("/")


def carregar_produtos_api() -> tuple[list, str]:
    import httpx

    base = obter_url_api()
    if not base:
        raise RuntimeError("GRAMADOWAY_API_URL não definida")
    url = f"{base}/v1/produtos"
    headers = {}
    key = os.environ.get("GRAMADOWAY_API_KEY", "").strip()
    if key:
        headers["X-Gramadoway-Key"] = key
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, headers=headers)
        if r.status_code == 404:
            return [], ""
        r.raise_for_status()
        return r.json(), url
