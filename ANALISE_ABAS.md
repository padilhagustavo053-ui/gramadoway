# Análise completa — Planilha preços Gramadoway

## Resumo

| Aba | Produtos | Estrutura | Unidades |
|-----|----------|----------|----------|
| Personalizados | ~286 | Col A=produto, B=valor | UN |
| Barras | ~102 | 2 blocos: Ao Leite (A-B), Branco (F-G) | KG |
| Bombons liquidos | ~26 | 2 blocos: KG (A-B), UND (F-G) | KG, UN |
| Bombons 12gr | ~40 | 2 blocos: KG (A-B), UND (G-H) | KG, UN |
| Trufas e trufados | ~64 | 2 blocos: Saco 25 (A-B), UND (F-G) | SACO, UN |
| Degustação | ~4 | A=tipo, B=valor | KG |
| Planilha9 | ~76 | 2 blocos: 50% Cacau (A-C), Bombons Especiais (F-H) | KG, UN |

**Total: ~598 produtos**

---

## Detalhamento por aba

### 1. Personalizados
- **Cabeçalho:** L1=título, L2=PRODUTO, VALOR, QTIDE, TOTAL
- **Dados:** L3+ | Col A=produto (pode ter código "480- Avião 35g"), Col B=valor
- **Unidade:** UN (única)
- **Observação:** Código extraído do início do produto com regex

### 2. Barras
- **Bloco 1 (Barras ao Leite):** Col A=sabor, B=valor/kg
- **Bloco 2 (Barras Branco):** Col F=sabor, G=valor/kg
- **Unidade:** KG em ambos
- **Linha inicial:** 3

### 3. Bombons liquidos
- **Bloco 1:** Col A=tipo, B=valor/kg (ex: 149)
- **Bloco 2:** Col F=tipo, G=valor/und (ex: 3)
- **Produtos:** Mesmo tipo gera 2 linhas — "(kg)" e "(un)"

### 4. Bombons 12gr
- **Bloco 1:** Col A=tipo, B=valor/kg
- **Bloco 2:** Col G=tipo, H=valor/und
- **Ignorar:** Linhas com "TOTAL"

### 5. Trufas e trufados
- **Bloco 1:** Col A=sabor, B=valor (saco 25 un)
- **Bloco 2:** Col F=sabor, G=valor (und)
- **Unidades:** SACO e UN

### 6. Degustação
- **Estrutura:** Col A=tipo, B=valor (ex: "R$ 99,00 Kg")
- **Parsing:** Extrair número de strings com "R$" e "Kg"

### 7. Planilha9
- **Bloco 1 (50% Cacau):** Col A=nome, B=preco_kg, C=preco_un
- **Bloco 2 (Bombons Especiais):** Col F=nome, G=preco_kg, H=preco_un
- **Ignorar:** "50% CACAU", "70% CACAU", "BOMBOM ESPECIAIS" (headers)
- **Regra:** Só criar linha UN se preco_un ≠ preco_kg

---

## Extrator

O arquivo `extrair.py` implementa um extrator específico para cada aba, validado contra a estrutura real da planilha.
