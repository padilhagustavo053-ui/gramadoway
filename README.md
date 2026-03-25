# Sistema de Pedidos Gramadoway

Sistema **potente, robusto e grandioso** para formulário de pedidos da Gramadoway — standalone, sem Google Sheets.

## Como usar

1. **Coloque a planilha** `Planilha preços Gramadoway (1).xlsx` na **área de trabalho**
2. **Execute** o sistema:
   - Duplo clique em `INICIAR.bat`, ou
   - No terminal: `python -m streamlit run app.py`
3. **Abra** http://localhost:8501 no navegador
4. Preencha os dados do cliente e as quantidades desejadas
5. O total é calculado automaticamente
6. Clique em **Baixar pedido.xlsx** para exportar

## Requisitos

- Python 3.10+
- Planilha Gramadoway na área de trabalho

```bash
pip install -r requirements.txt
```

## Funcionalidades

- **Design profissional** — Logo GRAMADOWAY, cores marrom/bege, layout inspirado em formulários de chocolates artesanais
- **Seção CLIENTE** — Campos em duas colunas (Razão Social, CNPJ, Endereço, Fone, Cond. Pagto, etc.)
- **~598 produtos** — Extraídos de todas as 7 abas da planilha
- **Filtro por categoria** e busca por nome
- **Coluna Qtde editável** — Total = Qtde × Preço
- **Exportação Excel** — Abas Cliente + Pedido

## Análise das abas

Cada aba foi analisada individualmente. Ver `ANALISE_ABAS.md` para detalhes.
