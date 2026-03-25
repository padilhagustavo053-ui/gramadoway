#!/usr/bin/env python3
"""
Sistema de Pedidos Gramadoway — Potente, robusto e grandioso
Design inspirado em formulários profissionais de chocolates artesanais.
"""
import streamlit as st
from pathlib import Path
import pandas as pd
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent))
from config_paths import (
    data_root,
    inject_streamlit_secrets_into_environ,
    migrate_legacy_pedidos_folder,
)
from extrair import extrair_todos, extrair_todos_de_bytes, _caminho_planilha
from api_client import obter_url_api, carregar_produtos_api
from historico import (
    carregar_historico, salvar_pedido, gerar_pdf,
    carregar_clientes, salvar_cliente,
    carregar_rascunho, salvar_rascunho, limpar_rascunho,
)
from utils import mascara_cnpj, mascara_telefone, mascara_cep, formatar_moeda, aplicar_totais_pedido
from busca_inteligente import buscar_produtos, parsear_atalho
import auth

inject_streamlit_secrets_into_environ()
migrate_legacy_pedidos_folder()

st.set_page_config(
    page_title="Gramadoway — Formulário de Pedido",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS — Letras fortes, grossas, bem visíveis (font-weight 600–700)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --ouro: #C9A227;
    --ouro-claro: #E5D4A1;
    --ouro-escuro: #9A7B1A;
    --chocolate: #3d2914;
    --chocolate-claro: #5c4033;
    --creme: #F5F0E8;
    --creme-escuro: #EBE4D8;
    --fundo-escuro: #1a1410;
    --fundo-card: #2d2218;
    --fundo-page: #FAF7F2;
    --texto-primary: #1a1410;
    --texto-secondary: #4a3f35;
    --texto-muted: #6b5d52;
    --borda: #d4c4a8;
    --borda-ouro: rgba(201,162,39,0.5);
    --borda-focus: var(--ouro);
    --sombra-sm: 0 2px 4px rgba(61,41,20,0.08);
    --sombra-md: 0 4px 12px rgba(61,41,20,0.12), 0 2px 4px rgba(201,162,39,0.06);
    --sombra-lg: 0 12px 24px rgba(61,41,20,0.15), 0 4px 8px rgba(201,162,39,0.08);
}


* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
    text-rendering: optimizeLegibility !important;
}
/* Hierarquia tipográfica — padrão SaaS (Inter, Figma/Linear) */
.stMarkdown, p, span { font-weight: 400 !important; color: var(--texto-primary) !important; }
/* Logo: título branco — override qualquer herança */
.logo-container h1, div.logo-container h1, .logo-container > h1 { color: #ffffff !important; }
.stMarkdown strong { font-weight: 600 !important; }
label { font-weight: 500 !important; color: var(--texto-primary) !important; font-size: 0.875rem !important; }
.stCaption, [data-testid="stCaption"], [data-testid="stCaption"] * {
    font-weight: 400 !important; color: var(--texto-secondary) !important; font-size: 0.8125rem !important;
}
.stTextInput input, .stTextArea textarea {
    font-weight: 400 !important; color: var(--texto-primary) !important; font-size: 0.9375rem !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    font-weight: 400 !important; color: var(--texto-muted) !important;
}

/* Fundo da página */
.stApp { background: var(--fundo-page) !important; }

/* Logo — cabeçalho premium, dourado e escuro */
.logo-container {
    background: linear-gradient(135deg, var(--fundo-escuro) 0%, var(--fundo-card) 100%) !important;
    color: white;
    padding: 2rem 3rem;
    margin: -1rem -1rem 2rem -1rem;
    text-align: center;
    box-shadow: var(--sombra-lg);
    border-radius: 0 0 16px 16px;
    border-bottom: 2px solid var(--ouro);
}
.logo-icon { margin-bottom: 0.5rem; opacity: 0.95; }
.logo-container h1 {
    font-family: 'Inter', sans-serif !important;
    font-size: 2.25rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.05em;
    color: #ffffff !important;
}
.logo-container .subtitle {
    font-size: 0.875rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ouro-claro) !important;
    margin-top: 0.5rem;
    font-weight: 500;
}
.logo-container .tagline {
    font-size: 0.8125rem;
    margin-top: 0.5rem;
    font-weight: 400;
    color: rgba(255,255,255,0.9) !important;
}

/* Seção CLIENTE */
.client-section {
    background: var(--fundo-escuro) !important;
    color: white;
    padding: 0.875rem 1.5rem;
    margin: 0 0 1rem 0;
    border-radius: 10px;
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    box-shadow: var(--sombra-sm);
    border-left: 4px solid var(--ouro);
}
.client-form {
    background: linear-gradient(180deg, #fffefb 0%, var(--creme) 100%);
    border: 1px solid var(--borda);
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--sombra-md);
}
.client-form:hover { box-shadow: var(--sombra-lg); border-color: var(--borda-ouro) !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: white !important;
    border: 1px solid var(--borda) !important;
    border-radius: 10px !important;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    box-shadow: 0 0 0 2px rgba(15,23,42,0.08) !important;
    border-color: var(--borda-focus) !important;
}

