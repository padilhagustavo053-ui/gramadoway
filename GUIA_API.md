# Gramadoway — modo simples com API

Tudo fica organizado em **uma API** com tela de ajuda automática (**Swagger**). Você não precisa decorar caminhos de pasta: abre o navegador em `/docs` e testa.

## O que a API faz

| Endereço | Função |
|----------|--------|
| `http://localhost:8000/docs` | **Documentação interativa** — testar envio de planilha e ver status |
| `GET /health` | Só confirma que está ligada |
| `GET /v1/status` | Mostra pasta de dados, se achou planilha, quantos usuários |
| `GET /v1/produtos` | Lista todos os produtos (lê o Excel) |
| `POST /v1/planilha` | **Envia** o arquivo `.xlsx` — salva como `data/planilha.xlsx` |

## Passo a passo no seu PC

1. Instalar dependências (uma vez):
   ```bash
   pip install -r requirements.txt
   ```

2. **Terminal 1 — API**
   ```bash
   cd gramadoway_sistema
   uvicorn api_app:app --host 0.0.0.0 --port 8000
   ```

3. Abra no navegador: **http://localhost:8000/docs**

4. Envie a planilha: expanda **`POST /v1/planilha`** → **Try it out** → escolha o arquivo → **Execute**.

5. **Terminal 2 — site (Streamlit)**
   ```bash
   set GRAMADOWAY_API_URL=http://localhost:8000
   streamlit run app.py
   ```
   No PowerShell: `$env:GRAMADOWAY_API_URL="http://localhost:8000"`

Pronto: o formulário usa só a API; a planilha fica centralizada na API.

## Chave de segurança (opcional)

Se definir no servidor da API:
```text
GRAMADOWAY_API_KEY=minha_chave_secreta
```

No Streamlit use a mesma chave (variável de ambiente ou Secrets):
```text
GRAMADOWAY_API_KEY=minha_chave_secreta
```

Nas chamadas, a API exige o header `X-Gramadoway-Key` — o app Streamlit já envia quando a variável existe.

## Nuvem (resumo)

1. Hospede a **API** num serviço que aceite Python (Railway, Render, Fly.io, etc.) com comando:
   `uvicorn api_app:app --host 0.0.0.0 --port $PORT`
2. Anote a URL pública, ex.: `https://gramado-api.onrender.com`
3. No **Streamlit Cloud**, em Secrets:
   ```toml
   GRAMADOWAY_API_URL = "https://gramado-api.onrender.com"
   ```
   (e `GRAMADOWAY_API_KEY` se você ativou a chave na API)

4. Envie a planilha uma vez pelo `/docs` da API na nuvem.

Histórico de pedidos e logins do Streamlit continuam no disco do **Streamlit** (no plano gratuito pode resetar). A API só centraliza **planilha + lista de produtos** de forma clara.

## Docker (tudo junto)

Na pasta `gramadoway_sistema`:
```bash
docker compose up --build
```

- API: http://localhost:8000/docs  
- Site: http://localhost:8501  
