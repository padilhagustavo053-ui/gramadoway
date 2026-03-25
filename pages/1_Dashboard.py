"""
Dashboard BI — Gramadoway
Painel de controle profissional, polido, última geração.
"""
import streamlit as st
from pathlib import Path
import pandas as pd
from datetime import datetime
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_paths import inject_streamlit_secrets_into_environ, migrate_legacy_pedidos_folder

inject_streamlit_secrets_into_environ()
migrate_legacy_pedidos_folder()

from historico import stats_dashboard
import auth

st.set_page_config(
    page_title="Painel de Controle BI — Gramadoway",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS — BI profissional, tema escuro, precisão visual
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bi-azul: #3b82f6;
    --bi-verde: #10b981;
    --bi-vermelho: #ef4444;
    --bi-roxo: #8b5cf6;
    --bi-amber: #f59e0b;
    --bi-fundo: #0f172a;
    --bi-card: #1e293b;
    --bi-card-hover: #334155;
    --bi-borda: #334155;
    --bi-texto: #f8fafc;
    --bi-texto-sec: #cbd5e1;
}

.stApp { background: var(--bi-fundo) !important; }
/* Só área principal — não forçar fonte na sidebar (ícones multipage) */
section[data-testid="stMain"], section[data-testid="stMain"] button,
section[data-testid="stMain"] input, section[data-testid="stMain"] label {
    font-family: 'Inter', -apple-system, sans-serif !important;
    -webkit-font-smoothing: subpixel-antialiased !important;
    -moz-osx-font-smoothing: auto !important;
    text-rendering: geometricPrecision !important;
}

/* Header premium */
.dash-header {
    background: linear-gradient(135deg, rgba(59,130,246,0.12) 0%, rgba(139,92,246,0.08) 100%);
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 20px;
    padding: 2rem 3rem;
    margin: -1rem -1rem 2rem -1rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.dash-header h1 {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--bi-texto) !important;
    margin: 0;
    letter-spacing: 0.04em;
}
.dash-header .sub { color: var(--bi-texto-sec); font-size: 1rem; margin-top: 0.5rem; font-weight: 600; opacity: 1; }

