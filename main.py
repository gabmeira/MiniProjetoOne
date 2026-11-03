from pathlib import Path

from funcoes import carregar_dados

PASTA = Path(__file__).resolve().parent
dado = carregar_dados(PASTA / "halloween_vendas.csv")

print("Dimensões:", dado.shape)
print("Colunas:", dado.columns.tolist())
print("\nAmostra:")
print(dado.head(3).to_string(index=False))
print("\nTipos:")
print(dado.dtypes)

from funcoes import _limpar_categoria, normalizar_canal

for texto in ["Fantasia", "  FANTASIA!!!  ", "", " Acessorio "]:
    print(repr(texto), "->", repr(_limpar_categoria(texto)))

for texto in ["Web", " web ", "LOJA FÍSICA"]:
    print(repr(texto), "->", repr(normalizar_canal(texto)))