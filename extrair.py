"""
Extrai produtos da planilha Gramadoway (Excel).
Ordem: variável de ambiente → pasta data/ → Área de trabalho (uso local).
"""
import io
import os
import re
from pathlib import Path
from typing import Any

from config_paths import data_root


def _caminho_planilha() -> Path:
    """Localiza planilha: GRAMADOWAY_PLANILHA, depois data/, depois Desktop."""
    env = os.environ.get("GRAMADOWAY_PLANILHA", "").strip()
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p

    root = data_root()
    for name in (
        "planilha.xlsx",
        "Planilha preços Gramadoway (1).xlsx",
        "Planilha precos Gramadoway (1).xlsx",
    ):
        cand = root / name
        if cand.is_file():
            return cand
    for f in sorted(root.glob("*.xlsx")):
        if "gramadoway" in f.name.lower():
            return f
    for f in sorted(root.glob("*.xlsx")):
        return f

    desktop = Path.home() / "Desktop"
    if desktop.is_dir():
        for f in desktop.glob("*.xlsx"):
            if "gramadoway" in f.name.lower():
                return f

    raise FileNotFoundError(
        f"Planilha .xlsx não encontrada. Opções:\n"
        f"• Coloque o arquivo em: {root} (ex.: planilha.xlsx)\n"
        f"• Ou defina GRAMADOWAY_PLANILHA com o caminho completo\n"
        f"• Ou use o upload na tela do app (nuvem)\n"
        f"• (PC local) Área de trabalho: {desktop}"
    )


