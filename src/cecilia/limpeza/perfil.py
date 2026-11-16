"""Perfil de valores por coluna: tipo, ausentes, faixa e valores mais frequentes.

Funções puras: recebem um DataFrame (ou uma Series) e devolvem outro, sem ler disco.
Para tabelas grandes, o script chama `perfil_serie` coluna a coluna.
"""

from __future__ import annotations

import pandas as pd

PERCENTIS = {"p01": 0.01, "p50": 0.50, "p99": 0.99}
N_TOP = 5


def _e_numerica(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)


def perfil_serie(s: pd.Series) -> dict:
    """Resumo de uma coluna. Numéricas: min, p01, p50, p99, max. Demais: top valores."""
    n = len(s)
    n_ausentes = int(s.isna().sum())
    linha = {
        "coluna": s.name,
        "tipo": str(s.dtype),
        "n": n,
        "n_ausentes": n_ausentes,
        "frac_ausentes": n_ausentes / n if n else float("nan"),
        "n_distintos": int(s.nunique(dropna=True)),
        "min": None,
        "p01": None,
        "p50": None,
        "p99": None,
        "max": None,
        "top": None,
    }
    valores = s.dropna()
    if _e_numerica(s):
        if len(valores):
            # float para não estourar Int64 em quantile e para o CSV ficar uniforme
            v = valores.astype("float64")
            linha["min"], linha["max"] = float(v.min()), float(v.max())
            for nome, q in PERCENTIS.items():
                linha[nome] = float(v.quantile(q))
    else:
        contagem = valores.astype(str).value_counts().head(N_TOP)
        linha["top"] = "; ".join(f"{k}={v}" for k, v in contagem.items())
    return linha


def perfil_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por coluna do DataFrame, na ordem das colunas."""
    return pd.DataFrame([perfil_serie(df[c]) for c in df.columns])
