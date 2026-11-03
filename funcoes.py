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