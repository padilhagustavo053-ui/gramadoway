"""
Catálogo de produtos embutido — mesma estrutura que extrair.py devolve.
Usado quando não há planilha .xlsx nem upload: abre a página e já funciona.
Substitua por planilha real quando quiser (upload ou data/planilha.xlsx).
Baseado na especificação Gramadoway (personalizados, barras kg, bombons, trufas, etc.).
"""
from __future__ import annotations


def produtos_padrao() -> list[dict]:
    """Se existir data/planilha.xlsx, usa a planilha real; senão lista demo pequena."""
    try:
        from config_paths import data_root
        from extrair import extrair_todos

        p = data_root() / "planilha.xlsx"
        if p.is_file():
            todos = extrair_todos(p)
            if todos:
                return todos
    except Exception:
        pass

    out: list[dict] = []

    def p(cat, cod, nome, un, preco):
        out.append(
            {
                "categoria": cat,
                "codigo": str(cod) if cod is not None else "",
                "produto": nome,
                "un": un,
                "preco": round(float(preco), 2),
            }
        )

    # Personalizados (UN) — exemplos do plano + linha típica
    for cod, nome, pr in [
        ("480", "Avião 35g", 6.50),
        ("73", "Barra Chocolate 70g", 11.70),
        ("101", "Ovo P 50g", 12.50),
        ("102", "Coração 80g", 18.90),
        ("201", "Caixa sortida P", 24.00),
        ("202", "Caixa sortida M", 38.00),
        ("310", "Trufa decorada unidade", 4.20),
        ("415", "Tablete personalizado", 9.90),
        ("520", "Bombom recheado especial", 3.80),
    ]:
        p("Personalizados", cod, nome, "UN", pr)

    # Barras ao leite (KG)
    for nome, pr in [
        ("MARULA", 128.0),
        ("DAMASCO", 128.0),
        ("MARACUJÁ", 128.0),
        ("LARANJA", 130.0),
        ("CAFÉ", 132.0),
        ("NOZES", 135.0),
        ("AMÊNDOA", 135.0),
        ("COCO", 125.0),
        ("MENTA", 126.0),
        ("TRADICIONAL AO LEITE", 118.0),
        ("MEIO AMARGO BLEND", 122.0),
    ]:
        p("Barras ao Leite", "", nome, "KG", pr)

    # Barras branco (KG)
    for nome, pr in [
        ("Branco com nibs", 102.0),
        ("Branco limão", 104.0),
        ("Branco morango", 104.0),
    ]:
        p("Barras Branco", "", nome, "KG", pr)

    # Bombons líquidos — kg e un (como na planilha)
    for nome, pr in [
        ("Leite Condensado", 149.0),
        ("Licor cereja", 155.0),
        ("Brigadeiro gourmet", 142.0),
        ("Doce de leite", 138.0),
    ]:
        p("Bombons Líquidos", "", f"{nome} (kg)", "KG", pr)
    for nome, pr in [
        ("Leite Condensado", 3.00),
        ("Licor fino", 4.50),
        ("Trufa líquida", 3.80),
        ("Cereja", 4.20),
    ]:
        p("Bombons Líquidos", "", f"{nome} (un)", "UN", pr)

    # Bombons 12gr
    for nome, pr in [
        ("Sortido premium", 140.0),
        ("Meio amargo 12g", 136.0),
        ("Ao leite 12g", 132.0),
    ]:
        p("Bombons 12gr", "", f"{nome} (kg)", "KG", pr)
    for nome, pr in [
        ("Trufa ouro", 3.20),
        ("Cappuccino", 2.90),
        ("Romeu e Julieta", 3.10),
        ("Nozes", 3.40),
    ]:
        p("Bombons 12gr", "", f"{nome} (un)", "UN", pr)

    # Trufas — saco 25 e un
    for nome, pr in [
        ("Trufa tradicional", 85.0),
        ("Trufa pistache", 92.0),
        ("Trufa maracujá", 88.0),
        ("Trufa champagne", 95.0),
    ]:
        p("Trufas", "", f"{nome} (saco 25)", "SACO", pr)
    for nome, pr in [
        ("Trufa tradicional", 5.50),
        ("Trufa pistache", 6.20),
        ("Trufa limão", 5.80),
    ]:
        p("Trufas", "", f"{nome} (un)", "UN", pr)

    # Degustação
    for nome, pr in [
        ("Mesa degustação", 150.0),
        ("Kit degustação P", 45.0),
        ("Kit degustação G", 85.0),
    ]:
        p("Degustação", "", nome, "KG", pr)

    # Planilha9 — 50% cacau e bombons especiais
    for nome, pkg, un, pr in [
        ("Tablete 50% cacau", "(kg)", "KG", 88.0),
        ("Barra premium 50%", "(kg)", "KG", 92.0),
        ("Nibs 50%", "(kg)", "KG", 98.0),
        ("Tablete 50% cacau", "(un)", "UN", 8.50),
        ("Mini tablete", "(un)", "UN", 5.50),
    ]:
        p("50% Cacau", "", f"{nome} {pkg}".strip(), un, pr)
    for nome, pkg, un, pr in [
        ("Bombom especial sortido", "(kg)", "KG", 160.0),
        ("Bombom licor", "(kg)", "KG", 168.0),
        ("Bombom especial", "(un)", "UN", 6.00),
        ("Bombom crocante", "(un)", "UN", 5.50),
    ]:
        p("Bombons Especiais", "", f"{nome} {pkg}".strip(), un, pr)

    return out
