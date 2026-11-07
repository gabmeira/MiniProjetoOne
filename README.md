# MiniProjetoOne — Festa em Cena

## Problema e objetivo

Este projeto analisa uma base fictícia de pedidos da loja Festa em Cena. O arquivo contém 1.500 registros de agosto a novembro de 2024 e de 2025. Cada linha representa um pedido de um produto; `quantidade` informa quantas unidades desse produto foram pedidas. Por isso, as contagens deste projeto são de pedidos, não de unidades.

O trabalho prepara e verifica os dados, resume problemas de qualidade, investiga a relação entre pedidos sem data de entrega e status cancelado e conta pedidos por canal e por mês. Os resultados descrevem somente esta base fictícia.

## Dados de entrada

O arquivo de origem é [`halloween_vendas.csv`](halloween_vendas.csv), na raiz do projeto. Ele tem 14 colunas:

| Coluna | Significado |
|---|---|
| `pedido_id` | Identificador do pedido |
| `data_venda` | Data e hora em que o pedido foi registrado |
| `produto` | Nome do produto pedido |
| `categoria` | Categoria do produto |
| `canal_venda` | Canal usado na venda |
| `cidade` | Cidade do pedido |
| `quantidade` | Unidades do produto no pedido |
| `preco_unitario` | Preço por unidade |
| `custo_unitario` | Custo por unidade |
| `desconto_pct` | Desconto percentual |
| `status_pedido` | Status do pedido |
| `publico` | Público associado ao produto |
| `tamanho` | Tamanho do produto |
| `data_entrega` | Data e hora da entrega, quando informada |

## Estrutura do projeto

- [`main.py`](main.py) coordena a leitura, preparação, análise, impressão do resumo e exportação dos arquivos.
- [`funcoes.py`](funcoes.py) contém as funções de carga, limpeza, validação, análise e exportação.
- [`resultados/`](resultados/) reúne os seis arquivos gerados pela execução.
- [`tests/test_preparacao.py`](tests/test_preparacao.py) contém testes automatizados das regras de preparação e dos resumos.

## Preparação e regras de análise

- A leitura mantém os valores como texto e preserva campos vazios, para que a ausência possa ser identificada explicitamente.
- Categorias são convertidas para minúsculas, têm espaços repetidos reduzidos a um, pontuação e dígitos removidos; categoria vazia recebe o rótulo `sem categoria`.
- Os canais conhecidos são padronizados como `Web`, `Loja física` e `Mercado`. Valores fora desses três grupos são marcados como `Não reconhecido`.
- Quantidade precisa ser um número inteiro maior que zero. Preço unitário precisa ser numérico e maior ou igual a zero.
- Ausências e valores inválidos recebem indicadores. Quantidade, preço, custo, desconto e datas não são preenchidos por estimativa; custo e desconto são campos complementares e não entram no total de pedidos com problema principal.
- Datas de venda são lidas com `datetime.strptime` no formato `%Y-%m-%d %H:%M:%S`. A conversão inválida fica identificada, e a representação original é mantida nos dados de origem; `strftime` adiciona a forma brasileira formatada em outra coluna.
- As verificações de quantidade, preço e data são combinadas por linha com `np.column_stack` e `np.where`: um pedido com mais de um desses problemas é contado uma vez no indicador `pedido_com_problema`.
- Os resumos por canal e por mês contam pedidos de todos os status. O agrupamento mensal inclui somente datas válidas; o agrupamento por canal inclui somente canais reconhecidos. Essas exclusões são independentes.

## Resultados principais

Na base de 1.500 pedidos, 18 categorias vazias receberam o rótulo `sem categoria`. Das categorias não vazias, 1.482 foram normalizadas: 1.351 mudanças foram somente de maiúsculas/minúsculas e 131 envolveram espaços ou pontuação. Foram padronizados 45 canais e nenhum canal ficou sem reconhecimento.

Há 7 quantidades inválidas e 12 preços unitários inválidos. Em 19 pedidos existe ao menos um problema numérico obrigatório. Quatro datas de venda são inválidas; ao combinar quantidade, preço e data, 23 pedidos têm ao menos um problema. Os campos complementares têm 7 custos inválidos e nenhum desconto inválido; esses problemas não alteram a contagem dos 23 pedidos.

O canal Web aparece em 666 pedidos (44,4%), seguido por Loja física (551) e Mercado (283). Web é o maior canal nesta base, mas não representa a maioria dos pedidos. Por mês, outubro de 2025 tem 410 pedidos contra 393 em outubro de 2024: uma diferença de 17 pedidos, ou aproximadamente 4,3%. Os totais mensais incluem todos os status; quatro datas inválidas foram excluídas, restando 1.496 pedidos na análise temporal.

Há 143 pedidos sem data de entrega: 109 têm status `Cancelado` e 34 têm status `Concluído`. Portanto, a hipótese de que todos os pedidos sem data de entrega são cancelados não se confirma. A saída inclui até três exemplos dos casos com outro status.

## Arquivos gerados

Execute `main.py` para gerar ou atualizar os arquivos abaixo em `resultados/`:

1. [Dados processados com indicadores](resultados/dados_processados_com_indicadores.csv) — dados originais e colunas derivadas de limpeza, validação e componentes de data (1.500 linhas, 44 colunas).
2. [Pedidos por canal](resultados/pedidos_por_canal.csv) — contagem por canal reconhecido.
3. [Pedidos por ano e mês](resultados/pedidos_por_ano_mes.csv) — contagem por mês de venda válida.
4. [Exemplos sem data de entrega](resultados/exemplos_sem_data_entrega.csv) — até três pedidos sem entrega registrada e com status diferente de `Cancelado`.
5. [Resumo de análise em JSON](resultados/resumo_analise.json) — contagens de qualidade, entregas, canal e mês em formato estruturado.
6. [Resumo de análise em Markdown](resultados/resumo_analise.md) — versão legível das conclusões exportadas.

O arquivo [`report.md`](report.md) também está na raiz do projeto.

## Como executar

Use Python 3.12 ou superior; o projeto foi validado com Python 3.14.7. As dependências têm versões fixadas em [`requirements.txt`](requirements.txt).

Abra um terminal nesta pasta. Se o ambiente virtual `.venv` ainda não existir, crie-o:

```bash
python3 -m venv .venv
```

Ative o ambiente, inclusive quando ele já existir, instale as dependências e execute o programa:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

O arquivo `halloween_vendas.csv` deve ficar na raiz do projeto. `main.py` localiza o CSV a partir da pasta do próprio script, então também pode ser chamado pelo caminho completo a partir de outra pasta, por exemplo: `python "/caminho/para/MiniProjetoOne/main.py"`.

Os testes existentes são opcionais e podem ser executados com:

```bash
python -m unittest discover -s tests
```

## Limites e reflexão sobre aprendizado de máquina

A base é fictícia e cobre somente os períodos informados. Os números descrevem registros, sem demonstrar causas, comportamento de clientes fora da base, receita ou unidades vendidas. A diferença entre os meses de outubro é apenas uma comparação descritiva.

Uma limpeza consistente ajuda a reduzir erros de formato, mas não garante que os dados representem uma população real nem que um modelo seja confiável. Este projeto não define um alvo de previsão nem avalia modelos. Antes de treinar um modelo, seria necessário justificar o objetivo, verificar a representatividade, escolher uma divisão de treino e avaliação adequada e evitar vazamento de informação — por exemplo, usar campos que só são conhecidos depois do resultado que se deseja prever.
