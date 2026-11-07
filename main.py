from pathlib import Path

from funcoes import carregar_dados, preparar_dados


def main():
    pasta = Path(__file__).resolve().parent
    dados = carregar_dados(pasta / "halloween_vendas.csv")
    tratados = preparar_dados(dados)

    print("Dimensões:", dados.shape)
    print("Dimensões após preparação:", tratados.shape)
    print("Colunas:", dados.columns.tolist())
    print("\nAmostra:")
    print(dados.head(3).to_string(index=False))
    print("\nTipos:")
    print(dados.dtypes)

    colunas_tratadas = [
        "categoria_limpa",
        "canal_normalizado",
        "quantidade_numero",
        "preco_unitario_numero",
        "data_venda_convertida",
        "pedido_com_problema",
    ]
    print("\nAmostra preparada:")
    print(tratados[colunas_tratadas].head(3).to_string(index=False))


if __name__ == "__main__":
    main()
