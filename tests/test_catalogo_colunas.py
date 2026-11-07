"""Testes do catálogo de colunas (AC-3 e AC-4 do plano 03-01)."""

from pathlib import Path

import pyarrow.parquet as pq
import pytest

from cecilia.data_assembly.fetch_raw import AP_COLS
from cecilia.limpeza.catalogo_colunas import (
    GSPPHOT_COLS,
    Categoria,
    catalogo,
    colunas_por_categoria,
    colunas_proibidas,
)

ROOT = Path(__file__).resolve().parents[1]
INTERIM = {
    "A": ROOT / "data" / "interim" / "trailA_lamost_gaia_2mass.parquet",
    "B": ROOT / "data" / "interim" / "trailB_apokasc_gaia_2mass.parquet",
}


@pytest.mark.parametrize("trilho", ["A", "B"])
def test_toda_entrada_tem_categoria_e_justificativa(trilho):
    for coluna, info in catalogo(trilho).items():
        assert isinstance(info.categoria, Categoria), coluna
        assert info.justificativa.strip(), coluna


def test_lista_gspphot_e_a_mesma_da_consulta():
    assert GSPPHOT_COLS == AP_COLS


def test_proibidas_trilho_a_inclui_gspphot_e_rotulo():
    proibidas = colunas_proibidas("A")
    assert set(AP_COLS) <= proibidas
    assert {"lamost_Class", "lamost_subClass"} <= proibidas


def test_proibidas_trilho_b_inclui_rotulo_e_relacoes_de_escala():
    proibidas = colunas_proibidas("B")
    assert {
        "apokasc_EvolSt",
        "apokasc_Mass",
        "apokasc_Radius",
        "apokasc_loggSeis",
        "apokasc_AgeCat",
    } <= proibidas


def test_features_candidatas_nao_sao_proibidas():
    for trilho in "AB":
        assert not set(
            colunas_por_categoria(trilho, Categoria.FEATURE_CANDIDATA)
        ) & colunas_proibidas(trilho)


def test_trilho_invalido():
    with pytest.raises(ValueError):
        catalogo("C")


@pytest.mark.parametrize("trilho", ["A", "B"])
def test_cobertura_contra_esquema_real(trilho):
    """Toda coluna do Parquet está no catálogo e nenhuma do catálogo é inventada."""
    caminho = INTERIM[trilho]
    if not caminho.exists():
        pytest.skip(f"{caminho.name} ausente (CI não tem dados)")
    no_parquet = set(pq.read_schema(caminho).names)
    no_catalogo = set(catalogo(trilho))
    assert no_parquet - no_catalogo == set(), "colunas sem categoria"
    assert no_catalogo - no_parquet == set(), "colunas inexistentes no Parquet"
