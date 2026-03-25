# Melhorias aplicadas — Sistema Gramadoway

## Como é feita a identificação KG vs UN vs SACO

Cada **aba** da planilha tem estrutura fixa. O extrator sabe qual unidade usar:

| Aba | Colunas | Unidade |
|-----|---------|---------|
| Personalizados | A-B | UN (sempre unidade) |
| Barras | A-B, F-G | KG (preço por kg) |
| Bombons liquidos | A-B = KG, F-G = UN | KG ou UN conforme bloco |
| Bombons 12gr | A-B = KG, G-H = UN | KG ou UN conforme bloco |
| Trufas | A-B = SACO, F-G = UN | SACO ou UN conforme bloco |
| Degustação | A-B | KG |
| Planilha9 | A-C, F-H | KG ou UN conforme bloco |

O produto recebe o sufixo "(kg)" ou "(un)" quando há as duas opções, para o usuário escolher.

---

## Melhorias implementadas

1. **Coluna "Preço por"** — Mostra R$/kg, R$/un ou R$/saco em cada linha
2. **Instruções expandíveis** — Tabela explicando KG, UN e SACO
3. **Resumo do pedido** — Lista só os itens com quantidade > 0 antes do total
4. **Cálculo com `round(..., 2)`** — Evita erros de ponto flutuante
5. **Validação de quantidade** — Garante valor ≥ 0 e numérico
6. **Export Excel** — Recalcula Total antes de exportar e inclui aba "Resumo" com o total

---

## Recomendações futuras

- **Atualizar preços** — Ao alterar a planilha na área de trabalho, recarregar a página (F5) ou clicar em "Recarregar"
- **Backup** — Manter cópia da planilha de preços antes de alterações
- **Teste** — Conferir alguns itens manualmente: Qtde × Preço = Total
