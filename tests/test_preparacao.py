import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from funcoes import (
    _converter_data,
    _limpar_categoria,
    carregar_dados,
    exportar_resultados,
    investigar_entregas,
    normalizar_canal,
    preparar_dados,
    resumir_qualidade,
    resumir_pedidos,
)


PASTA = Path(__file__).resolve().parents[1]


def linha(**alteracoes):
    valores = {
        "pedido_id": "1",
        "data_venda": "2024-10-29 18:41:26",
        "produto": "Fantasia",
        "categoria": "Fantasia",
        "canal_venda": "Web",
        "cidade": "Curitiba",
        "quantidade": "2",
        "preco_unitario": "10.50",
        "custo_unitario": "5.00",
        "desconto_pct": "0",
        "status_pedido": "Concluído",
        "publico": "Adulto",
        "tamanho": "M",
        "data_entrega": "2024-11-03 18:41:26",
    }
    valores.update(alteracoes)
    return valores


class TestFuncoesDePreparacao(unittest.TestCase):
    def test_categoria_vazia_pontuacao_digitos_e_acentos(self):
        self.assertEqual(_limpar_categoria("  ACESSÓRIO!!_42  "), "acessório")
        self.assertEqual(_limpar_categoria("  !!!  "), "sem categoria")
        self.assertEqual(_limpar_categoria(""), "sem categoria")

        dados = preparar_dados(pd.DataFrame([linha(categoria="  !!!  ")]))
        self.assertTrue(bool(dados.loc[0, "categoria_vazia"]) is False)
        self.assertEqual(dados.loc[0, "categoria_limpa"], "sem categoria")

        dados = preparar_dados(pd.DataFrame([linha(categoria="   ")]))
        self.assertTrue(dados.loc[0, "categoria_vazia"])

    def test_canais_conhecidos_e_desconhecido(self):
        self.assertEqual(normalizar_canal(" web "), "Web")
        self.assertEqual(normalizar_canal("LOJA FÍSICA"), "Loja física")
        self.assertEqual(normalizar_canal("mercado"), "Mercado")
        self.assertEqual(normalizar_canal("aplicativo"), "Não reconhecido")

        dados = preparar_dados(pd.DataFrame([
            linha(canal_venda=" WEB "),
            linha(canal_venda="???"),
        ]))
        self.assertEqual(dados["canal_normalizado"].tolist(), ["Web", "Não reconhecido"])
        self.assertEqual(dados["canal_reconhecido"].tolist(), [True, False])

    def test_datas_validas_vazias_impossiveis_e_componentes(self):
        data = _converter_data("2024-10-29 18:41:26")
        self.assertEqual(data.strftime("%d/%m/%Y %H:%M:%S"), "29/10/2024 18:41:26")
        self.assertIsNone(_converter_data(""))
        self.assertIsNone(_converter_data("2024-02-30 10:00:00"))

        dados = preparar_dados(pd.DataFrame([
            linha(data_venda="2024-10-29 18:41:26"),
            linha(data_venda=""),
            linha(data_venda="2024-02-30 10:00:00"),
        ]))
        self.assertEqual(dados["data_venda_invalida"].tolist(), [False, True, True])
        self.assertEqual(dados.loc[0, ["ano", "mes", "dia", "hora"]].astype(int).tolist(), [2024, 10, 29, 18])
        self.assertEqual(dados.loc[0, "data_venda_br"], "29/10/2024 18:41:26")
        self.assertTrue(pd.isna(dados.loc[1, "ano"]))

    def test_quantidade_precisa_ser_inteiro_positivo(self):
        dados = preparar_dados(pd.DataFrame([
            linha(quantidade="1"),
            linha(quantidade="0"),
            linha(quantidade="-2"),
            linha(quantidade="1.5"),
            linha(quantidade="abc"),
        ]))
        self.assertEqual(dados["quantidade_invalida"].tolist(), [False, True, True, True, True])

    def test_preco_zero_e_valido_e_negativo_ou_ausente_nao(self):
        dados = preparar_dados(pd.DataFrame([
            linha(preco_unitario="0"),
            linha(preco_unitario="-0.01"),
            linha(preco_unitario=""),
            linha(preco_unitario="texto"),
        ]))
        self.assertEqual(dados["preco_invalido"].tolist(), [False, True, True, True])

    def test_pedido_com_multiplos_erros_e_contado_uma_vez(self):
        dados = preparar_dados(pd.DataFrame([
            linha(),
            linha(quantidade="0", preco_unitario="texto", data_venda=""),
            linha(quantidade="abc"),
        ]))
        self.assertEqual(dados["pedido_com_problema"].tolist(), [False, True, True])
        self.assertEqual(int(dados["pedido_com_problema"].sum()), 2)

    def test_preparacao_nao_altera_dataframe_bruto_nem_csv(self):
        caminho = PASTA / "halloween_vendas.csv"
        hash_antes = hashlib.sha256(caminho.read_bytes()).hexdigest()
        bruto = carregar_dados(caminho)
        copia = bruto.copy(deep=True)
        preparar_dados(bruto)
        pd.testing.assert_frame_equal(bruto, copia)
        hash_depois = hashlib.sha256(caminho.read_bytes()).hexdigest()
        self.assertEqual(hash_antes, hash_depois)

    def test_resumo_de_problemas_na_base_real(self):
        bruto = carregar_dados(PASTA / "halloween_vendas.csv")
        dados = preparar_dados(bruto)
        self.assertEqual(len(bruto), 1500)
        self.assertEqual(int(dados["quantidade_invalida"].sum()), 7)
        self.assertEqual(int(dados["preco_invalido"].sum()), 12)
        self.assertEqual(int(dados["data_venda_invalida"].sum()), 4)
        self.assertEqual(int(dados["pedido_com_problema"].sum()), 23)

    def test_resumo_de_qualidade_na_base_real(self):
        bruto = carregar_dados(PASTA / "halloween_vendas.csv")
        resumo = resumir_qualidade(preparar_dados(bruto))

        self.assertEqual(resumo["total_pedidos"], 1500)
        self.assertEqual(resumo["categorias_vazias_preenchidas"], 18)
        self.assertEqual(resumo["categorias_nao_vazias_alteradas"], 1482)
        self.assertEqual(resumo["categorias_alteradas_apenas_caixa"], 1351)
        self.assertEqual(resumo["categorias_alteradas_espacos_pontuacao"], 131)
        self.assertEqual(resumo["canais_alterados"], 45)
        self.assertEqual(resumo["quantidade_invalidos"], 7)
        self.assertEqual(resumo["preco_unitario_invalidos"], 12)
        self.assertEqual(resumo["custo_unitario_invalidos"], 7)
        self.assertEqual(resumo["datas_venda_invalidas"], 4)
        self.assertEqual(resumo["pedidos_com_problema_numerico_obrigatorio"], 19)
        self.assertEqual(resumo["pedidos_com_problema_core"], 23)

    def test_resumo_de_qualidade_usa_ou_no_core_sem_mutar_dataframe(self):
        bruto = pd.DataFrame([
            linha(quantidade="0", preco_unitario="texto", custo_unitario=""),
            linha(pedido_id="2", custo_unitario="texto"),
        ])
        copia = bruto.copy(deep=True)
        dados = preparar_dados(bruto)
        copia_dados = dados.copy(deep=True)

        resumo = resumir_qualidade(dados)

        self.assertEqual(resumo["quantidade_invalidos"], 1)
        self.assertEqual(resumo["preco_unitario_invalidos"], 1)
        self.assertEqual(resumo["custo_unitario_invalidos"], 2)
        self.assertEqual(resumo["pedidos_com_problema_numerico_obrigatorio"], 1)
        self.assertEqual(resumo["pedidos_com_problema_core"], 1)
        pd.testing.assert_frame_equal(bruto, copia)
        pd.testing.assert_frame_equal(dados, copia_dados)

    def test_resumo_de_qualidade_distingue_categoria_vazia_caixa_e_pontuacao(self):
        dados = preparar_dados(pd.DataFrame([
            linha(categoria="   "),
            linha(pedido_id="2", categoria="!!!"),
            linha(pedido_id="3", categoria="FANTASIA"),
            linha(pedido_id="4", categoria="  ACESSORIO!!!  ", canal_venda=" WEB "),
            linha(pedido_id="5", categoria="fantasia", canal_venda="???"),
        ]))

        resumo = resumir_qualidade(dados)

        self.assertEqual(resumo["categorias_vazias_preenchidas"], 1)
        self.assertEqual(resumo["categorias_nao_vazias_alteradas"], 3)
        self.assertEqual(resumo["categorias_alteradas_apenas_caixa"], 1)
        self.assertEqual(resumo["categorias_alteradas_espacos_pontuacao"], 2)
        self.assertEqual(resumo["canais_alterados"], 1)
        self.assertEqual(resumo["canais_nao_reconhecidos"], 1)

    def test_investigacao_de_entregas_na_base_real(self):
        tratados = preparar_dados(carregar_dados(PASTA / "halloween_vendas.csv"))

        resultado = investigar_entregas(tratados)

        self.assertEqual(resultado["total_cancelados"], 109)
        self.assertEqual(resultado["sem_entrega_total"], 143)
        self.assertEqual(resultado["sem_entrega_cancelados"], 109)
        self.assertEqual(resultado["sem_entrega_outros_status"], 34)
        self.assertIs(resultado["hipotese_confirmada"], False)
        self.assertEqual(len(resultado["exemplos"]), 3)
        self.assertEqual(
            set(resultado["exemplos"][0]),
            {"pedido_id", "status_pedido", "data_venda", "data_entrega"},
        )

    def test_investigacao_de_entregas_distingue_status_e_preserva_dados(self):
        tratados = preparar_dados(pd.DataFrame([
            linha(pedido_id="1", status_pedido="Concluído", data_entrega="   "),
            linha(pedido_id="2", status_pedido="Devolvido", data_entrega=""),
            linha(pedido_id="3", status_pedido="Em análise", data_entrega=""),
            linha(pedido_id="4", status_pedido="Cancelado", data_entrega="2024-11-03 18:41:26"),
            linha(pedido_id="5", status_pedido="Cancelado", data_entrega=""),
        ]))
        copia = tratados.copy(deep=True)

        resultado = investigar_entregas(tratados)

        self.assertEqual(resultado["total_cancelados"], 2)
        self.assertEqual(resultado["sem_entrega_total"], 4)
        self.assertEqual(resultado["sem_entrega_cancelados"], 1)
        self.assertEqual(resultado["sem_entrega_outros_status"], 3)
        self.assertIs(resultado["hipotese_confirmada"], False)
        self.assertEqual(len(resultado["exemplos"]), 3)
        self.assertEqual(
            [exemplo["pedido_id"] for exemplo in resultado["exemplos"]],
            ["1", "2", "3"],
        )
        self.assertEqual(
            set(resultado["exemplos"][0]),
            {"pedido_id", "status_pedido", "data_venda", "data_entrega"},
        )
        self.assertEqual(resultado["exemplos"][0]["data_entrega"], "   ")
        pd.testing.assert_frame_equal(tratados, copia)

    def test_investigacao_de_entregas_confirma_ou_nao_avalia_sem_casos(self):
        cenarios = [
            (
                pd.DataFrame([linha(status_pedido="Cancelado", data_entrega="")]),
                True,
            ),
            (
                pd.DataFrame([linha(status_pedido="Concluído", data_entrega="2024-11-03 18:41:26")]),
                None,
            ),
        ]

        for bruto, hipotese_esperada in cenarios:
            with self.subTest(hipotese=hipotese_esperada):
                resultado = investigar_entregas(preparar_dados(bruto))
                self.assertIs(resultado["hipotese_confirmada"], hipotese_esperada)
                self.assertEqual(resultado["exemplos"], [])

    def test_resumo_de_pedidos_na_base_real(self):
        tratados = preparar_dados(carregar_dados(PASTA / "halloween_vendas.csv"))

        resumo = resumir_pedidos(tratados)

        self.assertEqual(
            resumo["pedidos_por_canal"].set_index("canal_normalizado")["pedidos"].to_dict(),
            {"Web": 666, "Loja física": 551, "Mercado": 283},
        )
        mensal = resumo["pedidos_por_ano_mes"].set_index("ano_mes")["pedidos"]
        self.assertEqual(len(mensal), 8)
        self.assertEqual(int(mensal.sum()), 1496)
        self.assertEqual(int(mensal.loc["2024-10"]), 393)
        self.assertEqual(int(mensal.loc["2025-10"]), 410)
        self.assertEqual(resumo["excluidos_canal"], 0)
        self.assertEqual(resumo["excluidos_data"], 4)

    def test_resumo_de_pedidos_conta_pedidos_e_exclui_canal_e_data_independentemente(self):
        tratados = preparar_dados(pd.DataFrame([
            linha(pedido_id="1", status_pedido="Cancelado", quantidade="0", preco_unitario="texto"),
            linha(
                pedido_id="2",
                data_venda="2025-01-12 08:00:00",
                canal_venda="Loja física",
                status_pedido="Devolvido",
                quantidade="abc",
                preco_unitario="-1",
            ),
            linha(pedido_id="3", data_venda="2025-02-12 08:00:00", canal_venda="Aplicativo"),
            linha(pedido_id="4", canal_venda="Web", data_venda=""),
            linha(pedido_id="5", canal_venda="???", data_venda="2025-02-30 08:00:00"),
            linha(pedido_id="6", data_venda="2025-10-12 08:00:00", canal_venda="Mercado"),
        ]))
        copia = tratados.copy(deep=True)

        resumo = resumir_pedidos(tratados)

        canais = resumo["pedidos_por_canal"]
        meses = resumo["pedidos_por_ano_mes"]
        self.assertEqual(list(canais.columns), ["canal_normalizado", "pedidos"])
        self.assertEqual(list(meses.columns), ["ano_mes", "pedidos"])
        self.assertEqual(
            canais.set_index("canal_normalizado")["pedidos"].to_dict(),
            {"Web": 2, "Loja física": 1, "Mercado": 1},
        )
        self.assertEqual(
            meses.set_index("ano_mes")["pedidos"].to_dict(),
            {"2024-10": 1, "2025-01": 1, "2025-02": 1, "2025-10": 1},
        )
        self.assertEqual(resumo["excluidos_canal"], 2)
        self.assertEqual(resumo["excluidos_data"], 2)
        pd.testing.assert_frame_equal(tratados, copia)

    def test_resumo_de_pedidos_vazio_e_todos_invalidos_tem_schemas_e_contagens_zero(self):
        tratados_base = preparar_dados(pd.DataFrame([linha()]))
        cenarios = [
            ("vazio", tratados_base.iloc[0:0].copy(), 0, 0),
            (
                "todos inválidos",
                preparar_dados(pd.DataFrame([
                    linha(pedido_id="1", canal_venda="???", data_venda=""),
                    linha(pedido_id="2", canal_venda="Aplicativo", data_venda="2024-02-30 10:00:00"),
                ])),
                2,
                2,
            ),
        ]

        for nome, tratados, excluidos_canal, excluidos_data in cenarios:
            with self.subTest(cenario=nome):
                resumo = resumir_pedidos(tratados)
                self.assertEqual(
                    list(resumo["pedidos_por_canal"].columns),
                    ["canal_normalizado", "pedidos"],
                )
                self.assertEqual(
                    list(resumo["pedidos_por_ano_mes"].columns),
                    ["ano_mes", "pedidos"],
                )
                self.assertTrue(resumo["pedidos_por_canal"].empty)
                self.assertTrue(resumo["pedidos_por_ano_mes"].empty)
                self.assertEqual(resumo["excluidos_canal"], excluidos_canal)
                self.assertEqual(resumo["excluidos_data"], excluidos_data)

    def test_exportacao_base_real_gera_arquivos_com_conteudo_e_textos_originais(self):
        caminho_origem = PASTA / "halloween_vendas.csv"
        hash_origem = hashlib.sha256(caminho_origem.read_bytes()).hexdigest()
        bruto = carregar_dados(caminho_origem)
        tratados = preparar_dados(bruto)
        qualidade = resumir_qualidade(tratados)
        entregas = investigar_entregas(tratados)
        pedidos = resumir_pedidos(tratados)

        with tempfile.TemporaryDirectory() as pasta_temporaria:
            destino = Path(pasta_temporaria)
            self.assertIsNone(
                exportar_resultados(tratados, qualidade, entregas, pedidos, destino)
            )

            esperados = {
                "dados_processados_com_indicadores.csv",
                "pedidos_por_canal.csv",
                "pedidos_por_ano_mes.csv",
                "exemplos_sem_data_entrega.csv",
                "resumo_analise.json",
                "resumo_analise.md",
            }
            self.assertEqual({arquivo.name for arquivo in destino.iterdir()}, esperados)

            dados_exportados = pd.read_csv(
                destino / "dados_processados_com_indicadores.csv",
                dtype=str,
                keep_default_na=False,
            )
            self.assertEqual(dados_exportados.shape, (1500, 44))
            for coluna in bruto.columns:
                self.assertEqual(dados_exportados[coluna].tolist(), bruto[coluna].tolist())

            canais_exportados = pd.read_csv(destino / "pedidos_por_canal.csv")
            meses_exportados = pd.read_csv(destino / "pedidos_por_ano_mes.csv")
            self.assertEqual(int(canais_exportados["pedidos"].sum()), 1500)
            self.assertEqual(int(meses_exportados["pedidos"].sum()), 1496)
            exemplos_exportados = pd.read_csv(
                destino / "exemplos_sem_data_entrega.csv",
                dtype=str,
                keep_default_na=False,
            )
            self.assertEqual(
                list(exemplos_exportados.columns),
                ["pedido_id", "status_pedido", "data_venda", "data_entrega"],
            )
            self.assertEqual(len(exemplos_exportados), 3)

            with (destino / "resumo_analise.json").open(encoding="utf-8") as arquivo:
                resumo_json = json.load(arquivo)
            self.assertEqual(resumo_json["qualidade"], qualidade)
            self.assertEqual(resumo_json["entregas"], entregas)
            self.assertEqual(
                resumo_json["pedidos"]["pedidos_por_canal"],
                pedidos["pedidos_por_canal"].to_dict(orient="records"),
            )
            self.assertEqual(
                resumo_json["pedidos"]["pedidos_por_ano_mes"],
                pedidos["pedidos_por_ano_mes"].to_dict(orient="records"),
            )
            self.assertEqual(resumo_json["pedidos"]["excluidos_canal"], pedidos["excluidos_canal"])
            self.assertEqual(resumo_json["pedidos"]["excluidos_data"], pedidos["excluidos_data"])
            self.assertTrue((destino / "resumo_analise.md").read_text(encoding="utf-8").strip())

        self.assertEqual(hashlib.sha256(caminho_origem.read_bytes()).hexdigest(), hash_origem)

    def test_exportacao_e_deterministica_e_nao_muta_entradas(self):
        caminho_origem = PASTA / "halloween_vendas.csv"
        hash_origem = hashlib.sha256(caminho_origem.read_bytes()).hexdigest()
        bruto = carregar_dados(caminho_origem)
        tratados = preparar_dados(bruto)
        qualidade = resumir_qualidade(tratados)
        entregas = investigar_entregas(tratados)
        pedidos = resumir_pedidos(tratados)
        bruto_antes = bruto.copy(deep=True)
        tratados_antes = tratados.copy(deep=True)
        qualidade_antes = dict(qualidade)
        entregas_antes = json.loads(json.dumps(entregas, ensure_ascii=False))
        canais_antes = pedidos["pedidos_por_canal"].copy(deep=True)
        meses_antes = pedidos["pedidos_por_ano_mes"].copy(deep=True)
        pedidos_scalars_antes = (pedidos["excluidos_canal"], pedidos["excluidos_data"])

        with tempfile.TemporaryDirectory() as primeira, tempfile.TemporaryDirectory() as segunda:
            exportar_resultados(tratados, qualidade, entregas, pedidos, primeira)
            exportar_resultados(tratados, qualidade, entregas, pedidos, segunda)
            hashes_primeira = {
                arquivo.name: hashlib.sha256(arquivo.read_bytes()).hexdigest()
                for arquivo in Path(primeira).iterdir()
            }
            hashes_segunda = {
                arquivo.name: hashlib.sha256(arquivo.read_bytes()).hexdigest()
                for arquivo in Path(segunda).iterdir()
            }

        self.assertEqual(hashes_primeira, hashes_segunda)
        pd.testing.assert_frame_equal(bruto, bruto_antes)
        pd.testing.assert_frame_equal(tratados, tratados_antes)
        self.assertEqual(qualidade, qualidade_antes)
        self.assertEqual(entregas, entregas_antes)
        pd.testing.assert_frame_equal(pedidos["pedidos_por_canal"], canais_antes)
        pd.testing.assert_frame_equal(pedidos["pedidos_por_ano_mes"], meses_antes)
        self.assertEqual(
            (pedidos["excluidos_canal"], pedidos["excluidos_data"]),
            pedidos_scalars_antes,
        )
        self.assertEqual(hashlib.sha256(caminho_origem.read_bytes()).hexdigest(), hash_origem)

    def test_exportacao_sem_exemplos_e_entrada_vazia_preserva_schemas(self):
        cenarios = [
            (
                "hipótese verdadeira",
                pd.DataFrame([linha(status_pedido="Cancelado", data_entrega="")]),
                True,
            ),
            (
                "hipótese indeterminada",
                pd.DataFrame([linha(status_pedido="Concluído")]),
                None,
            ),
            ("entrada vazia", pd.DataFrame(columns=list(linha())), None),
        ]

        for nome, bruto, hipotese_esperada in cenarios:
            with self.subTest(cenario=nome), tempfile.TemporaryDirectory() as pasta_temporaria:
                tratados = preparar_dados(bruto)
                qualidade = resumir_qualidade(tratados)
                entregas = investigar_entregas(tratados)
                pedidos = resumir_pedidos(tratados)
                destino = Path(pasta_temporaria)
                exportar_resultados(tratados, qualidade, entregas, pedidos, destino)

                exemplos = pd.read_csv(
                    destino / "exemplos_sem_data_entrega.csv",
                    dtype=str,
                    keep_default_na=False,
                )
                self.assertEqual(
                    list(exemplos.columns),
                    ["pedido_id", "status_pedido", "data_venda", "data_entrega"],
                )
                self.assertTrue(exemplos.empty)
                with (destino / "resumo_analise.json").open(encoding="utf-8") as arquivo:
                    resumo_json = json.load(arquivo)
                self.assertIs(resumo_json["entregas"]["hipotese_confirmada"], hipotese_esperada)
                self.assertEqual(resumo_json["entregas"]["exemplos"], [])
                self.assertEqual(
                    resumo_json["pedidos"]["pedidos_por_canal"],
                    pedidos["pedidos_por_canal"].to_dict(orient="records"),
                )
                self.assertEqual(
                    resumo_json["pedidos"]["pedidos_por_ano_mes"],
                    pedidos["pedidos_por_ano_mes"].to_dict(orient="records"),
                )
                self.assertTrue((destino / "resumo_analise.md").is_file())


if __name__ == "__main__":
    unittest.main()
