# Publicar o Gramadoway na nuvem (link para a equipe)

**Quer algo mais organizado?** Use a **API + `/docs`** — leia primeiro o arquivo **`GUIA_API.md`** (Swagger, upload da planilha, Docker).

---

O app foi preparado para rodar no **Streamlit Community Cloud** (grátis) ou em qualquer servidor com Python.

## Opção A — Streamlit Cloud (recomendado para começar)

1. **GitHub**  
   - Crie um repositório (pode ser **privado**).  
   - Envie a pasta `gramadoway_sistema` inteira (ou o monorepo com ela dentro).

2. **streamlit.io/cloud**  
   - Entre com a conta GitHub.  
   - **New app** → escolha o repositório.  
   - **Main file path:** `gramadoway_sistema/app.py` (ajuste se a pasta tiver outro nome).  
   - **Branch:** `main` (ou a que você usar).

3. **Planilha na nuvem**  
   - O projeto inclui **`data/planilha.xlsx`** (produtos de **exemplo**) para o Streamlit já mostrar o formulário sem upload.  
   - Troque por sua planilha real (mesmo caminho e nome), commit e redeploy — ou use **“Enviar Excel”** no app.  
   - Preços confidenciais: repósitorio **privado** ou só upload na sessão.

4. **Secrets**  
   - No painel do app: **Settings → Secrets**.  
   - Veja o modelo em `.streamlit/secrets.toml.example` (planilha, caminhos, **base de dados**).

5. **Persistência na nuvem (recomendado) — PostgreSQL / Supabase**  
   Sem banco, no Streamlit grátis o disco **volátil** pode apagar usuários e pedidos após hibernar ou redeployar.  
   Com **`GRAMADOWAY_DATABASE_URL`** os dados ficam na base **sempre ligada** (você não mantém servidor).

   **Passos resumidos (Supabase grátis):**  
   1. Crie um projeto em [supabase.com](https://supabase.com).  
   2. **Project Settings → Database → Connection string → URI** (modo *Session* ou conexão **direta** porta `5432`).  
   3. Copie a URI com a **senha** da base (não commite no Git).  
   4. No Streamlit Cloud: **Settings → Secrets** e adicione por exemplo:  
      `GRAMADOWAY_DATABASE_URL = "postgresql://postgres...."`  
   5. Faça **Redeploy** do app. Na primeira execução as tabelas são criadas sozinhas (ou rode `supabase/schema.sql` no **SQL Editor** do Supabase).  
   6. **Importante:** ao ativar a URL, **novos** logins/pedidos vão para a BD. Dados antigos só em `data/` no disco **não** migram automaticamente — trate como instalação nova ou migre manualmente.

6. **Histórico e logins só em arquivo (sem URL)**  
   - Continua válido para testes locais; na nuvem grátis pode **perder** dados conforme o item 5.

## Opção B — Seu próprio servidor / Docker

```bash
cd gramadoway_sistema
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Defina `GRAMADOWAY_DATA_DIR` apontando para uma pasta **persistente** no servidor.

## Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `GRAMADOWAY_PLANILHA` | Caminho absoluto do `.xlsx` |
| `GRAMADOWAY_DATA_DIR` | Onde ficam `usuarios/`, `users/` e dados por login (se **não** usar BD) |
| `GRAMADOWAY_DATABASE_URL` | URI PostgreSQL (Supabase, Neon, etc.) — **persiste** usuários e JSON por login |
| `SUPABASE_DB_URL` | Alias opcional da mesma URI |

## Depois do deploy

Copie a URL gerada (ex.: `https://xxx.streamlit.app`) e envie para o time. Todos acessam pelo navegador, sem instalar Python.