def _parse_valor(val: Any) -> float | None:
    """Converte valor para float. Aceita número, 'R$ 99,00' ou 'R$ 99,00 Kg'."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val) if val else None
    s = str(val).strip()
    s = re.sub(r"R\$\s*", "", s, flags=re.I)
    s = s.replace(".", "").replace(",", ".")
    m = re.search(r"[\d.]+", s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            pass
    return None


def _extrair_codigo(produto: str) -> tuple[str, str]:
    """Extrai código do início. Ex: '480- Avião 35g' -> ('480', 'Avião 35g')."""
    produto = str(produto).strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*[-.]?\s*(.*)$", produto)
    if m:
        return m.group(1).strip(), (m.group(2).strip() or produto)
    return "", produto


# --- ABA 1: Personalizados ---
# L1: título | L2: PRODUTO, VALOR, QTIDE, TOTAL | L3+: dados
# Col A=produto (pode ter código), Col B=valor (UN)
def extrair_personalizados(ws) -> list[dict]:
    itens = []
    for r in range(3, ws.max_row + 1):
        prod = ws.cell(r, 1).value
        val = ws.cell(r, 2).value
        if not prod or str(prod).strip() in ("PRODUTO", "TOTAL", ""):
            continue
        preco = _parse_valor(val)
        if preco is None or preco <= 0:
            continue
        cod, nome = _extrair_codigo(prod)
        itens.append({
            "categoria": "Personalizados",
            "codigo": cod,
            "produto": nome or str(prod).strip(),
            "un": "UN",
            "preco": round(preco, 2),
        })
    return itens


# --- ABA 2: Barras ---
# L2: Bloco1 A=sabor B=valor | Bloco2 F=sabor G=valor | Un=KG
def extrair_barras(ws) -> list[dict]:
    itens = []
    for r in range(3, ws.max_row + 1):
        sabor = ws.cell(r, 1).value
        val = ws.cell(r, 2).value
        if sabor and str(sabor).strip() and str(sabor).strip().upper() != "TOTAL":
            preco = _parse_valor(val)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Barras ao Leite",
                    "codigo": "",
                    "produto": str(sabor).strip(),
                    "un": "KG",
                    "preco": round(preco, 2),
                })
    for r in range(3, ws.max_row + 1):
        sabor = ws.cell(r, 6).value
        val = ws.cell(r, 7).value
        if sabor and str(sabor).strip() and str(sabor).strip().upper() != "TOTAL":
            preco = _parse_valor(val)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Barras Branco",
                    "codigo": "",
                    "produto": str(sabor).strip(),
                    "un": "KG",
                    "preco": round(preco, 2),
                })
    return itens


# --- ABA 3: Bombons liquidos ---
# Bloco1: A=tipo B=valor/kg | Bloco2: F=tipo G=valor/und
def extrair_bombons_liquidos(ws) -> list[dict]:
    itens = []
    for r in range(3, ws.max_row + 1):
        tipo = ws.cell(r, 1).value
        val_kg = ws.cell(r, 2).value
        if tipo and str(tipo).strip():
            preco = _parse_valor(val_kg)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Bombons Líquidos",
                    "codigo": "",
                    "produto": f"{str(tipo).strip()} (kg)",
                    "un": "KG",
                    "preco": round(preco, 2),
                })
        tipo2 = ws.cell(r, 6).value
        val_un = ws.cell(r, 7).value
        if tipo2 and str(tipo2).strip():
            preco = _parse_valor(val_un)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Bombons Líquidos",
                    "codigo": "",
                    "produto": f"{str(tipo2).strip()} (un)",
                    "un": "UN",
                    "preco": round(preco, 2),
                })
    return itens


# --- ABA 4: Bombons 12gr ---
# Bloco1: A=tipo B=valor/kg | Bloco2: G=tipo H=valor/und
def extrair_bombons_12gr(ws) -> list[dict]:
    itens = []
    for r in range(3, ws.max_row + 1):
        tipo = ws.cell(r, 1).value
        val_kg = ws.cell(r, 2).value
        if tipo and str(tipo).strip() and "TOTAL" not in str(tipo).upper():
            preco = _parse_valor(val_kg)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Bombons 12gr",
                    "codigo": "",
                    "produto": f"{str(tipo).strip()} (kg)",
                    "un": "KG",
                    "preco": round(preco, 2),
                })
        tipo2 = ws.cell(r, 7).value
        val_un = ws.cell(r, 8).value
        if tipo2 and str(tipo2).strip() and "TOTAL" not in str(tipo2).upper():
            preco = _parse_valor(val_un)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Bombons 12gr",
                    "codigo": "",
                    "produto": f"{str(tipo2).strip()} (un)",
                    "un": "UN",
                    "preco": round(preco, 2),
                })
    return itens


# --- ABA 5: Trufas e trufados ---
# Bloco1: A=sabor B=valor (saco 25) | Bloco2: F=sabor G=valor (und)
def extrair_trufas(ws) -> list[dict]:
    itens = []
    for r in range(3, ws.max_row + 1):
        sabor = ws.cell(r, 1).value
        val = ws.cell(r, 2).value
        if sabor and str(sabor).strip():
            preco = _parse_valor(val)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Trufas",
                    "codigo": "",
                    "produto": f"{str(sabor).strip()} (saco 25)",
                    "un": "SACO",
                    "preco": round(preco, 2),
                })
        sabor2 = ws.cell(r, 6).value
        val2 = ws.cell(r, 7).value
        if sabor2 and str(sabor2).strip():
            preco = _parse_valor(val2)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Trufas",
                    "codigo": "",
                    "produto": f"{str(sabor2).strip()} (un)",
                    "un": "UN",
                    "preco": round(preco, 2),
                })
    return itens


# --- ABA 6: Degustação ---
# A=tipo B=valor (ex: "R$ 99,00 Kg")
def extrair_degustacao(ws) -> list[dict]:
    itens = []
    for r in range(3, ws.max_row + 1):
        tipo = ws.cell(r, 1).value
        val = ws.cell(r, 2).value
        if tipo and str(tipo).strip():
            preco = _parse_valor(val)
            if preco and preco > 0:
                itens.append({
                    "categoria": "Degustação",
                    "codigo": "",
                    "produto": str(tipo).strip(),
                    "un": "KG",
                    "preco": round(preco, 2),
                })
    return itens


# --- ABA 7: Planilha9 ---
# Bloco1 (50% CACAU): A=nome B=preco_kg C=preco_un
# Bloco2 (BOMBOM ESPECIAIS): F=nome G=preco_kg H=preco_un
# Ignorar: 50% CACAU, 70% CACAU, BOMBOM ESPECIAIS (são headers)
def extrair_planilha9(ws) -> list[dict]:
    itens = []
    skip = {"", "50% CACAU", "70% CACAU", "BOMBOM ESPECIAIS"}
    for r in range(3, ws.max_row + 1):
        nome = ws.cell(r, 1).value
        if nome and str(nome).strip() and str(nome).strip() not in skip:
            val_kg = ws.cell(r, 2).value
            val_un = ws.cell(r, 3).value
            preco_kg = _parse_valor(val_kg)
            preco_un = _parse_valor(val_un)
            if preco_kg and preco_kg > 0:
                itens.append({
                    "categoria": "50% Cacau",
                    "codigo": "",
                    "produto": f"{str(nome).strip()} (kg)",
                    "un": "KG",
                    "preco": round(preco_kg, 2),
                })
            if preco_un and preco_un > 0 and preco_un != preco_kg:
                itens.append({
                    "categoria": "50% Cacau",
                    "codigo": "",
                    "produto": f"{str(nome).strip()} (un)",
                    "un": "UN",
                    "preco": round(preco_un, 2),
                })
        nome2 = ws.cell(r, 6).value
        if nome2 and str(nome2).strip() and str(nome2).strip() not in skip:
            val_kg2 = ws.cell(r, 7).value
            val_un2 = ws.cell(r, 8).value
            preco_kg2 = _parse_valor(val_kg2)
            preco_un2 = _parse_valor(val_un2)
            if preco_kg2 and preco_kg2 > 0:
                itens.append({
                    "categoria": "Bombons Especiais",
                    "codigo": "",
                    "produto": f"{str(nome2).strip()} (kg)",
                    "un": "KG",
                    "preco": round(preco_kg2, 2),
                })
            if preco_un2 and preco_un2 > 0 and preco_un2 != preco_kg2:
                itens.append({
                    "categoria": "Bombons Especiais",
                    "codigo": "",
                    "produto": f"{str(nome2).strip()} (un)",
                    "un": "UN",
                    "preco": round(preco_un2, 2),
                })
    return itens


EXTRATORES = {
    "Personalizados": extrair_personalizados,
    "Barras": extrair_barras,
    "Bombons liquidos": extrair_bombons_liquidos,
    "Bombons 12gr": extrair_bombons_12gr,
    "Trufas e trufados": extrair_trufas,
    "Degustação": extrair_degustacao,
    "Planilha9": extrair_planilha9,
}


def extrair_todos_workbook(wb) -> list[dict]:
    """Extrai produtos a partir de um workbook já aberto (openpyxl)."""
    todos = []
    for sn in wb.sheetnames:
        ext = EXTRATORES.get(sn)
        if not ext and "Degust" in sn:
            ext = extrair_degustacao
        if ext:
            try:
                itens = ext(wb[sn])
                todos.extend(itens)
            except Exception as e:
                print(f"Aviso: erro em aba '{sn}': {e}")
    return todos


def extrair_todos_de_bytes(data: bytes) -> list[dict]:
    """Carrega planilha a partir de bytes (upload na nuvem)."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    try:
        return extrair_todos_workbook(wb)
    finally:
        wb.close()


def extrair_todos(caminho: str | Path | None = None) -> list[dict]:
    """Extrai todos os produtos de todas as abas."""
    import openpyxl

    path = caminho or _caminho_planilha()
    wb = openpyxl.load_workbook(path, data_only=True)
    try:
        todos = extrair_todos_workbook(wb)
    finally:
        wb.close()
    return todos
