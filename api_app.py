"""
API REST Gramadoway — um único lugar para planilha, status e produtos.

Documentação interativa: http://localhost:8000/docs

Uso local:
  uvicorn api_app:app --host 0.0.0.0 --port 8000

Streamlit usa a API se existir a variável GRAMADOWAY_API_URL (ex.: http://localhost:8000).
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config_paths import data_root, inject_streamlit_secrets_into_environ, migrate_legacy_pedidos_folder
from extrair import extrair_todos, extrair_todos_de_bytes, _caminho_planilha

inject_streamlit_secrets_into_environ()
migrate_legacy_pedidos_folder()

app = FastAPI(
    title="Gramadoway API",
    description="Planilha de preços e status do sistema. Use `/docs` para testar.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("GRAMADOWAY_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _api_key_ok(x_key: str | None = Header(default=None, alias="X-Gramadoway-Key")) -> None:
    expected = os.environ.get("GRAMADOWAY_API_KEY", "").strip()
    if not expected:
        return
    if (x_key or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Chave de API inválida ou ausente (header X-Gramadoway-Key)")


def _json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    if hasattr(obj, "item"):
        try:
            return _json_safe(obj.item())
        except Exception:
            pass
    return str(obj)


@app.get("/", tags=["Início"])
def raiz():
    return {
        "nome": "Gramadoway API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints_principais": ["/v1/status", "/v1/produtos", "POST /v1/planilha"],
    }


@app.get("/health", tags=["Início"])
def health():
    return {"status": "ok"}


@app.get("/v1/status", tags=["Sistema"], dependencies=[Depends(_api_key_ok)])
def status():
    root = data_root()
    planilha_ok = False
    planilha_caminho = None
    try:
        p = _caminho_planilha()
        planilha_ok = p.is_file()
        planilha_caminho = str(p)
    except FileNotFoundError:
        pass
    try:
        import auth

        n_usuarios = auth.contar_usuarios()
    except Exception:
        n_usuarios = 0
    return {
        "data_dir": str(root),
        "planilha_encontrada": planilha_ok,
        "planilha_caminho": planilha_caminho,
        "usuarios_cadastrados": n_usuarios,
        "api_key_ativa": bool(os.environ.get("GRAMADOWAY_API_KEY", "").strip()),
    }


@app.get("/v1/produtos", tags=["Produtos"], dependencies=[Depends(_api_key_ok)])
def listar_produtos():
    try:
        path = _caminho_planilha()
        produtos = extrair_todos(path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Planilha não encontrada. Envie com POST /v1/planilha ou coloque planilha.xlsx em data/",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(_json_safe(produtos))


@app.post("/v1/planilha", tags=["Produtos"], dependencies=[Depends(_api_key_ok)])
async def upload_planilha(arquivo: UploadFile = File(..., description="Arquivo .xlsx")):
    if not arquivo.filename or not arquivo.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .xlsx")
    data = await arquivo.read()
    if len(data) < 100:
        raise HTTPException(status_code=400, detail="Arquivo muito pequeno")
    try:
        extrair_todos_de_bytes(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel inválido: {e}")
    dest = data_root() / "planilha.xlsx"
    dest.write_bytes(data)
    return {
        "ok": True,
        "salvo_em": str(dest),
        "nome_original": arquivo.filename,
        "mensagem": "Planilha gravada. O Streamlit pode usar GRAMADOWAY_API_URL para ler daqui.",
    }


@app.post("/v1/produtos/preview", tags=["Produtos"], dependencies=[Depends(_api_key_ok)])
async def preview_planilha_upload(arquivo: UploadFile = File(...)):
    """Testa um .xlsx sem salvar no servidor."""
    if not arquivo.filename or not arquivo.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .xlsx")
    data = await arquivo.read()
    try:
        produtos = extrair_todos_de_bytes(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"total_produtos": len(produtos), "amostra": _json_safe(produtos[:5])}
