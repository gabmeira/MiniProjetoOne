# Relatório de análise — Festa em Cena

## Escopo e método

A análise cobre 1.500 pedidos da base fictícia Festa em Cena, de agosto a novembro de 2024 e 2025. Cada linha representa um pedido de um produto, que pode incluir várias unidades; a contagem é de pedidos, não de unidades.

O processamento modular em Python usou Pandas e NumPy, expressões regulares para normalizar textos e conversão de datas para agrupamentos. Os originais foram preservados; ausências e inválidos foram sinalizados, sem imputação.

## Qualidade dos dados

Havia 18 categorias vazias. Entre as 1.482 não vazias, 1.351 alterações foram apenas de caixa e 131 envolveram espaços ou pontuação. Foram normalizados 45 canais; nenhum permaneceu não reconhecido. Sem isso, variações de escrita fragmentariam as contagens.

Havia 7 quantidades e 12 preços unitários inválidos (19 pedidos com problema obrigatório) e 4 datas de venda inválidas, totalizando 23 pedidos com problema central. Outros 7 custos unitários inválidos são complementares. Não foram inventados valores numéricos nem datas.

## Resultados

Web foi o maior canal, com 666 pedidos (44,4%), seguido por Loja física (551) e Mercado (283). Não ultrapassa metade do total; as contagens não representam unidades ou receita.

As contagens mensais incluem todos os status; as 4 datas inválidas ficaram fora, então 1.496 pedidos compõem os agrupamentos. Outubro registrou 393 pedidos em 2024 e 410 em 2025: 17 a mais (+4,3%). É uma diferença observada, não prova de tendência, campanha ou causa. Como há somente quatro meses por ano, não se deve extrapolar para o ano inteiro.

143 pedidos não têm data de entrega: 109 cancelados e 34 com status Concluído. A hipótese de que toda ausência corresponde a cancelamento não se confirma. A lacuna não prova que não houve entrega; é preciso investigar o preenchimento.

## Limites e reflexão

Os achados são descritivos, de base sintética, com inconsistências e janela curta; não demonstram causalidade e as contagens não medem receita. Antes de orientar decisões, cabe validar definições, investigar o preenchimento da entrega e ampliar a cobertura temporal.

Limpeza e resumo não bastam para aprendizado de máquina: são necessários dados representativos, alvo confiável e avaliação adequada. Sem isso, o modelo pode reproduzir lacunas com aparência de precisão. Preservar originais e registrar regras torna a análise auditável e separa observação de inferência.
