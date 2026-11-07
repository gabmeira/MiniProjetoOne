from pathlib import Path

from funcoes import (
    _converter_data,
    _limpar_categoria,
    carregar_dados,
    normalizar_canal,
    preparar_dados,
)

PASTA = Path(__file__).resolve().parent
dado = carregar_dados(PASTA / "halloween_vendas.csv")
tratados = preparar_dados(dado)

print("Dimensões:", dado.shape)
print("Dimensões após preparação:", tratados.shape)
print("Colunas:", dado.columns.tolist())
print("\nAmostra:")
print(dado.head(3).to_string(index=False))
print("\nTipos:")
print(dado.dtypes)

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

for texto in ["Fantasia", "  FANTASIA!!!  ", "", " Acessorio "]:
    print(repr(texto), "->", repr(_limpar_categoria(texto)))

for texto in ["Web", " web ", "LOJA FÍSICA"]:
    print(repr(texto), "->", repr(normalizar_canal(texto)))

data = _converter_data("2024-10-29 18:41:26")
print(data.strftime("%d/%m/%Y %H:%M:%S"))
print(_converter_data("2024-02-30 10:00:00"))
print(_converter_data(""))
