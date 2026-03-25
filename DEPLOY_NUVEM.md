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

3. **Planilha na nuvem** (escolha uma):  
   - **Mais simples:** abra o app e use **“Enviar Excel (.xlsx)”**. Cada sessão pode precisar reenviar após o app “dormir” no plano gratuito.  
   - **Mais estável:** inclua `data/planilha.xlsx` no repositório (repositório **privado** se os preços forem confidenciais) e faça deploy de novo após cada atualização de preços.

4. **Secrets (opcional)**  
   - No painel do app: **Settings → Secrets**.  
   - Copie o modelo de `.streamlit/secrets.toml.example` se quiser definir caminhos fixos.

5. **Histórico e logins**  
   - No plano gratuito do Streamlit Cloud o disco é **reiniciado** quando o app hiberna ou é redeployado. Usuários e pedidos salvos só em arquivo **podem sumir**.  
   - Para produção séria, use banco externo (Supabase, etc.) — isso é um passo extra.

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
| `GRAMADOWAY_DATA_DIR` | Onde ficam `usuarios/`, `users/` e dados por login |

## Depois do deploy

Copie a URL gerada (ex.: `https://xxx.streamlit.app`) e envie para o time. Todos acessam pelo navegador, sem instalar Python.