/* KPI Cards — estilo primeira linha */
.kpi-card {
    background: linear-gradient(145deg, var(--bi-card) 0%, #0f172a 100%);
    border: 1px solid var(--bi-borda);
    border-radius: 16px;
    padding: 1.5rem 1.2rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    border-color: rgba(59,130,246,0.4);
}
.kpi-card.azul { border-left: 4px solid var(--bi-azul); }
.kpi-card.verde { border-left: 4px solid var(--bi-verde); }
.kpi-card.vermelho { border-left: 4px solid var(--bi-vermelho); }
.kpi-card.roxo { border-left: 4px solid var(--bi-roxo); }
.kpi-card.amber { border-left: 4px solid var(--bi-amber); }
.kpi-card .valor { font-size: 1.8rem; font-weight: 700; color: var(--bi-texto); }
.kpi-card .label { font-size: 0.85rem; color: var(--bi-texto-sec); margin-top: 0.4rem; font-weight: 600; }
.kpi-card .sub { font-size: 0.75rem; color: var(--bi-texto-sec); margin-top: 0.2rem; opacity: 1; font-weight: 500; }

/* Chart containers */
.chart-box {
    background: var(--bi-card);
    border: 1px solid var(--bi-borda);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.chart-box h3 { color: var(--bi-texto); font-size: 1.1rem; font-weight: 600; margin: 0 0 1rem 0; }

/* Tabela estilizada */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(135deg, #334155, #1e293b) !important;
    color: var(--bi-texto) !important;
    font-weight: 600 !important;
}

/* Botão voltar sem ícone problemático */
.stPageLink { margin-bottom: 1rem !important; }

section[data-testid="stMain"] .stButton > button {
    font-weight: 600 !important;
    border-radius: 12px !important;
    transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease !important;
}
section[data-testid="stMain"] .stButton > button:hover {
    filter: brightness(1.08) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35) !important;
}
section[data-testid="stMain"] .stButton > button:active {
    transform: scale(0.98) !important;
}

[data-testid="stCaptionContainer"] { opacity: 1 !important; }
[data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] span,
[data-testid="stCaptionContainer"] label {
    color: var(--bi-texto-sec) !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)


def _fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _agregar_por_mes(historico):
    """Agrupa pedidos por mês para gráfico de evolução."""
    por_mes = defaultdict(float)
    for p in historico:
        data_str = p.get("data", "")[:10]
        if data_str:
            try:
                dt = datetime.strptime(data_str, "%d/%m/%Y")
                chave = dt.strftime("%Y-%m")
                por_mes[chave] += float(p.get("total", 0))
            except ValueError:
                pass
    return sorted(por_mes.items())


def _valor_por_produto(historico):
    """Valor total por produto para donut/treemap."""
    por_prod = defaultdict(float)
    for p in historico:
        for item in p.get("itens", []):
            prod = item.get("Produto", item.get("produto", ""))
            if prod:
                tot = float(item.get("Total", 0))
                por_prod[prod] += tot
    return sorted(por_prod.items(), key=lambda x: -x[1])


def _dados_diarios_ohlc(historico):
    """Agrupa pedidos por dia e gera OHLC (estilo trader) para candlestick."""
    por_dia = defaultdict(list)
    for p in historico:
        data_str = p.get("data", "")[:10]
        if data_str:
            try:
                dt = datetime.strptime(data_str, "%d/%m/%Y")
                chave = dt.strftime("%Y-%m-%d")
                por_dia[chave].append((p.get("data", ""), float(p.get("total", 0))))
            except ValueError:
                pass
    rows = []
    for dia, vals in sorted(por_dia.items()):
        vals_sorted = sorted(vals, key=lambda x: x[0])
        totais = [v[1] for v in vals_sorted]
        if totais:
            rows.append((dia, totais[0], max(totais), min(totais), totais[-1]))
    return rows


def _faturamento_mes_atual(historico):
    """Faturamento do mês atual."""
    mes_atual = datetime.now().strftime("%Y-%m")
    total = 0.0
    for p in historico:
        data_str = p.get("data", "")[:10]
        if data_str:
            try:
                dt = datetime.strptime(data_str, "%d/%m/%Y")
                if dt.strftime("%Y-%m") == mes_atual:
                    total += float(p.get("total", 0))
            except ValueError:
                pass
    return total


def main():
    usuario = st.session_state.get(auth.SESSION_KEY)
    if not usuario:
        st.warning("Abra a página principal (Formulário), use **Entrar** ou **Criar minha conta**.")
        if st.button("Ir ao acesso / login", type="primary", use_container_width=True):
            st.switch_page("app.py")
        st.stop()

    if st.button("← Voltar ao Formulário", key="dash_voltar_form"):
        st.switch_page("app.py")

    st.markdown(f"""
    <div class="dash-header">
        <h1>PAINEL DE CONTROLE BI</h1>
        <p class="sub">Gramadoway — Chocolates Artesanais • Sua visão: <b>{usuario}</b></p>
    </div>
    """, unsafe_allow_html=True)

    stats = stats_dashboard(usuario)
    hist = stats["historico"]
    total_geral = stats["valor_total"]
    total_pedidos = stats["total_pedidos"]
    pedidos_hoje = stats["pedidos_hoje"]
    valor_hoje = stats["valor_hoje"]
    ticket_medio = total_geral / max(1, total_pedidos)

    # KPIs — cards premium
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-card azul">
            <div class="valor">{total_pedidos}</div>
            <div class="label">Total de Pedidos</div>
            <div class="sub">histórico completo</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card verde">
            <div class="valor">{_fmt_moeda(total_geral)}</div>
            <div class="label">Faturamento Total</div>
            <div class="sub">valor acumulado</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card vermelho">
            <div class="valor">{pedidos_hoje}</div>
            <div class="label">Pedidos Hoje</div>
            <div class="sub">data atual</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card roxo">
            <div class="valor">{_fmt_moeda(valor_hoje)}</div>
            <div class="label">Valor Hoje</div>
            <div class="sub">faturamento do dia</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="kpi-card amber">
            <div class="valor">{_fmt_moeda(ticket_medio)}</div>
            <div class="label">Ticket Médio</div>
            <div class="sub">por pedido</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    try:
        import plotly.express as px
        import plotly.graph_objects as go

        # === GAUGES (relógio com ponteiro) — dados reais ===
        fat_mes = _faturamento_mes_atual(hist)
        meta_mes = max(fat_mes * 1.5, 10000) if fat_mes > 0 else 10000
        meta_pedidos = max(pedidos_hoje * 3, 5)
        meta_ticket = max(ticket_medio * 1.3, 500)

        st.markdown("### Indicadores em tempo real")
        g1, g2, g3 = st.columns(3)
        with g1:
            fig_g1 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=fat_mes,
                number={"prefix": "R$ ", "font": {"size": 22}},
                title={"text": "Faturamento do mês", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, meta_mes], "tickwidth": 1},
                    "bar": {"color": "#3b82f6"},
                    "bgcolor": "rgba(0,0,0,0.3)",
                    "borderwidth": 2,
                    "bordercolor": "#334155",
                    "steps": [{"range": [0, meta_mes * 0.5], "color": "rgba(239,68,68,0.2)"}, {"range": [meta_mes * 0.5, meta_mes * 0.8], "color": "rgba(245,158,11,0.2)"}, {"range": [meta_mes * 0.8, meta_mes], "color": "rgba(16,185,129,0.2)"}],
                    "threshold": {"line": {"color": "#10b981", "width": 4}, "thickness": 0.75, "value": fat_mes},
                },
            ))
            fig_g1.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"), height=260, margin=dict(t=40, b=30))
            st.plotly_chart(fig_g1, use_container_width=True)
        with g2:
            fig_g2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pedidos_hoje,
                number={"font": {"size": 28}},
                title={"text": "Pedidos hoje", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, meta_pedidos], "tickwidth": 1},
                    "bar": {"color": "#10b981"},
                    "bgcolor": "rgba(0,0,0,0.3)",
                    "borderwidth": 2,
                    "bordercolor": "#334155",
                    "steps": [{"range": [0, meta_pedidos * 0.5], "color": "rgba(239,68,68,0.2)"}, {"range": [meta_pedidos * 0.5, meta_pedidos], "color": "rgba(16,185,129,0.2)"}],
                    "threshold": {"line": {"color": "#10b981", "width": 4}, "thickness": 0.75, "value": pedidos_hoje},
                },
            ))
            fig_g2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"), height=260, margin=dict(t=40, b=30))
            st.plotly_chart(fig_g2, use_container_width=True)
        with g3:
            fig_g3 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=ticket_medio,
                number={"prefix": "R$ ", "font": {"size": 22}},
                title={"text": "Ticket médio", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, meta_ticket], "tickwidth": 1},
                    "bar": {"color": "#8b5cf6"},
                    "bgcolor": "rgba(0,0,0,0.3)",
                    "borderwidth": 2,
                    "bordercolor": "#334155",
                    "steps": [{"range": [0, meta_ticket * 0.6], "color": "rgba(245,158,11,0.2)"}, {"range": [meta_ticket * 0.6, meta_ticket], "color": "rgba(139,92,246,0.2)"}],
                    "threshold": {"line": {"color": "#8b5cf6", "width": 4}, "thickness": 0.75, "value": ticket_medio},
                },
            ))
            fig_g3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"), height=260, margin=dict(t=40, b=30))
            st.plotly_chart(fig_g3, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # === CANDLESTICK (estilo trader) — faturamento diário ===
        ohlc = _dados_diarios_ohlc(hist)
        if len(ohlc) >= 1:
            st.markdown("### Tendência — Faturamento diário (estilo trader)")
            df_ohlc = pd.DataFrame(ohlc, columns=["Data", "Open", "High", "Low", "Close"])
            fig_candle = go.Figure(go.Candlestick(
                x=df_ohlc["Data"],
                open=df_ohlc["Open"],
                high=df_ohlc["High"],
                low=df_ohlc["Low"],
                close=df_ohlc["Close"],
                increasing_line_color="#10b981",
                decreasing_line_color="#ef4444",
                increasing_fillcolor="rgba(16,185,129,0.5)",
                decreasing_fillcolor="rgba(239,68,68,0.5)",
            ))
            fig_candle.update_layout(
                title=dict(text="Faturamento por dia (OHLC)", font=dict(size=16, color="#f1f5f9")),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#94a3b8"),
                height=380,
                xaxis=dict(rangeslider=dict(visible=False), showgrid=False),
                yaxis=dict(title="R$", gridcolor="rgba(148,163,184,0.15)"),
            )
            st.plotly_chart(fig_candle, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

        col_esq, col_dir = st.columns([1, 1])

        with col_esq:
            # Faturamento ao longo do tempo (barras + linha tendência)
            dados_mes = _agregar_por_mes(hist)
            if dados_mes:
                df_mes = pd.DataFrame(dados_mes, columns=["Mês", "Faturamento"])
                df_mes["Mês"] = pd.to_datetime(df_mes["Mês"] + "-01")
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_mes["Mês"], y=df_mes["Faturamento"],
                    name="Faturamento",
                    marker_color="#3b82f6",
                    marker_line_color="rgba(59,130,246,0.5)",
                ))
                fig.add_trace(go.Scatter(
                    x=df_mes["Mês"], y=df_mes["Faturamento"],
                    name="Tendência",
                    line=dict(color="#f59e0b", width=3, dash="dot"),
                    mode="lines+markers",
                ))
                fig.update_layout(
                    title=dict(text="Faturamento ao longo do tempo", font=dict(size=16, color="#f1f5f9")),
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#94a3b8", size=11),
                    height=380,
                    margin=dict(t=50, b=50, l=50, r=30),
                    xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                    yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.15)", tickformat=",.0f"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("""
                <div class="chart-box">
                    <h3>Faturamento ao longo do tempo</h3>
                    <p style="color:#94a3b8;font-size:0.95rem;">Nenhum dado de vendas ainda. Os pedidos aparecerão aqui.</p>
                </div>
                """, unsafe_allow_html=True)

        with col_dir:
            # Valor por produto — Donut + Treemap (hierárquico estilo trader)
            valor_prod = _valor_por_produto(hist)
            if valor_prod:
                df_prod = pd.DataFrame(valor_prod[:8], columns=["Produto", "Valor"])
                df_prod["Produto"] = df_prod["Produto"].apply(lambda x: (x[:28] + "…") if len(str(x)) > 28 else x)
                # Treemap hierárquico (estilo BI)
                fig_treemap = px.treemap(
                    df_prod, path=["Produto"], values="Valor",
                    color="Valor",
                    color_continuous_scale=["#1e293b", "#3b82f6", "#10b981"],
                )
                fig_treemap.update_layout(
                    title=dict(text="Valor por produto (Treemap)", font=dict(size=16, color="#f1f5f9")),
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#94a3b8"),
                    height=380,
                    margin=dict(t=50, b=30),
                )
                fig_treemap.update_coloraxes(showscale=True, colorbar=dict(title="R$"))
                st.plotly_chart(fig_treemap, use_container_width=True)
            else:
                st.markdown("""
                <div class="chart-box">
                    <h3>Valor por produto</h3>
                    <p style="color:#94a3b8;font-size:0.95rem;">Nenhum produto vendido ainda.</p>
                </div>
                """, unsafe_allow_html=True)


        # Segunda linha: Top produtos (barras) + Tabela detalhamento
        col_barra, col_tab = st.columns([1, 1])

        with col_barra:
            top = stats["top_produtos"]
            if top:
                df_top = pd.DataFrame(top[:10], columns=["Produto", "Quantidade"])
                df_top["Produto"] = df_top["Produto"].apply(lambda x: (x[:32] + "…") if len(str(x)) > 32 else x)
                fig3 = px.bar(
                    df_top, x="Quantidade", y="Produto",
                    orientation="h",
                    color="Quantidade",
                    color_continuous_scale=["#1e293b", "#3b82f6"],
                )
                fig3.update_layout(
                    title=dict(text="Top 10 Produtos Mais Vendidos", font=dict(size=16, color="#f1f5f9")),
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#94a3b8"),
                    height=400,
                    margin=dict(l=140),
                    showlegend=False,
                )
                fig3.update_coloraxes(showscale=False)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.markdown("""
                <div class="chart-box">
                    <h3>Top Produtos</h3>
                    <p style="color:#94a3b8;">Nenhum dado de vendas ainda.</p>
                </div>
                """, unsafe_allow_html=True)

        with col_tab:
            st.markdown("### Detalhamento — Últimos Pedidos")
            if hist:
                df_tab = pd.DataFrame([
                    {
                        "Data": p.get("data", "")[:16],
                        "Cliente": (p.get("cliente", {}).get("Razão Social") or p.get("cliente", {}).get("Fantasia") or "-")[:40],
                        "Itens": len(p.get("itens", [])),
                        "Total": _fmt_moeda(p.get("total", 0)),
                    }
                    for p in hist[:20]
                ])
                st.dataframe(df_tab, use_container_width=True, height=400)
            else:
                st.markdown("""
                <div class="chart-box">
                    <p style="color:#94a3b8;">Nenhum pedido registrado.</p>
                </div>
                """, unsafe_allow_html=True)

    except ImportError:
        st.markdown("""
        <div class="chart-box">
            <p style="color:#f59e0b;">Instale plotly para os gráficos: <code>pip install plotly</code></p>
        </div>
        """, unsafe_allow_html=True)
        if hist:
            st.dataframe(pd.DataFrame([
                {"Data": p.get("data"), "Cliente": (p.get("cliente", {}).get("Razão Social") or "-")[:30], "Total": p.get("total", 0)}
                for p in hist[:20]
            ]))


if __name__ == "__main__":
    main()
