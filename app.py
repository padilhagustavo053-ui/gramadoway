#!/usr/bin/env python3
"""
Sistema de Pedidos Gramadoway — Potente, robusto e grandioso
Design inspirado em formulários profissionais de chocolates artesanais.
"""
import streamlit as st
import streamlit.components.v1 as components
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

inject_streamlit_secrets_into_environ()
migrate_legacy_pedidos_folder()

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

# Som suave (Web Audio) — iframe 0px após clicar "Entrar no sistema"
GW_CHIME_HTML = """
<!DOCTYPE html><html><body style="margin:0;padding:0;overflow:hidden;">
<script>
(function () {
  try {
    var C = new (window.AudioContext || window.webkitAudioContext)();
    var o = C.createOscillator();
    var g = C.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(392, C.currentTime);
    o.frequency.exponentialRampToValueAtTime(523.25, C.currentTime + 0.08);
    o.frequency.exponentialRampToValueAtTime(659.25, C.currentTime + 0.2);
    g.gain.setValueAtTime(0.0001, C.currentTime);
    g.gain.exponentialRampToValueAtTime(0.065, C.currentTime + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, C.currentTime + 0.42);
    o.connect(g);
    g.connect(C.destination);
    o.start();
    o.stop(C.currentTime + 0.45);
  } catch (e) {}
})();
</script>
</body></html>
"""


st.set_page_config(
    page_title="Gramadoway — Formulário de Pedido",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS — Letras fortes, grossas, bem visíveis (font-weight 600–700)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,600&family=Inter:wght@400;500;600;700;800&display=swap');

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
    --texto-primary: #120d0a;
    --texto-secondary: #2d241c;
    --texto-muted: #4a3f36;
    --borda: #d4c4a8;
    --borda-ouro: rgba(201,162,39,0.5);
    --borda-focus: var(--ouro);
    --sombra-sm: 0 2px 6px rgba(61,41,20,0.07);
    --sombra-md: 0 6px 20px rgba(61,41,20,0.1), 0 2px 8px rgba(201,162,39,0.08);
    --sombra-lg: 0 16px 40px rgba(61,41,20,0.14), 0 6px 16px rgba(201,162,39,0.1);
    --sombra-press: inset 0 2px 6px rgba(0,0,0,0.12);
}