/* Instruções */
.instrucoes-box {
    background: linear-gradient(180deg, #fffefb 0%, var(--creme) 100%);
    border: 1px solid var(--borda);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--sombra-md);
}
.instrucoes-texto {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9375rem;
    font-weight: 400;
    color: var(--texto-primary);
    line-height: 1.6;
}
.como-funciona {
    font-family: 'Inter', sans-serif !important;
    border-top: 1px solid var(--borda);
    padding-top: 1rem;
}
.como-funciona summary {
    font-weight: 600;
    font-size: 0.9375rem;
    color: var(--texto-primary);
    cursor: pointer;
    list-style: none;
}
.como-funciona summary::-webkit-details-marker { display: none; }
.como-funciona summary::before {
    content: "+ ";
    color: var(--ouro);
    font-weight: 700;
    margin-right: 6px;
}
.como-funciona[open] summary::before { content: "- "; }
.tabela-unidades {
    width: 100%;
    margin: 1rem 0;
    border-collapse: collapse;
    font-size: 0.95rem;
}
.tabela-unidades th, .tabela-unidades td {
    padding: 0.5rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--borda);
}
.tabela-unidades th {
    background: var(--creme-escuro);
    font-weight: 600;
    color: var(--texto-primary);
    border-bottom: 1px solid var(--borda);
}
.formula-total { margin: 1rem 0 0 0; font-size: 0.875rem; font-weight: 500; color: var(--texto-secondary); }

/* Tabela de produtos */
[data-testid="stDataFrameResizable"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    box-shadow: var(--sombra-lg) !important;
    border: 1px solid var(--borda) !important;
}
[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(135deg, var(--chocolate) 0%, var(--chocolate-claro) 100%) !important;
    color: var(--ouro-claro) !important;
    font-weight: 600 !important;
    font-size: 0.8125rem !important;
    padding: 0.75rem 1rem !important;
    letter-spacing: 0.03em;
    border-bottom: 2px solid var(--ouro) !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(odd) { background: #fffefb !important; }
[data-testid="stDataFrame"] tbody tr:nth-child(even) { background: var(--creme) !important; }
[data-testid="stDataFrame"] tbody tr:hover { background: var(--creme-escuro) !important; }
[data-testid="stDataFrame"] tbody td, [data-testid="stDataFrame"] tbody input,
[data-testid="stDataFrameResizable"] tbody td, [data-testid="stDataFrameResizable"] tbody input,
div[data-testid="stDataFrameResizable"] td, div[data-testid="stDataFrameResizable"] input {
    font-weight: 400 !important;
    color: var(--texto-primary) !important;
    font-size: 0.875rem !important;
}
[data-testid="stDataFrame"] thead th { font-weight: 600 !important; }
[data-testid="stDataFrame"] td:last-child, [data-testid="stDataFrame"] td:nth-child(1),
[data-testid="stDataFrameResizable"] td:last-child, [data-testid="stDataFrameResizable"] td:nth-child(1) {
    font-weight: 500 !important;
}

/* Total */
.total-box {
    background: linear-gradient(135deg, var(--ouro-escuro) 0%, var(--ouro) 50%, #d4a817 100%) !important;
    color: #FFFFFF !important;
    padding: 1.25rem 2rem;
    border-radius: 14px;
    font-size: 1.5rem;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    text-align: center;
    margin-top: 1.5rem;
    box-shadow: var(--sombra-lg);
    border: 1px solid rgba(255,255,255,0.3) !important;
}

/* Barra de ações */
.action-bar {
    background: linear-gradient(180deg, #fffefb 0%, var(--creme) 100%);
    border: 1px solid var(--borda);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-top: 1.5rem;
    box-shadow: var(--sombra-md);
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
}
.action-placeholder {
    font-size: 0.875rem;
    color: var(--texto-secondary);
    font-weight: 500;
    padding: 0.6rem 1rem;
    background: linear-gradient(180deg, var(--creme) 0%, var(--creme-escuro) 100%);
    border-radius: 10px;
    border: 1px solid var(--borda);
}

/* Botões */
.stButton > button {
    background: linear-gradient(180deg, var(--ouro) 0%, var(--ouro-escuro) 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.25rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    box-shadow: var(--sombra-md) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    box-shadow: var(--sombra-lg) !important;
    transform: translateY(-1px) !important;
}

/* Esconder info boxes feios — usar mensagem customizada */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fffefb 0%, var(--creme) 100%) !important;
    border-right: 1px solid var(--borda) !important;
    box-shadow: 4px 0 12px rgba(61,41,20,0.06) !important;
}
[data-testid="stSidebar"] .stMarkdown { color: var(--texto-primary) !important; }

.data-source {
    font-size: 0.8125rem;
    color: var(--texto-secondary);
    margin-bottom: 1rem;
    font-weight: 500;
}

/* Abas — chocolates: fundo creme, bordas douradas, sombras */
.stTabs [data-baseweb="tab-list"] {
    flex-wrap: wrap !important;
    gap: 8px !important;
    background: linear-gradient(180deg, var(--creme-escuro) 0%, var(--creme) 100%) !important;
    padding: 14px 14px 0 14px !important;
    border-radius: 14px 14px 0 0 !important;
    border: 1px solid var(--borda) !important;
    border-bottom: none !important;
    box-shadow: var(--sombra-md) !important;
}
.stTabs [data-baseweb="tab"] span, .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] div {
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    color: var(--texto-secondary) !important;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.6) !important;
    font-weight: 500 !important;
    color: var(--texto-secondary) !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 10px 16px !important;
    border: 1px solid rgba(212,196,168,0.6) !important;
    border-bottom: none !important;
    box-shadow: 0 -1px 2px rgba(0,0,0,0.04) !important;
}
.stTabs [data-baseweb="tab"]:hover, .stTabs [data-baseweb="tab"]:hover * {
    color: var(--texto-primary) !important;
    background: rgba(255,255,255,0.9) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255,255,255,0.9) !important;
    border-color: var(--borda-ouro) !important;
    box-shadow: 0 -2px 8px rgba(201,162,39,0.15) !important;
}
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] * {
    background: white !important;
    color: var(--chocolate) !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    border: 1px solid var(--borda) !important;
    border-bottom: 2px solid white !important;
    box-shadow: 0 -3px 12px rgba(61,41,20,0.1), 0 2px 0 0 var(--ouro) !important;
    margin-bottom: -1px !important;
}
/* Conteúdo das abas — card creme com borda */
.stTabs [data-baseweb="tab-panel"], .stTabs > div > div:last-child {
    background: linear-gradient(180deg, white 0%, var(--creme) 100%) !important;
    border: 1px solid var(--borda) !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
    padding: 1.25rem !important;
    box-shadow: var(--sombra-md) !important;
}

