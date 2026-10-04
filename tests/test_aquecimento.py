"""Testes do aquecimento da Fase 01 (tabela de estrelas e diagrama HR)."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from cecilia.aquecimento import (
    CAMINHO_TABELA,
    carregar_estrelas,
    magnitude_absoluta,
    plotar_hr,
)

# --- Magnitude absoluta (AC-2) ---


def test_magnitude_absoluta_a_10_pc_igual_a_aparente():
    """ϖ = 100 mas → 10 pc → M = m."""
    assert magnitude_absoluta(3.0, 100.0) == pytest.approx(3.0)


def test_magnitude_absoluta_a_100_pc():
    """ϖ = 10 mas → 100 pc → M = m − 5."""
    assert magnitude_absoluta(3.0, 10.0) == pytest.approx(-2.0)


def test_magnitude_absoluta_aceita_arrays():
    resultado = magnitude_absoluta(np.array([3.0, 3.0]), np.array([100.0, 10.0]))
    np.testing.assert_allclose(resultado, [3.0, -2.0])


@pytest.mark.parametrize("paralaxe", [0.0, -1.5])
def test_magnitude_absoluta_rejeita_paralaxe_nao_positiva(paralaxe):
    with pytest.raises(ValueError):
        magnitude_absoluta(3.0, paralaxe)


# --- Tabela (AC-1) ---


def test_tabela_real_tem_10_estrelas_sem_ausentes():
    df = carregar_estrelas(CAMINHO_TABELA)
    assert len(df) == 10
    assert df.isna().sum().sum() == 0


def test_tabela_sem_coluna_obrigatoria_falha(tmp_path):
    caminho = tmp_path / "incompleta.csv"
    caminho.write_text("nome,V\nVega,0.03\n")
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        carregar_estrelas(caminho)


# --- Diagrama HR (AC-3) ---


@pytest.fixture
def hr(tmp_path):
    """Gera o HR da tabela real num diretório temporário."""
    df = carregar_estrelas(CAMINHO_TABELA)
    df["M_V"] = magnitude_absoluta(df["V"], df["paralaxe_mas"])
    saida = tmp_path / "sub" / "hr.png"
    fig, ax = plotar_hr(df, saida)
    yield df, ax, saida
    plt.close(fig)


def test_hr_salva_arquivo(hr):
    _, _, saida = hr
    assert saida.exists() and saida.stat().st_size > 0


def test_hr_eixo_y_invertido_e_x_crescente(hr):
    _, ax, _ = hr
    assert ax.yaxis_inverted()
    assert not ax.xaxis_inverted()


def test_hr_estrela_quente_a_esquerda_da_fria(hr):
    """A estrela de menor B−V (mais quente) aparece à esquerda da de maior B−V."""
    df, ax, _ = hr
    quente = df.loc[df["B_V"].idxmin()]
    fria = df.loc[df["B_V"].idxmax()]
    x_quente, _ = ax.transData.transform((quente["B_V"], quente["M_V"]))
    x_fria, _ = ax.transData.transform((fria["B_V"], fria["M_V"]))
    assert x_quente < x_fria


def test_hr_eixos_com_unidade(hr):
    _, ax, _ = hr
    assert "(mag)" in ax.get_xlabel()
    assert "(mag)" in ax.get_ylabel()


def test_hr_nomeia_cada_estrela(hr):
    df, ax, _ = hr
    textos = {t.get_text() for t in ax.texts}
    assert set(df["nome"]) <= textos


def test_carregar_estrelas_retorna_dataframe():
    assert isinstance(carregar_estrelas(), pd.DataFrame)