/* ========== Launch / boas-vindas (simples, centrado, sem Lottie) ========== */
#gw-launch-anchor { position: absolute; width: 0; height: 0; pointer-events: none; }
body:has(#gw-launch-anchor) [data-testid="stHeader"] { display: none !important; }
body:has(#gw-launch-anchor) [data-testid="stSidebar"] { display: none !important; }

/* Conteúdo centralizado — evita texto “cortado” à esquerda no Cloud */
body:has(#gw-launch-anchor) .stMainBlockContainer {
    max-width: 28rem !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding: 1.5rem 1.25rem 2.5rem !important;
    width: 100% !important;
    box-sizing: border-box !important;
}

/* Fundo: slate frio, sóbrio (sem roxo/dourado pesado) */
body:has(#gw-launch-anchor) .stApp {
    background: linear-gradient(165deg, #0b1220 0%, #111827 38%, #0f172a 100%) !important;
}
body:has(#gw-launch-anchor) [data-testid="stAppViewContainer"],
body:has(#gw-launch-anchor) [data-testid="stMain"],
body:has(#gw-launch-anchor) .main {
    background: transparent !important;
}

.gw-launch-shell {
    text-align: center;
    padding: 1.75rem 1.5rem 1.5rem;
    margin: 0 auto 1.25rem;
    max-width: 100%;
    border-radius: 20px;
    background: rgba(15,23,42,0.65);
    border: 1px solid rgba(148,163,184,0.22);
    box-shadow: 0 24px 48px rgba(0,0,0,0.35);
    position: relative;
}
.gw-launch-inner { position: relative; z-index: 1; }
.gw-launch-mark {
    margin: 0 auto 1.25rem;
    display: flex;
    justify-content: center;
}
.gw-launch-kicker {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #94a3b8 !important;
    margin-bottom: 0.75rem;
}
.gw-launch-title {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: clamp(1.75rem, 6vw, 2.35rem);
    font-weight: 700;
    line-height: 1.2;
    color: #f8fafc !important;
    margin: 0 0 0.65rem 0;
}
.gw-launch-sub {
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem;
    font-weight: 500;
    color: #cbd5e1 !important;
    margin: 0;
    line-height: 1.55;
}
.gw-launch-hint {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem;
    font-weight: 500;
    color: #64748b !important;
    margin: 1.25rem 0 0 0;
    text-align: center;
}
@keyframes gw-fade-up {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Botões do splash: sempre visíveis, largura total, sem herança estranha */
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton {
    width: 100% !important;
}
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton > button {
    width: 100% !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    min-height: 3.1rem !important;
    font-size: 1rem !important;
    opacity: 1 !important;
    visibility: visible !important;
    background: rgba(30,41,59,0.95) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(148,163,184,0.5) !important;
}
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton > button[kind="primary"],
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton > button[kind="primary"] * {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #d4a20c, #b8860b) !important;
    border: none !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35) !important;
}
/* Secundário: Streamlit pinta o rótulo interno com theme textColor — forçar branco no botão e em tudo lá dentro */
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton > button[kind="secondary"],
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton > button[kind="secondary"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stButton > button[kind="secondary"] {
    background: rgba(15,23,42,0.5) !important;
    border: 2px solid rgba(248,250,252,0.65) !important;
    box-shadow: none !important;
}

/* Cartão login — após launch */
.gw-login-card {
    background: linear-gradient(165deg, rgba(255,255,255,0.97) 0%, var(--creme) 100%);
    border: 1px solid var(--borda);
    border-radius: 18px;
    padding: 1.75rem 1.5rem 2rem;
    margin: 1.25rem auto 2rem;
    max-width: 520px;
    box-shadow: var(--sombra-lg);
}


/* Tipografia só na área principal — NÃO usar * global (quebra ícones Material na sidebar multipage) */
section[data-testid="stMain"], section[data-testid="stMain"] button, section[data-testid="stMain"] input,
section[data-testid="stMain"] textarea, section[data-testid="stMain"] label {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    -webkit-font-smoothing: subpixel-antialiased !important;
    -moz-osx-font-smoothing: auto !important;
    text-rendering: geometricPrecision !important;
}
section[data-testid="stMain"] .stMarkdown, section[data-testid="stMain"] p,
section[data-testid="stMain"] span:not([class*="material"]):not([data-testid="stIconMaterial"]) {
    font-weight: 400 !important;
    color: var(--texto-primary) !important;
}

/* Splash: ganhar ao CSS acima — letras claras no fundo escuro */
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stMarkdown,
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stMarkdown p,
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stMarkdown h1,
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stMarkdown span,
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stMarkdown div {
    color: #f8fafc !important;
}
body:has(#gw-launch-anchor) section[data-testid="stMain"] .gw-launch-kicker { color: #94a3b8 !important; }
body:has(#gw-launch-anchor) section[data-testid="stMain"] .gw-launch-title { color: #f8fafc !important; }
body:has(#gw-launch-anchor) section[data-testid="stMain"] .gw-launch-sub { color: #cbd5e1 !important; }
body:has(#gw-launch-anchor) section[data-testid="stMain"] .gw-launch-hint { color: #64748b !important; }
body:has(#gw-launch-anchor) section[data-testid="stMain"] .stMarkdown strong { color: #ffffff !important; }

/* Página de login (após splash): leve contraste no fundo */
body:has(#gw-login-anchor):not(:has(#gw-launch-anchor)) .stApp {
    background: linear-gradient(180deg, #faf7f2 0%, #f5f0e8 100%) !important;
}

/* Logo: título branco — override qualquer herança */
.logo-container h1, div.logo-container h1, .logo-container > h1 { color: #ffffff !important; }
section[data-testid="stMain"] .stMarkdown strong { font-weight: 600 !important; }
section[data-testid="stMain"] label {
    font-weight: 500 !important; color: var(--texto-primary) !important; font-size: 0.875rem !important;
}
section[data-testid="stMain"] .stCaption, section[data-testid="stMain"] [data-testid="stCaption"],
section[data-testid="stMain"] [data-testid="stCaption"] * {
    font-weight: 500 !important;
    color: var(--texto-secondary) !important;
    font-size: 0.8125rem !important;
    opacity: 1 !important;
}
/* Alertas — texto nítido (evita “apagado”) */
[data-testid="stAlert"] {
    border: 1px solid rgba(201,162,39,0.35) !important;
    box-shadow: var(--sombra-sm) !important;
}
[data-testid="stAlert"] p, [data-testid="stAlert"] div, [data-testid="stAlert"] span {
    color: var(--texto-primary) !important;
    font-weight: 500 !important;
    -webkit-font-smoothing: subpixel-antialiased !important;
}
/* Tabs — rótulos mais legíveis */
.stTabs [data-baseweb="tab"] span, .stTabs [data-baseweb="tab"] p {
    font-weight: 600 !important;
    color: var(--texto-secondary) !important;
}
section[data-testid="stMain"] .stTextInput input, section[data-testid="stMain"] .stTextArea textarea {
    font-weight: 400 !important;
    color: var(--texto-primary) !important;
    font-size: 0.9375rem !important;
    letter-spacing: 0.01em !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
}
section[data-testid="stMain"] .stTextInput input:focus, section[data-testid="stMain"] .stTextArea textarea:focus {
    box-shadow: 0 0 0 3px rgba(201,162,39,0.2) !important;
}
section[data-testid="stMain"] .stTextInput input::placeholder,
section[data-testid="stMain"] .stTextArea textarea::placeholder {
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
    transform: translateY(-2px) !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
    box-shadow: var(--sombra-press), 0 4px 14px rgba(201,162,39,0.25) !important;
    transition: transform 0.08s ease, box-shadow 0.08s ease !important;
}
.stDownloadButton > button {
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    box-shadow: var(--sombra-lg) !important;
    transform: translateY(-2px) !important;
}
.stDownloadButton > button:active {
    transform: scale(0.98) !important;
    box-shadow: var(--sombra-press) !important;
}

/* Esconder info boxes feios — usar mensagem customizada */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* Sidebar — navegação multipage legível, sem sobrepor ícones/texto */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fffefb 0%, var(--creme) 100%) !important;
    border-right: 1px solid var(--borda) !important;
    box-shadow: 4px 0 12px rgba(61,41,20,0.06) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    min-height: 2.25rem !important;
    padding: 0.35rem 0.5rem !important;
    margin-bottom: 0.15rem !important;
    border-radius: 8px !important;
    line-height: 1.35 !important;
    white-space: normal !important;
    word-break: break-word !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {
    margin: 0.75rem 0 !important;
}
[data-testid="stSidebar"] .stMarkdown { color: var(--texto-primary) !important; }
[data-testid="stSidebar"] .stMarkdown p { margin-bottom: 0.5rem !important; }
[data-testid="stSidebar"] .element-container { margin-bottom: 0.5rem !important; }

.data-source {
    font-size: 0.8125rem;
    color: var(--texto-secondary);
    margin-bottom: 1rem;
    font-weight: 500;
}

/* Caixa amigável — falta planilha */
.planilha-missing-box {
    background: linear-gradient(180deg, #fff9e6 0%, #fff3cc 100%);
    border: 1px solid var(--ouro);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0 1.25rem 0;
    box-shadow: var(--sombra-md);
}
.planilha-missing-box h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--chocolate);
}
.planilha-missing-box ol { margin: 0.5rem 0 0 1.1rem; padding: 0; color: var(--texto-primary); line-height: 1.65; }
.planilha-missing-box li { margin-bottom: 0.35rem; }

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
    """API → upload sessão → planilha em disco → catálogo embutido (sempre há produtos)."""
    if obter_url_api():
        try:
            prod, src = carregar_produtos_api()
            if prod:
                return prod, src
        except Exception as e:
            st.warning(f"API indisponível — a usar catálogo embutido. ({e})")
    blob = st.session_state.get("_planilha_bytes")
    if blob:
        try:
            return extrair_todos_de_bytes(blob), "upload_sessao.xlsx"
        except Exception as e:
            st.error(f"Erro ao ler o Excel enviado: {e}")
    try:
        path = _caminho_planilha()
        prod = _carregar_produtos_arquivo(str(path.resolve()))
        if prod:
            return prod, str(path)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    from produtos_catalogo import produtos_padrao

    return produtos_padrao(), "catalogo_embutido"


def _render_launch_splash() -> None:
    """Primeira visita: boas-vindas minimalistas + ações claras (sem Lottie / sem iframe branco)."""
    st.markdown('<div id="gw-launch-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="gw-launch-shell">
          <div class="gw-launch-inner">
            <div class="gw-launch-mark" aria-hidden="true">
              <svg width="52" height="52" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="10" y="14" width="36" height="28" rx="6" stroke="#C9A227" stroke-width="2" fill="none"/>
                <path d="M18 26 L28 33 L38 26" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" fill="none"/>
              </svg>
            </div>
            <p class="gw-launch-kicker">Chocolates artesanais</p>
            <h1 class="gw-launch-title">Gramadoway</h1>
            <p class="gw-launch-sub">Pedidos e orçamentos. <strong>Entre</strong> ou <strong>crie a sua conta</strong>.</p>
          </div>
        </div>
        <p class="gw-launch-hint">Toque num dos botões abaixo para continuar</p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:1rem" aria-hidden="true"></div>', unsafe_allow_html=True)
    if st.button(
        "Entrar",
        type="primary",
        use_container_width=True,
        key="gw_splash_entrar",
    ):
        st.session_state["gw_splash_done"] = True
        st.session_state["gw_auth_choice"] = "Entrar"
        st.session_state["_gw_play_chime"] = True
        st.rerun()
    st.markdown('<div style="height:0.6rem" aria-hidden="true"></div>', unsafe_allow_html=True)
    if st.button(
        "Criar minha conta",
        type="secondary",
        use_container_width=True,
        key="gw_splash_criar",
    ):
        st.session_state["gw_splash_done"] = True
        st.session_state["gw_auth_choice"] = "Criar minha conta"
        st.session_state["_gw_play_chime"] = True
        st.rerun()


def _render_login():
    """Link público: cada pessoa cria o próprio usuário ou entra se já tiver cadastro."""
    st.markdown('<div id="gw-login-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
    if "gw_auth_choice" not in st.session_state:
        st.session_state["gw_auth_choice"] = "Entrar"

    st.markdown("### Gramadoway — Acesso")
    st.info(
        "Quem recebe o **link** pode usar o sistema por aqui. "
        "Em **Criar minha conta** você escolhe login e senha **só seus**. "
        "Se já se cadastrou antes, use **Entrar**."
    )
    st.radio(
        "Como deseja continuar?",
        ["Entrar", "Criar minha conta"],
        horizontal=True,
        key="gw_auth_choice",
    )
    if st.session_state["gw_auth_choice"] == "Entrar":
        with st.form("form_login_publico"):
            lg = st.text_input("Usuário", placeholder="seu login", key="pub_login_user")
            pw = st.text_input("Senha", type="password", key="pub_login_pw")
            if st.form_submit_button("Entrar"):
                u = auth.verificar_login(lg, pw)
                if u:
                    st.session_state[auth.SESSION_KEY] = u
                    st.session_state.pop("df_pedido", None)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    else:
        with st.form("form_cadastro_publico"):
            nu = st.text_input(
                "Escolha seu login",
                placeholder="ex: joao_vendas",
                help="3 a 32 caracteres: letras minúsculas, números e _",
                key="pub_reg_login",
            )
            p1 = st.text_input("Senha (mín. 6 caracteres)", type="password", key="pub_reg_p1")
            p2 = st.text_input("Repita a senha", type="password", key="pub_reg_p2")
            if st.form_submit_button("Criar conta e entrar"):
                if p1 != p2:
                    st.error("As senhas não coincidem.")
                else:
                    try:
                        auth.registrar_usuario(nu, p1)
                        u = auth.verificar_login(nu, p1)
                        if u:
                            st.session_state[auth.SESSION_KEY] = u
                            st.session_state.pop("df_pedido", None)
                            st.rerun()
                    except Exception as e:
                        st.error(str(e))


def main():
    if st.session_state.pop("_gw_play_chime", None):
        components.html(GW_CHIME_HTML, height=0, width=0)

    usuario = st.session_state.get(auth.SESSION_KEY)
    if not usuario:
        if not st.session_state.get("gw_splash_done"):
            _render_launch_splash()
            return
        _render_login()
        return

    # Sidebar — Resumo rápido + Histórico + logout + novo usuário
    with st.sidebar:
        st.caption(f"Logado: **{usuario}**")
        if st.button("Sair", key="btn_logout"):
            st.session_state.pop(auth.SESSION_KEY, None)
            st.session_state.pop("df_pedido", None)
            st.rerun()
        st.caption("Novos colegas: envie o **mesmo link** do sistema — cada um cria a conta em *Criar minha conta*.")
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

    with st.spinner("Carregando produtos..."):
        produtos, path_planilha = carregar_produtos_ui()

    src_prod = str(path_planilha or "")
    if src_prod == "catalogo_embutido":
        st.success(
            "**Catálogo Gramadoway** carregado — já pode orçar. "
            "Preços de **referência**; para a sua planilha oficial, abra **Substituir planilha** abaixo."
        )
    elif src_prod.startswith("http"):
        st.caption(f"Produtos da **API**: `{src_prod}`")
    elif src_prod == "upload_sessao.xlsx":
        st.caption("A usar o **Excel que enviou** nesta sessão.")
    else:
        nome_src = (
            Path(src_prod).name
            if src_prod and ("/" in src_prod or "\\" in src_prod)
            else (src_prod or "—")
        )
        st.markdown(
            f'<p class="data-source">Preços: <strong>{nome_src}</strong></p>',
            unsafe_allow_html=True,
        )

    with st.expander("Substituir planilha de preços (.xlsx) — opcional", expanded=False):
        st.caption(
            "Se tiver o Excel oficial Gramadoway, envie aqui. "
            "Senão, o catálogo embutido continua ativo. Ficheiro em `data/planilha.xlsx` no projeto também é usado automaticamente."
        )
        c_up, c_lim = st.columns([2, 1])
        with c_up:
            arq = st.file_uploader("Enviar Excel (.xlsx)", type=["xlsx"], key="gw_upload_planilha")
            if arq is not None:
                st.session_state["_planilha_bytes"] = arq.getvalue()
                st.session_state.pop("df_pedido", None)
                st.cache_data.clear()
                st.rerun()
        with c_lim:
            if st.session_state.get("_planilha_bytes") and st.button(
                "Remover upload e voltar ao catálogo/disco", key="gw_clear_upload"
            ):
                st.session_state.pop("_planilha_bytes", None)
                st.session_state.pop("df_pedido", None)
                st.cache_data.clear()
                st.rerun()
        if st.button("Recarregar lista de produtos", key="gw_reload_prod"):
            st.cache_data.clear()
            st.rerun()

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

    # Abas visuais — Busca rápida, alteração de preço, categorias, Orçamento
    tab_labels = (
        ["Busca rápida", "Alteração de preço"]
        + [f"{a} ({len(df_ped[df_ped['aba']==a])})" for a in abas_unicas]
        + ["Orçamento"]
    )
    tabs = st.tabs(tab_labels)
    edited_frames = []
    edited_preco_df = None
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

    # Tab 1: Alteração de preço — busca dedicada + só a coluna Preço editável
    with tabs[1]:
        st.caption(
            "🔍 **Alteração de preço** — encontre o produto e altere **Preço**; "
            "totais do pedido recalculam ao confirmar a célula."
        )
        col_lupa, col_campo = st.columns([0.08, 0.92])
        with col_lupa:
            st.markdown('<p style="font-size:1.6rem;margin:0;line-height:1.2;">🔍</p>', unsafe_allow_html=True)
        with col_campo:
            busca_preco = st.text_input(
                "Buscar produto para alterar preço",
                placeholder="Nome, tipo de chocolate, código…",
                key="busca_alteracao_preco",
                label_visibility="collapsed",
            )
        termo_preco = (busca_preco or "").strip()
        if len(termo_preco) < 2:
            st.info("Digite **pelo menos 2 caracteres** para buscar e alterar preços.")
            df_pre = df_ped.head(0)
        else:
            df_pre = buscar_produtos(df_ped, termo_preco, limite=100)
        if len(df_pre) == 0 and len(termo_preco) >= 2:
            st.warning("Nenhum produto encontrado. Tente outro termo.")
        if len(df_pre) > 0:
            df_pre_show = df_pre[["produto", "aba", "un", "preco_por", "preco", "Qtde", "Total"]].copy()
            edited_preco_df = st.data_editor(
                df_pre_show,
                column_config={
                    "produto": st.column_config.TextColumn("Produto", disabled=True, width="large"),
                    "aba": st.column_config.TextColumn("Categoria", disabled=True),
                    "un": st.column_config.TextColumn("Un.", disabled=True),
                    "preco_por": st.column_config.TextColumn("Preço por", disabled=True),
                    "preco": st.column_config.NumberColumn(
                        "Preço",
                        format="R$ %.2f",
                        min_value=0.0,
                        step=0.01,
                        help="Preço unitário (R$/kg, R$/un, etc., conforme a unidade).",
                    ),
                    "Qtde": st.column_config.NumberColumn("Qtde", format="%.2f", disabled=True),
                    "Total": st.column_config.NumberColumn("Total", format="R$ %.2f", disabled=True),
                },
                use_container_width=True,
                height=min(480, 140 + len(df_pre_show) * 36),
                key="tab_alteracao_preco",
            )

    col_config = {
        "produto": st.column_config.TextColumn("Produto", disabled=True),
        "un": st.column_config.TextColumn("Un.", disabled=True, help="KG=quilograma | UN=unidade | SACO=saco"),
        "preco_por": st.column_config.TextColumn("Preço por", disabled=True),
        "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f", disabled=True),
        "Qtde": st.column_config.NumberColumn("Qtde", min_value=0.0, step=0.5, format="%.2f"),
        "Total": st.column_config.NumberColumn("Total", format="R$ %.2f", disabled=True),
    }

    for i, aba in enumerate(abas_unicas):
        with tabs[i + 2]:
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
    with tabs[num_abas_produtos + 2]:
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
    if edited_preco_df is not None:
        for idx in edited_preco_df.index:
            if idx in st.session_state.df_pedido.index:
                try:
                    npreco = float(edited_preco_df.loc[idx, "preco"])
                except (ValueError, TypeError):
                    continue
                if pd.notna(npreco) and npreco >= 0:
                    st.session_state.df_pedido.loc[idx, "preco"] = npreco
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
