# Resumo da análise

## Qualidade e normalização

- Pedidos analisados: 1500.
- Categorias vazias preenchidas: 18; categorias não vazias alteradas: 1482 (apenas caixa: 1351; espaços/pontuação: 131).
- Canais alterados: 45; não reconhecidos: 0.
- Problemas numéricos obrigatórios (quantidade ou preço): 19 pedidos.
- Quantidade inválida: 7 pedidos; preço unitário inválido: 12 pedidos (12 ausentes; 0 não numéricos).
- Problemas no conjunto principal (quantidade, preço ou data de venda): 23 pedidos, incluindo 4 datas de venda inválidas.
- Campos complementares: custo inválido em 7 pedidos; desconto inválido em 0 pedidos. Contagens de inválidos já incluem ausentes e não devem ser somadas novamente.

## Entregas

- Pedidos cancelados: 109.
- Pedidos sem data de entrega: 143; com status Cancelado: 109; com outro status: 34.
- Hipótese de que todos os pedidos sem data de entrega são cancelados: A hipótese não se confirma nesta base: há pedidos sem data de entrega com outro status.

## Pedidos por canal reconhecido

| canal_normalizado | pedidos |
| --- | --- |
| Web | 666 |
| Loja física | 551 |
| Mercado | 283 |

Excluídos por canal não reconhecido: 0.

## Pedidos por ano/mês de venda válida

| ano_mes | pedidos |
| --- | --- |
| 2024-08 | 77 |
| 2024-09 | 104 |
| 2024-10 | 393 |
| 2024-11 | 174 |
| 2025-08 | 62 |
| 2025-09 | 94 |
| 2025-10 | 410 |
| 2025-11 | 182 |

Excluídos por data de venda inválida: 4.

## Limitações

As contagens representam pedidos registrados de todos os status; não representam unidades vendidas nem receita. A base é fictícia e as conclusões descrevem somente os registros analisados.
