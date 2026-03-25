"""
Utilitários: máscaras, formatação, CEP, totais do pedido.
"""
import re
from typing import Optional

import pandas as pd


def mascara_cnpj(valor: str) -> str:
    """Aplica máscara 00.000.000/0001-00 ao CNPJ."""
    if not valor:
        return ""
    nums = re.sub(r"\D", "", valor)[:14]
    if len(nums) <= 2:
        return nums
    if len(nums) <= 5:
        return f"{nums[:2]}.{nums[2:]}"
    if len(nums) <= 8:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:]}"
    if len(nums) <= 12:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:]}"
    return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:]}"


def mascara_telefone(valor: str) -> str:
    """Aplica máscara (00) 00000-0000 ou (00) 0000-0000."""
    if not valor:
        return ""
    nums = re.sub(r"\D", "", valor)[:11]
    if len(nums) <= 2:
        return f"({nums}" if nums else ""
    if len(nums) <= 6:
        return f"({nums[:2]}) {nums[2:]}"
    return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}" if len(nums) > 7 else f"({nums[:2]}) {nums[2:]}"


def mascara_cep(valor: str) -> str:
    """Aplica máscara 00000-000 ao CEP."""
    if not valor:
        return ""
    nums = re.sub(r"\D", "", valor)[:8]
    if len(nums) <= 5:
        return nums
    return f"{nums[:5]}-{nums[5:]}"


def formatar_moeda(valor: float) -> str:
    """Formata valor como R$ 1.234,56."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def buscar_cep(cep: str) -> Optional[dict]:
    """Busca endereço pelo CEP via ViaCEP. Retorna dict com logradouro, bairro, localidade, uf."""
    nums = re.sub(r"\D", "", cep)
    if len(nums) != 8:
        return None
    try:
        import urllib.request
        import json
        url = f"https://viacep.com.br/ws/{nums}/json/"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("erro"):
                return None
            logr = (data.get("logradouro") or "").strip()
            comp = (data.get("complemento") or "").strip()
            end = f"{logr} {comp}".strip() if comp else logr
            return {
                "Endereço": end,
                "Bairro": data.get("bairro") or "",
                "Cidade": f"{data.get('localidade') or ''} - {data.get('uf') or ''}".strip(" -"),
            }
    except Exception:
        return None


def aplicar_totais_pedido(df: pd.DataFrame) -> None:
    """Atualiza coluna Total com Qtde × preço (vetorizado, rápido)."""
    q = pd.to_numeric(df["Qtde"], errors="coerce").fillna(0).clip(lower=0)
    p = pd.to_numeric(df["preco"], errors="coerce").fillna(0)
    df["Total"] = (q * p).round(2)


def chaves_produtos_df(df: pd.DataFrame) -> set[tuple[str, str, str]]:
    """Identifica linhas do catálogo (categoria, produto, código)."""
    if df is None or len(df) == 0:
        return set()
    n = len(df)
    if "categoria" in df.columns:
        c = df["categoria"].astype(str).fillna("")
    else:
        c = pd.Series([""] * n)
    if "produto" in df.columns:
        pr = df["produto"].astype(str).fillna("")
    else:
        pr = pd.Series([""] * n)
    if "codigo" in df.columns:
        co = df["codigo"].astype(str).fillna("")
    else:
        co = pd.Series([""] * n)
    return set(zip(c.tolist(), pr.tolist(), co.tolist()))


def sincronizar_df_pedido_com_catalogo(df_catalogo: pd.DataFrame, df_atual: pd.DataFrame) -> pd.DataFrame:
    """
    Substitui o pedido pela lista completa do catálogo e recupera quantidades
    já digitadas quando produto+categoria+código coincidem (ex.: planilha nova com mais linhas).
    """
    df_new = df_catalogo.copy()
    if "codigo" not in df_new.columns:
        df_new["codigo"] = ""
    df_new["un"] = df_new["un"].fillna("UN").replace("", "UN")
    df_new["Qtde"] = 0.0
    df_new["Total"] = 0.0
    for _, row in df_atual.iterrows():
        mask = (
            (df_new["produto"] == row["produto"])
            & (df_new["categoria"] == row["categoria"])
            & (df_new["codigo"].astype(str) == str(row.get("codigo", "") or ""))
        )
        if mask.any():
            ix = df_new.index[mask][0]
            try:
                q = float(row.get("Qtde", 0) or 0)
            except (TypeError, ValueError):
                q = 0.0
            df_new.loc[ix, "Qtde"] = max(0.0, q)
    aplicar_totais_pedido(df_new)
    return df_new
