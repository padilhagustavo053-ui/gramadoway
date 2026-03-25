"""
Copia a planilha Gramadoway (Desktop, Downloads, etc.) para data/planilha.xlsx.
Assim o Streamlit e a Cloud (após git push) usam a lista completa.

Uso:
  python scripts/sincronizar_planilha_desktop.py
  python scripts/sincronizar_planilha_desktop.py "C:\\caminho\\completo\\ficheiro.xlsx"
"""
from __future__ import annotations

import os
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config_paths import data_root  # noqa: E402
from extrair import (  # noqa: E402
    extrair_todos,
    _melhor_xlsx_em_pasta,
    _pastas_onde_procurar_planilha,
    _pontuacao_nome_planilha,
)


def _mapear_aba_exibicao(categoria: str) -> str:
    if categoria == "Personalizados":
        return "Personalizados"
    if categoria in ("Barras ao Leite", "Barras Branco"):
        return "Barras"
    if categoria == "Bombons Líquidos":
        return "Bombons líquidos"
    if categoria == "Bombons 12gr":
        return "Bombons 12gr"
    if categoria == "Trufas":
        return "Trufas"
    if categoria == "Degustação":
        return "Degustação"
    if categoria in ("50% Cacau", "Bombons Especiais"):
        return "Planilha9"
    return categoria


def _mesmo_ficheiro(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


def _origem_fora_de_data(dest: Path) -> Path:
    """
    Não usa data/planilha.xlsx como origem (evita copiar o ficheiro para cima de si mesmo).
    Procura: GRAMADOWAY_PLANILHA, Desktop/Downloads, outros .xlsx em data/ (exceto planilha.xlsx).
    """
    dest = dest.resolve()
    env = os.environ.get("GRAMADOWAY_PLANILHA", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_file() and not _mesmo_ficheiro(p, dest):
            return p

    for pasta in _pastas_onde_procurar_planilha():
        melhor = _melhor_xlsx_em_pasta(pasta)
        if melhor is not None and not _mesmo_ficheiro(melhor.resolve(), dest):
            return melhor.resolve()

    root_data = data_root()
    scored: list[tuple[int, float, Path]] = []
    for f in root_data.glob("*.xlsx"):
        if f.name.lower() == "planilha.xlsx":
            continue
        sc = _pontuacao_nome_planilha(f.name)
        if sc > 0:
            scored.append((sc, f.stat().st_mtime, f.resolve()))
    if scored:
        scored.sort(key=lambda t: (-t[0], -t[1]))
        cand = scored[0][2]
        if not _mesmo_ficheiro(cand, dest):
            return cand

    raise FileNotFoundError(
        "Não encontrei um Excel de origem (Área de trabalho / Downloads / outro .xlsx em data/).\n"
        "Guarde e feche o Excel. Depois:\n"
        f'  python scripts/sincronizar_planilha_desktop.py "C:\\caminho\\para\\sua_planilha.xlsx"'
    )


def main() -> None:
    dest_dir = ROOT / "data"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = (dest_dir / "planilha.xlsx").resolve()

    if len(sys.argv) > 1:
        src = Path(sys.argv[1]).expanduser().resolve()
        if not src.is_file():
            print(f"ERRO: ficheiro não existe: {src}")
            sys.exit(1)
        print(f"Origem (caminho manual): {src}")
    else:
        try:
            src = _origem_fora_de_data(dest)
            print(f"Origem (detetada): {src}")
        except FileNotFoundError as e:
            print(str(e))
            sys.exit(1)

    if _mesmo_ficheiro(src, dest):
        print(f"Origem já é {dest.name} — a saltar cópia. A validar extração...")
    else:
        try:
            shutil.copy2(src, dest)
            print(f"Copiado para: {dest}")
        except PermissionError:
            print()
            print("ERRO: O Windows bloqueou a gravação (ficheiro em uso).")
            print("  → Feche o Excel e qualquer app que tenha aberto:")
            print(f"     {dest}")
            print("  → Se usar Streamlit local, pare-o ou feche o browser e tente de novo.")
            sys.exit(1)

    produtos = extrair_todos(dest)
    por_aba = Counter(_mapear_aba_exibicao(p["categoria"]) for p in produtos)
    ordem = [
        "Personalizados",
        "Barras",
        "Bombons líquidos",
        "Bombons 12gr",
        "Trufas",
        "Degustação",
        "Planilha9",
    ]
    print()
    print("--- Resumo da extração (como nas abas do app) ---")
    for aba in ordem:
        if aba in por_aba:
            print(f"  {aba}: {por_aba[aba]}")
    for aba, n in sorted(por_aba.items()):
        if aba not in ordem:
            print(f"  {aba}: {n}")
    print(f"  TOTAL: {len(produtos)} produtos")
    print()
    print("Próximo passo para a Streamlit Cloud: faça commit e push de data/planilha.xlsx")


if __name__ == "__main__":
    main()
