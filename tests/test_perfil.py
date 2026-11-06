"""Testes do perfil de colunas com dados sintéticos."""

import math

import pandas as pd

from cecilia.limpeza.perfil import perfil_colunas, perfil_serie


def _df():
    return pd.DataFrame({
        "ids": pd.array([1234567890123456789, None, 3, 4], dtype="Int64"),
        "x": [1.0, 2.0, None, 4.0],
        "classe": ["G2", "K5", "G2", None],
        "flag": [True, False, True, True],
    })


def test_uma_linha_por_coluna_na_ordem():
    p = perfil_colunas(_df())
    assert list(p["coluna"]) == ["ids", "x", "classe", "flag"]


def test_contagem_de_ausentes():
    p = perfil_colunas(_df()).set_index("coluna")
    assert p.loc["ids", "n_ausentes"] == 1
    assert p.loc["x", "n_ausentes"] == 1
    assert p.loc["classe", "n_ausentes"] == 1
    assert p.loc["flag", "n_ausentes"] == 0
    assert math.isclose(p.loc["x", "frac_ausentes"], 0.25)


def test_faixa_numerica_ignora_nulos():
    linha = perfil_serie(_df()["x"])
    assert linha["min"] == 1.0 and linha["max"] == 4.0
    assert linha["p50"] == 2.0
    assert linha["top"] is None


def test_int64_nao_vira_float_no_dataframe():
    df = _df()
    perfil_colunas(df)
    assert str(df["ids"].dtype) == "Int64"
    assert perfil_serie(df["ids"])["tipo"] == "Int64"


def test_texto_e_bool_tem_top_e_sem_faixa():
    classe = perfil_serie(_df()["classe"])
    assert classe["top"].startswith("G2=2")
    assert classe["min"] is None
    flag = perfil_serie(_df()["flag"])
    assert flag["top"].startswith("True=3")
    assert flag["n_distintos"] == 2


def test_coluna_toda_nula():
    linha = perfil_serie(pd.Series([None, None], dtype="Float64", name="v"))
    assert linha["n_ausentes"] == 2
    assert linha["min"] is None
