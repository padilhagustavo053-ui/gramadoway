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
