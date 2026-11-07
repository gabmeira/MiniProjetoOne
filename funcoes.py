import re
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
