"""Gerencia histórico de pedidos, clientes e rascunhos — um conjunto de arquivos por usuário."""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from auth import sanitize_login
from config_paths import data_root


def _base_dir() -> Path:
    base = data_root()
    base.mkdir(exist_ok=True)
    return base


def _user_dir(username: str) -> Path:
    safe = sanitize_login(username)
    d = _base_dir() / "users" / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def _caminho_historico(username: str) -> Path:
    return _user_dir(username) / "historico.json"


def _caminho_clientes(username: str) -> Path:
    return _user_dir(username) / "clientes.json"


def _caminho_rascunho(username: str) -> Path:
    return _user_dir(username) / "rascunho.json"


def carregar_historico(username: str) -> list[dict]:
    path = _caminho_historico(username)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def salvar_pedido(username: str, cliente: dict, itens: list, total: float) -> dict:
    hist = carregar_historico(username)
    pedido = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "cliente": cliente,
        "itens": itens,
        "total": total,
    }
    hist.insert(0, pedido)
    _caminho_historico(username).write_text(
        json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return pedido


def carregar_clientes(username: str) -> list[dict]:
    path = _caminho_clientes(username)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def salvar_cliente(username: str, cliente: dict) -> None:
    clientes = carregar_clientes(username)
    cnpj = (cliente.get("CNPJ") or "").strip()
    razao = (cliente.get("Razão Social") or "").strip()
    if not cnpj and not razao:
        return
    novo = {k: v for k, v in cliente.items() if v and not str(k).startswith("_")}
    novo["_ultima_atualizacao"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    idx = next((i for i, c in enumerate(clientes) if (c.get("CNPJ") or "").strip() == cnpj and cnpj), None)
    if idx is None:
        idx = next((i for i, c in enumerate(clientes) if (c.get("Razão Social") or "").strip() == razao and razao), None)
    if idx is not None:
        clientes[idx] = novo
    else:
        clientes.append(novo)
    _caminho_clientes(username).write_text(
        json.dumps(clientes, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def carregar_rascunho(username: str) -> Optional[dict]:
    path = _caminho_rascunho(username)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def salvar_rascunho(username: str, cliente: dict, itens: list, total: float) -> None:
    """Salva rascunho."""
    rascunho = {
        "cliente": cliente,
        "itens": itens,
        "total": total,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    _caminho_rascunho(username).write_text(
        json.dumps(rascunho, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def limpar_rascunho(username: str) -> None:
    path = _caminho_rascunho(username)
    if path.exists():
        path.unlink()


def stats_dashboard(username: str) -> dict:
    """Retorna estatísticas para o dashboard (dados só do usuário)."""
    hist = carregar_historico(username)
    hoje = datetime.now().strftime("%d/%m/%Y")
    total_geral = sum(p.get("total", 0) for p in hist)
    pedidos_hoje = [p for p in hist if p.get("data", "").startswith(hoje[:10])]
    valor_hoje = sum(p.get("total", 0) for p in pedidos_hoje)
    produtos_vendidos = {}
    for p in hist:
        for item in p.get("itens", []):
            prod = item.get("Produto", item.get("produto", ""))
            if prod:
                produtos_vendidos[prod] = produtos_vendidos.get(prod, 0) + float(item.get("Qtde", 0))
    top_produtos = sorted(produtos_vendidos.items(), key=lambda x: -x[1])[:10]
    return {
        "total_pedidos": len(hist),
        "valor_total": total_geral,
        "pedidos_hoje": len(pedidos_hoje),
        "valor_hoje": valor_hoje,
        "top_produtos": top_produtos,
        "historico": hist,
    }


def _fmt_moeda(valor: float) -> str:
    """Formata valor como R$ 1.234,56."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf(pedido: dict) -> bytes:
    """Gera PDF do orçamento — layout profissional de empresa de grande porte."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except ImportError:
        return b""

    buf = __import__("io").BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.2*cm, bottomMargin=1.2*cm,
    )
    styles = getSampleStyleSheet()
    elements = []

    # Cabeçalho — identidade da empresa
    cabecalho = Paragraph(
        '<para align="center"><font size="22" color="#1a1612"><b>GRAMADOWAY</b></font><br/>'
        '<font size="11" color="#5D4E37">Chocolates Artesanais</font></para>',
        ParagraphStyle(name="Cab", alignment=1, spaceAfter=4)
    )
    elements.append(cabecalho)
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        '<para align="center"><font size="14" color="#9A7B1A"><b>ORÇAMENTO / PEDIDO</b></font></para>',
        ParagraphStyle(name="Tit", alignment=1, spaceAfter=12)
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Dados do cliente — tabela organizada em 2 colunas, todos os preenchidos
    cli = pedido.get("cliente") or {}
    ordem = ["Razão Social", "Fantasia", "CNPJ", "Fone", "Endereço", "Bairro", "Cidade", "CEP",
             "E-mail", "Contato", "I. Estadual", "Cond. Pagto", "Frete", "Observação"]
    pares = []
    for i in range(0, len(ordem), 2):
        c1, c2 = ordem[i], ordem[i + 1] if i + 1 < len(ordem) else None
        v1 = str(cli.get(c1, "") or "").strip()
        v2 = str(cli.get(c2, "") or "").strip() if c2 else ""
        if v1 or v2:
            pares.append((f"{c1}:", v1[:55] if v1 else "—", f"{c2}:" if c2 else "", v2[:55] if v2 else "—"))
    if pares:
        elements.append(Paragraph(
            '<font size="11" color="#5D4E37"><b>DADOS DO CLIENTE</b></font>',
            ParagraphStyle(name="Sec", spaceAfter=8)
        ))
        data_tbl = [[r[0], r[1], r[2], r[3]] for r in pares]
        t_cli = Table(data_tbl, colWidths=[3*cm, 7*cm, 3*cm, 7*cm])
        t_cli.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F5F0")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2d2822")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D4C4A8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5D4A1")),
            ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor("#C9A227")),
        ]))
        elements.append(t_cli)
        elements.append(Spacer(1, 0.6*cm))

    # Itens do pedido — tabela profissional
    elements.append(Paragraph(
        '<font size="11" color="#5D4E37"><b>ITENS DO PEDIDO</b></font>',
        ParagraphStyle(name="Sec2", spaceAfter=8)
    ))
    itens = pedido.get("itens", [])
    if itens:
        cab = [["Qtde", "Un.", "Produto", "Preço Unit.", "Total"]]
        linhas = []
        for r in itens:
            qtd = r.get("Qtde", r.get("Qtde", ""))
            un = r.get("Un.", r.get("un", ""))
            prod = str(r.get("Produto", r.get("produto", "")))[:50]
            prec = float(r.get("Preço", r.get("preco", 0)))
            tot = float(r.get("Total", 0))
            linhas.append([str(qtd), str(un), prod, _fmt_moeda(prec), _fmt_moeda(tot)])
        data = cab + linhas
        t = Table(data, colWidths=[2*cm, 1.8*cm, 8*cm, 3*cm, 3*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1612")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#2d2822")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("TOPPADDING", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D4C4A8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F5F0")]),
            ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor("#C9A227")),
        ]))
        elements.append(t)

    # Valor total — destaque
    elements.append(Spacer(1, 0.6*cm))
    total = pedido.get("total", 0)
    total_fmt = _fmt_moeda(total)
    elements.append(Paragraph(
        f'<para align="right"><font size="16" color="#1a1612"><b>VALOR TOTAL: {total_fmt}</b></font></para>',
        ParagraphStyle(name="Tot", alignment=2)
    ))
    elements.append(Spacer(1, 0.4*cm))

    # Rodapé — data e identificação
    elements.append(Paragraph(
        f'<font size="9" color="#6b6b6b">Documento gerado em {pedido.get("data", "")} — Gramadoway Chocolates Artesanais</font>',
        ParagraphStyle(name="Rod", alignment=1)
    ))

    doc.build(elements)
    return buf.getvalue()