/* Responsivo e acessibilidade */
@media (max-width: 768px) {
    .logo-container h1 { font-size: 1.8rem !important; letter-spacing: 0.08em !important; }
    .logo-container .subtitle { font-size: 0.85rem !important; letter-spacing: 0.2em !important; }
}
/* Contraste para acessibilidade */
.stButton > button:focus, .stTextInput input:focus, .stTextArea textarea:focus {
    outline: 2px solid var(--ouro) !important;
    outline-offset: 2px !important;
}

/* Breadcrumb e navegação */
.breadcrumb { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: var(--texto-medio); margin-bottom: 1rem; }
.breadcrumb a { color: var(--ouro); text-decoration: none; font-weight: 500; }
.breadcrumb a:hover { text-decoration: underline; }

/* Status do pedido */
.status-pedido { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; padding: 0.75rem 1rem; background: linear-gradient(180deg, #fffefb 0%, var(--creme) 100%); border: 1px solid var(--borda); border-radius: 12px; box-shadow: var(--sombra-sm); }
.status-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.8125rem; font-weight: 500; }
.status-badge.itens { background: rgba(59,130,246,0.12); color: #2563eb; }
.status-badge.total { background: rgba(16,185,129,0.12); color: #059669; }
.status-badge.rascunho { background: rgba(245,158,11,0.12); color: #b45309; font-weight: 500; }

</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def _carregar_produtos_arquivo(path_resolvido: str) -> list:
    """Cache só para planilha em disco (caminho estável)."""
    return extrair_todos(path_resolvido)


def carregar_produtos_ui() -> tuple[list, str]:
    """Se GRAMADOWAY_API_URL estiver definida, busca produtos na API; senão disco/upload."""
    if obter_url_api():
        try:
            return carregar_produtos_api()
        except Exception as e:
            st.error(f"Erro ao falar com a API: {e}")
            return [], ""
    blob = st.session_state.get("_planilha_bytes")
    if blob:
        try:
            return extrair_todos_de_bytes(blob), "upload_sessao.xlsx"
        except Exception as e:
            st.error(f"Erro ao ler planilha enviada: {e}")
            return [], ""
    try:
        path = _caminho_planilha()
        prod = _carregar_produtos_arquivo(str(path.resolve()))
        return prod, str(path)
    except FileNotFoundError:
        return [], ""


def _render_login():
    """Tela inicial: primeiro usuário ou login."""
    st.markdown("### Gramadoway — Acesso")
    if not auth.tem_usuarios():
        st.info("Primeiro acesso: crie o usuário principal (ex.: vendedor ou admin).")
        with st.form("primeiro_usuario"):
            nu = st.text_input("Login", placeholder="ex: maria_vendas", help="3–32 caracteres: letras minúsculas, números e _")
            p1 = st.text_input("Senha", type="password")
            p2 = st.text_input("Repita a senha", type="password")
            if st.form_submit_button("Criar e entrar"):
                if p1 != p2:
                    st.error("As senhas não coincidem.")
                else:
                    try:
                        auth.registrar_primeiro_usuario(nu, p1)
                        u = auth.verificar_login(nu, p1)
                        if u:
                            st.session_state[auth.SESSION_KEY] = u
                            st.session_state.pop("df_pedido", None)
                            st.rerun()
                    except Exception as e:
                        st.error(str(e))
        return
    with st.form("login"):
        lg = st.text_input("Usuário", placeholder="seu login")
        pw = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            u = auth.verificar_login(lg, pw)
            if u:
                st.session_state[auth.SESSION_KEY] = u
                st.session_state.pop("df_pedido", None)
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")


def main():
    usuario = st.session_state.get(auth.SESSION_KEY)
    if not usuario:
        _render_login()
        return

    # Sidebar — Resumo rápido + Histórico + logout + novo usuário
    with st.sidebar:
        st.caption(f"Logado: **{usuario}**")
        if st.button("Sair", key="btn_logout"):
            st.session_state.pop(auth.SESSION_KEY, None)
            st.session_state.pop("df_pedido", None)
            st.rerun()
        with st.expander("Cadastrar usuário"):
            with st.form("reg_sidebar"):
                nu = st.text_input("Login do colega", key="sb_reg_l")
                p1 = st.text_input("Senha", type="password", key="sb_reg_p1")
                p2 = st.text_input("Repita", type="password", key="sb_reg_p2")
                if st.form_submit_button("Cadastrar"):
                    if p1 != p2:
                        st.error("Senhas diferentes.")
                    else:
                        try:
                            auth.registrar_usuario(nu, p1)
                            st.success("Usuário criado.")
                        except Exception as e:
                            st.error(str(e))
        st.markdown("---")
        if "df_pedido" in st.session_state:
            n_itens = int((st.session_state.df_pedido["Qtde"] > 0).sum())
            if n_itens > 0:
                tot = st.session_state.df_pedido["Total"].sum()
                tot_fmt = formatar_moeda(float(tot))
                st.markdown(f"**Pedido atual:** {n_itens} itens • {tot_fmt}")
        st.markdown("---")
        st.markdown("### Histórico de Pedidos")
        historico = carregar_historico(usuario)
        if historico:
            for i, p in enumerate(historico[:10]):
                cli = p.get("cliente", {})
                nome = (cli.get("Razão Social") or cli.get("Fantasia") or "Orçamento")
                nome = nome[:24] + ".." if len(nome) > 24 else nome
                total = p.get("total", 0)
                total_fmt = formatar_moeda(total)
                with st.container():
                    st.markdown(f"**{nome}**")
                    st.caption(f"{p.get('data', '')} • {len(p.get('itens', []))} itens • {total_fmt}")
                    pdf_bytes = gerar_pdf(p)
                    if pdf_bytes:
                        st.download_button("PDF", pdf_bytes, f"Orcamento_{p.get('id','')}.pdf", "application/pdf", key=f"pdf_{usuario}_{i}")
                    st.markdown("---")
        else:
            st.caption("Nenhum pedido salvo ainda.")

    # Logo central — GRAMADOWAY com ícone SVG (st.html evita wrapper markdown que escurece)
    try:
        st.html("""
        <div class="logo-container">
            <div class="logo-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="4" y="8" width="40" height="32" rx="4" stroke="#C9A227" stroke-width="2" fill="none"/>
                    <path d="M12 20 L24 28 L36 20" stroke="#E5D4A1" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="24" cy="24" r="4" fill="#C9A227"/>
                </svg>
            </div>
            <h1 style="color:#fff!important;font-family:Inter,sans-serif;font-size:2.25rem;font-weight:700;margin:0;letter-spacing:.05em;">GRAMADOWAY</h1>
            <p class="subtitle">Chocolates Artesanais</p>
            <p class="tagline">Sistema de orçamento • Digite as quantidades • Total calculado automaticamente</p>
        </div>
        """)
    except AttributeError:
        st.markdown("""
        <div class="logo-container">
            <div class="logo-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="4" y="8" width="40" height="32" rx="4" stroke="#C9A227" stroke-width="2" fill="none"/>
                    <path d="M12 20 L24 28 L36 20" stroke="#E5D4A1" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="24" cy="24" r="4" fill="#C9A227"/>
                </svg>
            </div>
            <h1 style="color:#fff!important;">GRAMADOWAY</h1>
            <p class="subtitle">Chocolates Artesanais</p>
            <p class="tagline">Sistema de orçamento • Digite as quantidades • Total calculado automaticamente</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("##### Planilha de preços")
    dr = data_root()
    api_u = obter_url_api()
    if api_u:
        st.success(f"Produtos vêm da **API**: `{api_u}` — envie a planilha pelo Swagger em **/docs** (`POST /v1/planilha`) ou mantenha `data/planilha.xlsx` no servidor da API.")
    else:
        st.caption(
            f"**Modo direto:** coloque o `.xlsx` em `{dr}` (ex.: `planilha.xlsx`) ou envie abaixo. "
            f"**Modo API (opcional):** defina `GRAMADOWAY_API_URL` e suba a API — veja `GUIA_API.md`."
        )
        c_up, c_lim = st.columns([2, 1])
        with c_up:
            arq = st.file_uploader("Enviar Excel (.xlsx)", type=["xlsx"], key="gw_upload_planilha")
            if arq is not None:
                st.session_state["_planilha_bytes"] = arq.getvalue()
                st.session_state.pop("df_pedido", None)
        with c_lim:
            if st.session_state.get("_planilha_bytes") and st.button("Usar arquivo da pasta data/", key="gw_clear_upload"):
                st.session_state.pop("_planilha_bytes", None)
                st.session_state.pop("df_pedido", None)
                st.cache_data.clear()
                st.rerun()

    with st.spinner("Carregando produtos..."):
        produtos, path_planilha = carregar_produtos_ui()
    if not produtos:
        st.warning(
            "Nenhuma planilha encontrada. Envie um .xlsx acima ou copie o arquivo para a pasta **data** "
            f"do projeto (`{dr}`) e clique em Recarregar."
        )
        if st.button("Recarregar"):
            st.cache_data.clear()
            st.rerun()
        return

    nome_arquivo = (
        Path(path_planilha).name if ("/" in path_planilha or "\\" in path_planilha) else path_planilha
    )
    st.markdown(f'<p class="data-source">Dados: {nome_arquivo}</p>', unsafe_allow_html=True)

    # Seção CLIENTE — layout agrupado, máscaras, CEP, clientes recorrentes
    st.markdown('<div class="client-section">CLIENTE</div>', unsafe_allow_html=True)

    # Cliente recorrente
    MAPEAMENTO_CLIENTE = {
        "Razão Social": "razao", "Fantasia": "fantasia", "CNPJ": "cnpj", "Fone": "fone",
        "Endereço": "endereco", "Cidade": "cidade", "Bairro": "bairro", "CEP": "cep",
        "E-mail": "email", "Contato": "contato", "I. Estadual": "ie",
        "Cond. Pagto": "cond_pagto", "Frete": "frete", "Observação": "obs",
    }
    clientes = carregar_clientes(usuario)
    if clientes:
        opcoes = ["-- Novo cliente --"] + [f"{c.get('Razão Social') or c.get('Fantasia') or 'Cliente'} ({str(c.get('CNPJ',''))[:18] or 'sem CNPJ'})" for c in clientes[:20]]
        sel = st.selectbox("Cliente salvo", opcoes, key="sel_cliente")
        if sel and sel != "-- Novo cliente --":
            idx = opcoes.index(sel) - 1
            cli = clientes[idx]
            for k, sk in MAPEAMENTO_CLIENTE.items():
                if k in cli and cli[k]:
                    st.session_state[sk] = str(cli[k])

    # Aplicar máscaras nos campos (formatação automática)
    for key, fn in [("cnpj", mascara_cnpj), ("fone", mascara_telefone), ("cep", mascara_cep)]:
        if key in st.session_state and st.session_state[key]:
            fmt = fn(st.session_state[key])
            if fmt != st.session_state[key]:
                st.session_state[key] = fmt

    st.markdown('<div class="client-form">', unsafe_allow_html=True)
    st.markdown("**Dados básicos**")
    col_esq, col_dir = st.columns(2)
    with col_esq:
        razao = st.text_input("Razão Social", placeholder="Nome da empresa", key="razao")
        cnpj = st.text_input("CNPJ", placeholder="00.000.000/0001-00", key="cnpj")
        endereco = st.text_input("Endereço", placeholder="Rua, número, bairro", key="endereco")
        cidade = st.text_input("Cidade", placeholder="Cidade - UF", key="cidade")
    with col_dir:
        fantasia = st.text_input("Fantasia", placeholder="Nome fantasia", key="fantasia")
        fone = st.text_input("Fone", placeholder="(00) 00000-0000", key="fone")
        bairro = st.text_input("Bairro", placeholder="Bairro", key="bairro")
        cep = st.text_input("CEP", placeholder="00000-000", key="cep")
    st.markdown("**Contato e condições**")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        email = st.text_input("E-mail", placeholder="contato@empresa.com.br", key="email")
        contato = st.text_input("Contato", placeholder="Nome do contato", key="contato")
        frete = st.text_input("Frete", placeholder="CIF, FOB...", key="frete")
    with col_c2:
        ie = st.text_input("I. Estadual", placeholder="Inscrição estadual", key="ie")
        cond_pagto = st.text_input("Cond. Pagto", placeholder="À vista, 30 dias...", key="cond_pagto")
        obs = st.text_area("Observação", placeholder="Instruções especiais...", height=60, key="obs")

    st.session_state.cliente = {
        "Razão Social": razao, "Fantasia": fantasia, "CNPJ": cnpj, "Fone": fone,
        "Endereço": endereco, "Cidade": cidade, "Bairro": bairro, "CEP": cep,
        "E-mail": email, "Contato": contato, "I. Estadual": ie,
        "Cond. Pagto": cond_pagto, "Frete": frete, "Observação": obs,
    }

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class="instrucoes-box">
        <p class="instrucoes-texto">Digite a quantidade desejada na coluna <strong>Qtde</strong>. O total é calculado automaticamente. KG = quilogramas | UN = unidades | PCT = pacotes.</p>
        <details class="como-funciona">
            <summary>Como funciona: KG, UN, PCT e SACO</summary>
            <table class="tabela-unidades">
                <thead><tr><th>Un.</th><th>Significado</th><th>Você digita</th><th>Exemplo</th></tr></thead>
                <tbody>
                    <tr><td>KG</td><td>Preço por quilograma</td><td>Quantidade em kg</td><td>2,5 kg de barras</td></tr>
                    <tr><td>UN</td><td>Preço por unidade</td><td>Quantidade de unidades</td><td>10 bombons</td></tr>
                    <tr><td>PCT</td><td>Preço por pacote</td><td>Quantidade de pacotes</td><td>5 pacotes</td></tr>
                    <tr><td>SACO</td><td>Preço por saco (ex: 25 un)</td><td>Quantidade de sacos</td><td>3 sacos de trufas</td></tr>
                </tbody>
            </table>
            <p class="formula-total"><strong>Total</strong> = Qtde × Preço (por aquela unidade).</p>
        </details>
    </div>
    """, unsafe_allow_html=True)

    # DataFrame com Qtde editável
    df = pd.DataFrame(produtos)
    df["preco_por"] = df["un"].map({"KG": "R$/kg", "UN": "R$/un", "SACO": "R$/saco", "PCT": "R$/pct"}).fillna("R$/un")
    if "df_pedido" not in st.session_state:
        df["Qtde"] = 0.0
        df["Total"] = 0.0
        df["un"] = df["un"].fillna("UN").replace("", "UN")
        st.session_state.df_pedido = df.copy()
        # Restaurar rascunho se existir
        rascunho = carregar_rascunho(usuario)
        if rascunho:
            for item in rascunho.get("itens", []):
                prod, preco, qtd = item.get("produto"), item.get("preco"), float(item.get("Qtde", 0) or 0)
                if qtd > 0 and prod is not None:
                    mask = (st.session_state.df_pedido["produto"] == prod) & (st.session_state.df_pedido["preco"] == float(preco or 0))
                    if mask.any():
                        idx = mask.idxmax()
                        st.session_state.df_pedido.loc[idx, "Qtde"] = qtd
                        st.session_state.df_pedido.loc[idx, "Total"] = float(item.get("Total", 0) or qtd * float(preco or 0))
            cli = rascunho.get("cliente", {})
            for k, sk in [("Razão Social","razao"),("Fantasia","fantasia"),("CNPJ","cnpj"),("Fone","fone"),("Endereço","endereco"),("Cidade","cidade"),("Bairro","bairro"),("CEP","cep"),("E-mail","email"),("Contato","contato"),("I. Estadual","ie"),("Cond. Pagto","cond_pagto"),("Frete","frete"),("Observação","obs")]:
                if cli.get(k):
                    st.session_state[sk] = str(cli[k])
    else:
        aplicar_totais_pedido(st.session_state.df_pedido)

    # Garante coluna preco_por
    if "preco_por" not in st.session_state.df_pedido.columns:
        st.session_state.df_pedido["preco_por"] = st.session_state.df_pedido["un"].map(
            {"KG": "R$/kg", "UN": "R$/un", "SACO": "R$/saco", "PCT": "R$/pct"}
        ).fillna("R$/un")

    # Abas como na planilha — nomes iguais, agrupadas
    # Mapeamento: categoria interna -> nome da aba (como na planilha)
    ABA_NOMES = {
        "Personalizados": "Personalizados",
        "Barras ao Leite": "Barras",
        "Barras Branco": "Barras",
        "Bombons Líquidos": "Bombons liquidos",
        "Bombons L�quidos": "Bombons liquidos",
        "Bombons 12gr": "Bombons 12gr",
        "Trufas": "Trufas",
        "Degustação": "Degustação",
        "Degusta��o": "Degustação",
        "50% Cacau": "Planilha9",
        "Bombons Especiais": "Planilha9",
    }
    df_ped = st.session_state.df_pedido
    # Mapeia categoria -> aba (inclui variações de encoding)
    def map_aba(cat):
        s = str(cat)
        if cat in ABA_NOMES:
            return ABA_NOMES[cat]
        if "Bombons" in s and ("liquid" in s.lower() or "quidos" in s.lower()):
            return "Bombons liquidos"
        if "Degust" in s:
            return "Degustação"
        return cat
    df_ped["aba"] = df_ped["categoria"].apply(map_aba)
    abas_unicas = ["Personalizados", "Barras", "Bombons liquidos", "Bombons 12gr", "Trufas", "Degustação", "Planilha9"]
    abas_unicas = [a for a in abas_unicas if (df_ped["aba"] == a).any()]

    # Busca inteligente — atalho rápido: "produto 5" adiciona 5
    col_atalho, col_busca = st.columns(2)
    with col_atalho:
        atalho = st.text_input(
            "Adicionar rápido",
            placeholder="Ex: barras 2,5 ou avião 10 — produto e quantidade",
            key="atalho_rapido",
            help="Digite nome ou código do produto, espaço, e a quantidade.",
        )
    with col_busca:
        busca = st.text_input("Buscar produto", placeholder="Digite nome ou código do produto...", key="busca_global")
    if atalho:
        parsed = parsear_atalho(atalho)
        if parsed:
            termo, qtd = parsed
            df_busca = buscar_produtos(df_ped, termo, limite=5)
            if len(df_busca) > 0:
                idx = df_busca.index[0]
                if idx in st.session_state.df_pedido.index:
                    antigo = float(st.session_state.df_pedido.loc[idx, "Qtde"])
                    novo = antigo + qtd
                    st.session_state.df_pedido.loc[idx, "Qtde"] = novo
                    aplicar_totais_pedido(st.session_state.df_pedido)
                    st.success(f"Adicionado: {df_busca.iloc[0]['produto'][:40]} +{qtd}")
                    if "atalho_rapido" in st.session_state:
                        del st.session_state["atalho_rapido"]
                    st.rerun()

    # Abas visuais — Busca rápida primeiro, depois categorias + Orçamento
    tab_labels = ["Busca rápida"] + [f"{a} ({len(df_ped[df_ped['aba']==a])})" for a in abas_unicas] + ["Orçamento"]
    tabs = st.tabs(tab_labels)
    edited_frames = []
    num_abas_produtos = len(abas_unicas)

    # Tab 0: Busca rápida — itens selecionados (Qtde>0) sobem para o topo
    with tabs[0]:
        df_busca_full = buscar_produtos(df_ped, busca or " ", limite=80)
        if len(df_busca_full) > 0:
            df_busca_full = df_busca_full.sort_values(by="Qtde", ascending=False)
        st.caption(f"Busca inteligente em {len(df_ped)} produtos. Itens com quantidade primeiro. Total atualiza ao confirmar a edição na célula.")
        if len(df_busca_full) > 0:
            df_edit_busca = df_busca_full[["produto", "un", "preco_por", "preco", "Qtde", "Total"]].copy()
            edited_busca = st.data_editor(
                df_edit_busca,
                column_config={
                    "produto": st.column_config.TextColumn("Produto", disabled=True),
                    "un": st.column_config.TextColumn("Un.", disabled=True),
                    "preco_por": st.column_config.TextColumn("Preço por", disabled=True),
                    "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f", disabled=True),
                    "Qtde": st.column_config.NumberColumn("Qtde", min_value=0.0, step=0.5, format="%.2f"),
                    "Total": st.column_config.NumberColumn("Total", format="R$ %.2f", disabled=True),
                },
                use_container_width=True,
                height=450,
                key="tab_busca",
            )
            for idx in edited_busca.index:
                if idx in st.session_state.df_pedido.index:
                    q = float(edited_busca.loc[idx, "Qtde"]) if pd.notna(edited_busca.loc[idx, "Qtde"]) else 0.0
                    q = max(0.0, q)
                    st.session_state.df_pedido.loc[idx, "Qtde"] = q
        else:
            st.markdown("""
            <div class="action-placeholder" style="margin:0.5rem 0;">
                Digite na busca acima para filtrar. Ex: barras, avião, 480.
            </div>
            """, unsafe_allow_html=True)

    col_config = {
        "produto": st.column_config.TextColumn("Produto", disabled=True),
        "un": st.column_config.TextColumn("Un.", disabled=True, help="KG=quilograma | UN=unidade | SACO=saco"),
        "preco_por": st.column_config.TextColumn("Preço por", disabled=True),
        "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f", disabled=True),
        "Qtde": st.column_config.NumberColumn("Qtde", min_value=0.0, step=0.5, format="%.2f"),
        "Total": st.column_config.NumberColumn("Total", format="R$ %.2f", disabled=True),
    }

    for i, aba in enumerate(abas_unicas):
        with tabs[i + 1]:
            df_tab = df_ped[df_ped["aba"] == aba].copy()
            if busca:
                df_tab = df_tab[df_tab["produto"].str.contains(busca, case=False, na=False)]
            df_tab = df_tab.sort_values(by="Qtde", ascending=False)
            st.caption("Un. = KG | UN | SACO — Total = Qtde × Preço (atualiza ao sair da célula ou Enter)")
            if len(df_tab) > 0:
                df_display = df_tab[["produto", "un", "preco_por", "preco", "Qtde", "Total"]].copy()
                edited = st.data_editor(
                    df_display,
                    column_config=col_config,
                    use_container_width=True,
                    height=400,
                    key=f"tab_{i}",
                )
                edited_frames.append((aba, edited))
            else:
                st.markdown("""
                <div class="action-placeholder" style="margin:0.5rem 0;">
                    Nenhum produto encontrado.
                </div>
                """, unsafe_allow_html=True)

    # Aba Orçamento — resumo filtrado (só itens com qtde), útil para imprimir/enviar
    with tabs[num_abas_produtos + 1]:
        itens_orc = df_ped[df_ped["Qtde"] > 0]
        if len(itens_orc) > 0:
            df_orc = itens_orc[["Qtde", "produto", "un", "preco", "Total"]].copy()
            df_orc.columns = ["Qtde", "Produto", "Un.", "Preço", "Total"]
            st.caption("Resumo para impressão ou envio ao fornecedor. Apenas itens com quantidade.")
            st.dataframe(df_orc, use_container_width=True, height=min(350, 80 + len(itens_orc) * 38))
            tot_orc = float(itens_orc["Total"].sum())
            tot_fmt = f"R$ {tot_orc:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f'<div class="total-box" style="margin-top:1.2rem;">TOTAL GERAL: {tot_fmt}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="action-placeholder" style="margin:0.5rem 0;">
                Adicione quantidades nos produtos para gerar o orçamento.
            </div>
            """, unsafe_allow_html=True)

    for aba, edited in edited_frames:
        for idx in edited.index:
            if idx in st.session_state.df_pedido.index:
                try:
                    q = float(edited.loc[idx, "Qtde"]) if pd.notna(edited.loc[idx, "Qtde"]) else 0.0
                except (ValueError, TypeError):
                    q = 0.0
                q = max(0.0, q)
                st.session_state.df_pedido.loc[idx, "Qtde"] = q
    aplicar_totais_pedido(st.session_state.df_pedido)

    total_geral = float(round(float(st.session_state.df_pedido["Total"].sum()), 2))
    itens_pedido = st.session_state.df_pedido[st.session_state.df_pedido["Qtde"] > 0]

    # Rascunho automático
    if len(itens_pedido) > 0:
        cli = st.session_state.get("cliente", {})
        itens_rasc = [{"produto": r["produto"], "Qtde": r["Qtde"], "preco": r["preco"], "Total": r["Total"], "un": r["un"]} for _, r in itens_pedido.iterrows()]
        salvar_rascunho(usuario, cli, itens_rasc, float(total_geral))

    # Resumo do pedido (apenas itens com quantidade)
    if len(itens_pedido) > 0:
        st.markdown("---")
        st.markdown("**RESUMO DO PEDIDO** (itens selecionados)")
        df_resumo = itens_pedido[["Qtde", "un", "produto", "preco", "Total"]].copy()
        df_resumo.columns = ["Qtde", "Un.", "Produto", "Preço unit.", "Total"]
        st.dataframe(df_resumo, use_container_width=True, height=min(200, 50 + len(itens_pedido) * 35))
        st.caption(f"Subtotal dos itens acima: R$ {itens_pedido['Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Status do pedido — badges visuais (quando tem itens)
    if len(itens_pedido) > 0:
        total_fmt = f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        rascunho = carregar_rascunho(usuario)
        tem_rascunho = rascunho is not None and len(rascunho.get("itens", [])) > 0
        st.markdown(f"""
        <div class="status-pedido">
            <span class="status-badge itens">{len(itens_pedido)} itens no pedido</span>
            <span class="status-badge total">{total_fmt}</span>
            {"<span class=\"status-badge rascunho\">Rascunho salvo automaticamente</span>" if tem_rascunho else ""}
        </div>
        """, unsafe_allow_html=True)

    # Valor total — apenas aqui embaixo, tipografia nítida
    st.markdown("---")
    total_fmt = f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"""
    <div class="total-box">
        VALOR TOTAL DO PEDIDO: {total_fmt}
    </div>
    """, unsafe_allow_html=True)

    # Ações — barra organizada: Limpar | Salvar | PDF
    df_exp = itens_pedido[["Qtde", "codigo", "produto", "un", "preco", "Total"]].copy() if len(itens_pedido) > 0 else None
    if df_exp is not None:
        df_exp = df_exp.copy()
        aplicar_totais_pedido(df_exp)
        df_exp.columns = ["Qtde", "Código", "Produto", "Un.", "Preço", "Total"]
        total_exp = df_exp["Total"].sum()
        itens_list = df_exp[["Qtde", "Un.", "Produto", "Preço", "Total"]].to_dict("records")
        cli = st.session_state.get("cliente", {})

    # Barra de ações — organização clara
    tem_itens = len(itens_pedido) > 0
    st.markdown("""
    <div style="margin:1.5rem 0 0.8rem 0; font-size:0.85rem; font-weight:600; color:#6b6560; letter-spacing:0.08em; text-transform:uppercase;">
        Ações
    </div>
    """, unsafe_allow_html=True)
    if not tem_itens:
        st.markdown("""
        <div class="action-placeholder" style="margin:0 0 1rem 0; text-align:center;">
            Adicione quantidades aos itens acima para habilitar Salvar e exportar PDF.
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1.5])
    with col1:
        if st.session_state.get("_confirmar_limpar"):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sim, limpar tudo", key="btn_limpar_ok"):
                    if "df_pedido" in st.session_state:
                        st.session_state.df_pedido["Qtde"] = 0.0
                        st.session_state.df_pedido["Total"] = 0.0
                    limpar_rascunho(usuario)
                    st.session_state["_confirmar_limpar"] = False
                    st.rerun()
            with c2:
                if st.button("Cancelar", key="btn_limpar_cancel"):
                    st.session_state["_confirmar_limpar"] = False
                    st.rerun()
        elif st.button("Limpar", key="btn_limpar"):
            st.session_state["_confirmar_limpar"] = True
            st.rerun()
    with col2:
        if tem_itens:
            if st.button("Salvar no histórico", key="btn_salvar"):
                salvar_pedido(usuario, cli, itens_list, float(total_exp))
                salvar_cliente(usuario, cli)
                limpar_rascunho(usuario)
                st.success("Pedido e cliente salvos!")
        else:
            st.markdown('<p style="font-size:0.9rem;color:#8a8580;text-align:center;margin:0.5rem 0;">Salvar</p>', unsafe_allow_html=True)
    with col3:
        if tem_itens:
            pedido_atual = {"id": "", "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "cliente": cli, "itens": itens_list, "total": float(total_exp)}
            pdf_bytes = gerar_pdf(pedido_atual)
            if pdf_bytes:
                st.download_button("Exportar pedido com PDF moderno e organizado", data=pdf_bytes,
                    file_name=f"Orcamento_Gramadoway_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    help="PDF com todos os dados do cliente e itens — pronto para envio",
                    key="btn_pdf")
            else:
                st.caption("Instale: pip install reportlab")
        else:
            st.markdown('<p style="font-size:0.9rem;color:#8a8580;text-align:center;margin:0.5rem 0;">Exportar PDF</p>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
