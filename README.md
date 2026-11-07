# MiniProjetoOne

## Entendimento dos dados

Cada linha representa 

| Coluna | Significado |
|---|---|
| pedido_id | identificador do pedido |
| produto | descrição do pedido (nome) |
| quantidade | quantidade de produto pedido |
| canal_venda | onde foi vendido (site, loja etc...) |

## Executar o projeto

Use Python 3.12 ou superior (validado com Python 3.14.7). As versões das bibliotecas usadas nesta etapa estão registradas em `requirements.txt`.

Abra um terminal nesta pasta do projeto. Se o ambiente virtual `.venv` ainda não existir, crie-o:

```bash
python3 -m venv .venv
```

Ative o ambiente, inclusive quando ele já existir:

```bash
source .venv/bin/activate
```

Instale as dependências e execute o programa:

```bash
python -m pip install -r requirements.txt
python main.py
```

O resultado esperado informa 1500 linhas e 14 colunas na base original, e 1500 linhas e 44 colunas após a preparação. O arquivo `halloween_vendas.csv` deve ficar na raiz do projeto. O próprio `main.py` localiza o CSV a partir da pasta onde está salvo, então o comando pode ser iniciado de outra pasta desde que seja passado o caminho do script, por exemplo `python "/caminho/para/MiniProjetoOne/main.py"`.

Os testes automatizados existentes são opcionais e podem ser executados com `python -m unittest discover -s tests`.
