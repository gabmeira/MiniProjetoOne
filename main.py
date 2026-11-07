from pathlib import Path

from funcoes import carregar_dados, preparar_dados, resumir_qualidade, investigar_entregas


def main():
    pasta = Path(__file__).resolve().parent
    dados = carregar_dados(pasta / "halloween_vendas.csv")
    tratados = preparar_dados(dados)
    qualidade = resumir_qualidade(tratados)
    entregas = investigar_entregas(tratados)

    print("Dimensões:", dados.shape)
    print("Dimensões após preparação:", tratados.shape)
    print("Colunas:", dados.columns.tolist())
    print("\nAmostra:")
    print(dados.head(3).to_string(index=False))
    print("\nTipos:")
    print(dados.dtypes)

    print("\nDiagnóstico de qualidade:")
    print(f"Total de pedidos: {qualidade['total_pedidos']}")
    print("Categorias:")
    print(f"  Vazias preenchidas: {qualidade['categorias_vazias_preenchidas']}")
    print(f"  Não vazias alteradas: {qualidade['categorias_nao_vazias_alteradas']}")
    print(f"    Apenas caixa: {qualidade['categorias_alteradas_apenas_caixa']}")
    print(f"    Espaços/pontuação: {qualidade['categorias_alteradas_espacos_pontuacao']}")
    print("Canais:")
    print(f"  Reconhecidos com valor normalizado diferente do original: {qualidade['canais_alterados']}")
    print(f"  Não reconhecidos: {qualidade['canais_nao_reconhecidos']}")

    print("\nCampos numéricos obrigatórios (ausentes, não numéricos, inválidos):")
    for coluna in ("quantidade", "preco_unitario"):
        print(
            f"  {coluna}: {qualidade[f'{coluna}_ausentes']}, "
            f"{qualidade[f'{coluna}_nao_numericos']}, {qualidade[f'{coluna}_invalidos']}"
        )
    print("Campos complementares (custo e desconto; ausentes, não numéricos, inválidos):")
    for coluna in ("custo_unitario", "desconto_pct"):
        print(
            f"  {coluna}: {qualidade[f'{coluna}_ausentes']}, "
            f"{qualidade[f'{coluna}_nao_numericos']}, {qualidade[f'{coluna}_invalidos']}"
        )
    print(
        "Observação: inválidos inclui ausentes e valores não numéricos; "
        "não some essas contagens novamente."
    )
    print(f"Datas de venda inválidas: {qualidade['datas_venda_invalidas']}")
    print(
        "Pedidos com problema numérico obrigatório (quantidade ou preço): "
        f"{qualidade['pedidos_com_problema_numerico_obrigatorio']}"
    )
    print(
        "Pedidos com quantidade, preço ou data de venda inválida "
        "(não inclui ajustes de categoria/canal nem custo/desconto): "
        f"{qualidade['pedidos_com_problema_core']}"
    )

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

    print("\nInvestigação de entregas:")
    print(f"Pedidos cancelados: {entregas['total_cancelados']}")
    print(f"Pedidos sem data de entrega: {entregas['sem_entrega_total']}")
    print(f"  Sem data de entrega com status Cancelado: {entregas['sem_entrega_cancelados']}")
    print(f"  Sem data de entrega com outro status: {entregas['sem_entrega_outros_status']}")
    if entregas["hipotese_confirmada"] is None:
        print("Conclusão: sem casos para avaliar.")
    elif entregas["hipotese_confirmada"]:
        print("Conclusão: compatível nesta base, não prova regra geral.")
    else:
        print(
            "Conclusão: a hipótese de que todos os pedidos sem data de entrega são "
            "cancelados é falsa; há "
            f"{entregas['sem_entrega_outros_status']} contraexemplos."
        )
    if entregas["exemplos"]:
        print("Exemplos de pedidos sem data de entrega com outro status:")
        for exemplo in entregas["exemplos"]:
            print(
                f"  Pedido {exemplo['pedido_id']} | status: {exemplo['status_pedido']} | "
                f"venda: {exemplo['data_venda']} | entrega: {exemplo['data_entrega'] or '(vazia)'}"
            )


if __name__ == "__main__":
    main()
