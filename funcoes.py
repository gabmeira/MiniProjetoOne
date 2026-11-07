import re
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

def carregar_dados(caminho):
    """Lê o CSV como texto e mantém campos vazios como strings vazias."""
    return pd.read_csv(
        Path(caminho),
        sep=",",
        encoding="utf-8",
        dtype=str,
        keep_default_na=False,
    )

def _limpar_categoria(valor):
    """Padroniza categoria e explicita valores ausentes."""
    texto = valor.strip().lower()
    texto = re.sub(r"[^\w\s]|[_\d]", "", texto, flags=re.UNICODE)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto or "sem categoria"

def normalizar_canal(valor):
    """Normaliza os três canais conhecidos."""
    chave = valor.strip().casefold()
    canais = {
        "mercado": "Mercado",
        "loja física": "Loja física",
        "web": "Web",
    }
    return canais.get(chave, "Não reconhecido")

def _converter_data(texto):
    """Converte uma data no formato ISO esperado; vazio ou inválido retorna None."""
    if not texto.strip():
        return None
    try:
        data = datetime.strptime(texto.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return data

def preparar_dados(dados):
    tratados = dados.copy(deep=True)
    categoria_vazia = tratados["categoria"].str.strip().eq("")
    tratados["categoria_limpa"] = tratados["categoria"].map(_limpar_categoria)
    tratados["categoria_vazia"] = categoria_vazia
    canal_chave = tratados["canal_venda"].str.strip().str.casefold()
    mapa_canais = {"mercado": "Mercado", "loja física": "Loja física", "web": "Web"}
    tratados["canal_normalizado"] = canal_chave.map(mapa_canais).fillna("Não reconhecido")
    tratados["canal_reconhecido"] = tratados["canal_normalizado"].ne("Não reconhecido")

    for coluna in ("quantidade", "preco_unitario", "custo_unitario", "desconto_pct"):
        tratados[f"{coluna}_numero"] = pd.to_numeric(tratados[coluna], errors="coerce")
        tratados[f"{coluna}_ausente"] = tratados[coluna].str.strip().eq("")
        tratados[f"{coluna}_nao_numerico"] = (
            tratados[f"{coluna}_numero"].isna() & ~tratados[f"{coluna}_ausente"]
        )

    quantidade = tratados["quantidade_numero"]
    tratados["quantidade_invalida"] = (
        quantidade.isna() | quantidade.le(0) | quantidade.mod(1).ne(0)
    )
    preco = tratados["preco_unitario_numero"]
    tratados["preco_invalido"] = (
        tratados["preco_unitario_ausente"] | tratados["preco_unitario_nao_numerico"] | preco.lt(0)
    )
    custo = tratados["custo_unitario_numero"]
    tratados["custo_invalido"] = (
        tratados["custo_unitario_ausente"] | tratados["custo_unitario_nao_numerico"] | custo.lt(0)
    )
    desconto = tratados["desconto_pct_numero"]
    tratados["desconto_invalido"] = (
        tratados["desconto_pct_ausente"] | tratados["desconto_pct_nao_numerico"] | desconto.lt(0) | desconto.gt(100)
    )

    datas = tratados["data_venda"].map(_converter_data)
    tratados["data_venda_convertida"] = pd.to_datetime(datas)
    tratados["data_venda_invalida"] = tratados["data_venda_convertida"].isna()
    for nome, componente in [("ano", "year"), ("mes", "month"), ("dia", "day"), ("hora", "hour")]:
        tratados[nome] = getattr(tratados["data_venda_convertida"].dt, componente).astype("Int64")
    tratados["data_venda_br"] = [
        valor.strftime("%d/%m/%Y %H:%M:%S") if pd.notna(valor) else ""
        for valor in datas
    ]
    tratados["ano_mes"] = tratados["data_venda_convertida"].dt.strftime("%Y-%m")
    tratados["data_entrega_ausente"] = tratados["data_entrega"].str.strip().eq("")

    problemas = np.column_stack([
        tratados["quantidade_invalida"].to_numpy(dtype=bool),
        tratados["preco_invalido"].to_numpy(dtype=bool),
        tratados["data_venda_invalida"].to_numpy(dtype=bool),
    ])
    # Cada linha é um pedido; axis=1 combina as três verificações da mesma linha.
    # any(axis=1) marca o pedido se ao menos uma dessas verificações for verdadeira.
    tratados["pedido_com_problema"] = np.where(problemas.any(axis=1), True, False)
    return tratados


def resumir_qualidade(tratados) -> dict:
    """Resume contagens sem alterar o DataFrame preparado.

    O total de pedidos com problema considera somente quantidade, preço e data
    de venda. Ajustes de categoria/canal e problemas complementares de custo/
    desconto aparecem em contagens próprias e não entram nesse total.
    """
    resumo = {
        "total_pedidos": int(len(tratados)),
        "categorias_vazias_preenchidas": int(tratados["categoria_vazia"].sum()),
    }

    categoria_nao_vazia = ~tratados["categoria_vazia"]
    categoria_alterada = categoria_nao_vazia & tratados["categoria"].ne(tratados["categoria_limpa"])
    apenas_caixa = tratados["categoria"].str.casefold().eq(
        tratados["categoria_limpa"].str.casefold()
    )
    resumo["categorias_nao_vazias_alteradas"] = int(categoria_alterada.sum())
    resumo["categorias_alteradas_apenas_caixa"] = int((categoria_alterada & apenas_caixa).sum())
    resumo["categorias_alteradas_espacos_pontuacao"] = int(
        (categoria_alterada & ~apenas_caixa).sum()
    )

    canal_alterado = tratados["canal_reconhecido"] & tratados["canal_venda"].ne(
        tratados["canal_normalizado"]
    )
    resumo["canais_alterados"] = int(canal_alterado.sum())
    resumo["canais_nao_reconhecidos"] = int((~tratados["canal_reconhecido"]).sum())

    for coluna in ("quantidade", "preco_unitario", "custo_unitario", "desconto_pct"):
        resumo[f"{coluna}_ausentes"] = int(tratados[f"{coluna}_ausente"].sum())
        resumo[f"{coluna}_nao_numericos"] = int(tratados[f"{coluna}_nao_numerico"].sum())
        flag_invalido = {
            "quantidade": "quantidade_invalida",
            "preco_unitario": "preco_invalido",
            "custo_unitario": "custo_invalido",
            "desconto_pct": "desconto_invalido",
        }[coluna]
        resumo[f"{coluna}_invalidos"] = int(tratados[flag_invalido].sum())

    resumo["datas_venda_invalidas"] = int(tratados["data_venda_invalida"].sum())
    problema_numerico_obrigatorio = tratados["quantidade_invalida"] | tratados["preco_invalido"]
    resumo["pedidos_com_problema_numerico_obrigatorio"] = int(problema_numerico_obrigatorio.sum())
    resumo["pedidos_com_problema_core"] = int(tratados["pedido_com_problema"].sum())
    return resumo


def investigar_entregas(tratados) -> dict:
    """Avalia se pedidos sem entrega estão associados ao status Cancelado.

    A análise usa a coluna ``data_entrega_ausente`` criada na preparação e não
    altera o DataFrame. Qualquer status diferente de ``Cancelado`` conta como
    contraexemplo quando a data de entrega está ausente.
    """
    cancelados = tratados["status_pedido"].eq("Cancelado")
    sem_entrega = tratados["data_entrega_ausente"]
    outros_sem_entrega = sem_entrega & ~cancelados

    total_sem_entrega = int(sem_entrega.sum())
    sem_entrega_cancelados = int((sem_entrega & cancelados).sum())
    sem_entrega_outros_status = int(outros_sem_entrega.sum())
    hipotese_confirmada = (
        None if total_sem_entrega == 0 else sem_entrega_outros_status == 0
    )

    colunas_exemplo = ["pedido_id", "status_pedido", "data_venda", "data_entrega"]
    exemplos = (
        tratados.loc[outros_sem_entrega, colunas_exemplo]
        .head(3)
        .to_dict(orient="records")
    )

    return {
        "total_cancelados": int(cancelados.sum()),
        "sem_entrega_total": total_sem_entrega,
        "sem_entrega_cancelados": sem_entrega_cancelados,
        "sem_entrega_outros_status": sem_entrega_outros_status,
        "hipotese_confirmada": hipotese_confirmada,
        "exemplos": exemplos,
    }


def resumir_pedidos(tratados) -> dict:
    """Resume pedidos por canal reconhecido e por mês com data válida.

    Cada linha representa um pedido. As exclusões são independentes: uma
    data inválida não impede a contagem por canal, e um canal desconhecido
    não impede a contagem por ano/mês.
    """
    por_canal = tratados.loc[tratados["canal_reconhecido"]]
    pedidos_por_canal = (
        por_canal.groupby("canal_normalizado").size()
        .rename("pedidos")
        .reset_index()
        .sort_values(["pedidos", "canal_normalizado"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if pedidos_por_canal.empty:
        pedidos_por_canal = pd.DataFrame(columns=["canal_normalizado", "pedidos"])

    por_data = tratados.loc[~tratados["data_venda_invalida"]]
    pedidos_por_ano_mes = (
        por_data.groupby("ano_mes").size()
        .rename("pedidos")
        .reset_index()
        .sort_values("ano_mes")
        .reset_index(drop=True)
    )
    if pedidos_por_ano_mes.empty:
        pedidos_por_ano_mes = pd.DataFrame(columns=["ano_mes", "pedidos"])

    return {
        "pedidos_por_canal": pedidos_por_canal,
        "pedidos_por_ano_mes": pedidos_por_ano_mes,
        "excluidos_canal": int((~tratados["canal_reconhecido"]).sum()),
        "excluidos_data": int(tratados["data_venda_invalida"].sum()),
    }


def exportar_resultados(tratados, qualidade, entregas, pedidos, pasta_saida) -> None:
    """Exporta os dados preparados e resumos já calculados em arquivos UTF-8."""
    destino = Path(pasta_saida)
    destino.mkdir(parents=True, exist_ok=True)

    tratados.to_csv(
        destino / "dados_processados_com_indicadores.csv",
        index=False,
        encoding="utf-8",
    )

    canal_df = pedidos["pedidos_por_canal"]
    mes_df = pedidos["pedidos_por_ano_mes"]
    canal_registros = canal_df.to_dict(orient="records")
    mes_registros = mes_df.to_dict(orient="records")
    canal_df.to_csv(destino / "pedidos_por_canal.csv", index=False, encoding="utf-8")
    mes_df.to_csv(destino / "pedidos_por_ano_mes.csv", index=False, encoding="utf-8")

    colunas_exemplo = ["pedido_id", "status_pedido", "data_venda", "data_entrega"]
    exemplos = [
        {coluna: registro.get(coluna, "") for coluna in colunas_exemplo}
        for registro in entregas.get("exemplos", [])[:3]
    ]
    pd.DataFrame(exemplos, columns=colunas_exemplo).to_csv(
        destino / "exemplos_sem_data_entrega.csv", index=False, encoding="utf-8"
    )

    resumo = {
        "qualidade": qualidade,
        "entregas": entregas,
        "pedidos": {
            "pedidos_por_canal": canal_registros,
            "pedidos_por_ano_mes": mes_registros,
            "excluidos_canal": int(pedidos["excluidos_canal"]),
            "excluidos_data": int(pedidos["excluidos_data"]),
        },
    }
    with (destino / "resumo_analise.json").open("w", encoding="utf-8", newline="\n") as arquivo:
        json.dump(resumo, arquivo, ensure_ascii=False, indent=2, allow_nan=False)
        arquivo.write("\n")

    def tabela(registros, colunas):
        linhas = ["| " + " | ".join(colunas) + " |", "| " + " | ".join("---" for _ in colunas) + " |"]
        for registro in registros:
            valores = [str(registro.get(coluna, "")) for coluna in colunas]
            linhas.append("| " + " | ".join(valores) + " |")
        return "\n".join(linhas)

    def quantidade_chave(chave):
        return qualidade.get(chave, 0)

    hipotese = entregas.get("hipotese_confirmada")
    conclusoes = {
        True: "Os dados são compatíveis com a hipótese nesta base, mas isso não prova uma regra geral.",
        False: "A hipótese não se confirma nesta base: há pedidos sem data de entrega com outro status.",
        None: "Não há casos sem data de entrega para avaliar a hipótese.",
    }
    markdown = [
        "# Resumo da análise",
        "",
        "## Qualidade e normalização",
        "",
        f"- Pedidos analisados: {qualidade.get('total_pedidos', 0)}.",
        f"- Categorias vazias preenchidas: {quantidade_chave('categorias_vazias_preenchidas')}; "
        f"categorias não vazias alteradas: {quantidade_chave('categorias_nao_vazias_alteradas')} "
        f"(apenas caixa: {quantidade_chave('categorias_alteradas_apenas_caixa')}; "
        f"espaços/pontuação: {quantidade_chave('categorias_alteradas_espacos_pontuacao')}).",
        f"- Canais alterados: {quantidade_chave('canais_alterados')}; "
        f"não reconhecidos: {quantidade_chave('canais_nao_reconhecidos')}.",
        f"- Problemas numéricos obrigatórios (quantidade ou preço): "
        f"{quantidade_chave('pedidos_com_problema_numerico_obrigatorio')} pedidos.",
        f"- Quantidade inválida: {quantidade_chave('quantidade_invalidos')} pedidos; "
        f"preço unitário inválido: {quantidade_chave('preco_unitario_invalidos')} pedidos "
        f"({quantidade_chave('preco_unitario_ausentes')} ausentes; "
        f"{quantidade_chave('preco_unitario_nao_numericos')} não numéricos).",
        f"- Problemas no conjunto principal (quantidade, preço ou data de venda): "
        f"{quantidade_chave('pedidos_com_problema_core')} pedidos, incluindo "
        f"{quantidade_chave('datas_venda_invalidas')} datas de venda inválidas.",
        "- Campos complementares: "
        f"custo inválido em {quantidade_chave('custo_unitario_invalidos')} pedidos; "
        f"desconto inválido em {quantidade_chave('desconto_pct_invalidos')} pedidos. "
        "Contagens de inválidos já incluem ausentes e não devem ser somadas novamente.",
        "",
        "## Entregas",
        "",
        f"- Pedidos cancelados: {entregas.get('total_cancelados', 0)}.",
        f"- Pedidos sem data de entrega: {entregas.get('sem_entrega_total', 0)}; "
        f"com status Cancelado: {entregas.get('sem_entrega_cancelados', 0)}; "
        f"com outro status: {entregas.get('sem_entrega_outros_status', 0)}.",
        "- Hipótese de que todos os pedidos sem data de entrega são cancelados: "
        f"{conclusoes[hipotese]}",
        "",
        "## Pedidos por canal reconhecido",
        "",
        tabela(canal_registros, list(canal_df.columns)),
        "",
        f"Excluídos por canal não reconhecido: {pedidos['excluidos_canal']}.",
        "",
        "## Pedidos por ano/mês de venda válida",
        "",
        tabela(mes_registros, list(mes_df.columns)),
        "",
        f"Excluídos por data de venda inválida: {pedidos['excluidos_data']}.",
        "",
        "## Limitações",
        "",
        "As contagens representam pedidos registrados de todos os status; não representam unidades vendidas nem receita. "
        "A base é fictícia e as conclusões descrevem somente os registros analisados.",
        "",
    ]
    (destino / "resumo_analise.md").write_text("\n".join(markdown), encoding="utf-8")
