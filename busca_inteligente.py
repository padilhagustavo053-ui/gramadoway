"""
Busca inteligente — fuzzy search e atalhos rápidos para 200+ produtos.
"""
from difflib import SequenceMatcher
from typing import Optional


def similaridade(a: str, b: str) -> float:
    """Retorna similaridade 0-1 entre duas strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def buscar_produtos(df, termo: str, limite: int = 30) -> "pd.DataFrame":
    """Busca fuzzy em produtos. Ordena por relevância (match no início > similaridade)."""
    if not termo or len(termo.strip()) < 2:
        return df.head(limite)  # Sem busca: primeiros N produtos
    termo = termo.strip().lower()
    resultados = []
    for idx, row in df.iterrows():
        prod = str(row.get("produto", "")).lower()
        cod = str(row.get("codigo", "")).lower()
        cat = str(row.get("categoria", row.get("aba", ""))).lower()
        # Score: match exato no início > contém > similaridade
        score = 0.0
        if termo in prod:
            score = 0.9 + (0.1 if prod.startswith(termo) else 0)
        elif termo in cod:
            score = 0.95
        elif termo in cat:
            score = 0.7
        else:
            score = max(similaridade(termo, prod), similaridade(termo, cod) * 1.2)
        if score > 0.25:
            resultados.append((score, idx, row))
    resultados.sort(key=lambda x: -x[0])
    indices = [r[1] for r in resultados[:limite]]
    return df.loc[indices] if indices else df.head(0)


def parsear_atalho(texto: str) -> Optional[tuple[str, float]]:
    """
    Parseia "produto 5" ou "código 10" -> (termo_busca, quantidade).
    Retorna None se não conseguir parsear.
    """
    texto = texto.strip()
    if not texto:
        return None
    partes = texto.rsplit(maxsplit=1)
    if len(partes) == 2:
        try:
            qtd = float(partes[1].replace(",", "."))
            if qtd >= 0:
                return (partes[0].strip(), qtd)
        except ValueError:
            pass
    return (texto, 1.0) if texto else None
