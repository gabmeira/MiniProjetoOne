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
    tratados["pedido_com_problema"] = np.where(problemas.any(axis=1), True, False)
    return tratados
