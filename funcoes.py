import re
from pathlib import Path

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
    texto = re.sub(r"[ˆ\w\s]|[_\d]", "", texto, flags=re.UNICODE)
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