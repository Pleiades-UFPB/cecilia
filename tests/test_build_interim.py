"""Testes da colisão de nomes no build_interim (AC-1 do plano 02-01).

O DuckDB não diferencia maiúsculas de minúsculas: num Parquet com gmag e Gmag, b."Gmag"
lê gmag. Os testes usam Parquet sintéticos com valores diferentes em cada coluna do par
para conferir que cada coluna de saída vem da coluna de origem certa.
"""

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from cecilia.data_assembly.build_interim import (
    checar_nomes_unicos,
    nome_saida,
    nomes_duckdb,
    select_list,
    sql_trilho_a,
    sql_trilho_b,
)


def _gaia(tmp_path, ids):
    src = tmp_path / "gsrc.parquet"
    tm = tmp_path / "gtm.parquet"
    pq.write_table(
        pa.table({"source_id": ids, "ra": [1.0] * len(ids), "phot_g_mean_mag": [12.0] * len(ids)}),
        src,
    )
    pq.write_table(pa.table({"source_id": ids, "designation": ["x"] * len(ids)}), tm)
    return src, tm


def test_nomes_duckdb_por_posicao(tmp_path):
    caminho = tmp_path / "t.parquet"
    pq.write_table(pa.table({"gmag": [1.0], "Gmag": [2.0]}), caminho)
    nomes = nomes_duckdb(duckdb.connect(), caminho)
    assert list(nomes) == ["gmag", "Gmag"]
    # o DuckDB dá outro nome à segunda coluna do par
    assert nomes["gmag"] != nomes["Gmag"]


def test_select_list_le_a_coluna_certa(tmp_path):
    caminho = tmp_path / "t.parquet"
    pq.write_table(pa.table({"gmag": [10.0], "Gmag": [20.0]}), caminho)
    con = duckdb.connect()
    itens = select_list("b", nomes_duckdb(con, caminho), "lamost_", renomear={"Gmag": "Gmag_gaia"})
    linha = con.execute(f"SELECT {', '.join(itens)} FROM read_parquet('{caminho}') b").fetchdf()
    assert list(linha.columns) == ["lamost_gmag", "lamost_Gmag_gaia"]
    assert linha.loc[0, "lamost_gmag"] == 10.0
    assert linha.loc[0, "lamost_Gmag_gaia"] == 20.0


def test_nome_saida():
    assert nome_saida('b."e_[Fe/H]" AS "apokasc_e_[Fe/H]"') == "apokasc_e_[Fe/H]"


def test_checar_nomes_unicos_falha_sem_renomeacao():
    with pytest.raises(SystemExit, match="coincidem"):
        checar_nomes_unicos(["lamost_gmag", "lamost_Gmag"])
    checar_nomes_unicos(["lamost_gmag", "lamost_Gmag_gaia"])


def test_trilho_a_sem_colisao(tmp_path):
    lamost = tmp_path / "lamost.parquet"
    pq.write_table(
        pa.table(
            {
                "ObsID": [1, 2],
                "MJD": [100, 100],
                "Class": ["STAR", "STAR"],
                "subClass": ["G2", "K1"],
                "FiberType": ["Obj", "Obj"],
                "snrg": [50.0, 40.0],
                "snri": [60.0, 70.0],
                "gmag": [13.1, 14.1],  # Pan-STARRS g
                "GaiaDR3": [7, 8],
                "Gmag": [12.5, 13.5],  # Gaia G
            }
        ),
        lamost,
    )
    gsrc, gtm = _gaia(tmp_path, [7, 8])
    con = duckdb.connect()
    df = con.execute(sql_trilho_a(con, lamost, gsrc, gtm)).fetchdf().sort_values("source_id")
    assert not [c for c in df.columns if c.endswith("_1")]
    assert df["lamost_gmag"].tolist() == [13.1, 14.1]
    assert df["lamost_Gmag_gaia"].tolist() == [12.5, 13.5]


def test_trilho_b_sem_colisao(tmp_path):
    apo = tmp_path / "apo.parquet"
    pq.write_table(
        pa.table(
            {
                "KIC": [1],
                "AgeRGB": [5.0],
                "E_AgeRGB": [1.5],  # incerteza superior
                "e_AgeRGB": [-0.9],  # incerteza inferior
                "AgeRC": [3.0],
                "E_AgeRC": [0.7],
                "e_AgeRC": [-0.4],
                "GaiaDR3": [7],
            }
        ),
        apo,
    )
    gsrc, gtm = _gaia(tmp_path, [7])
    con = duckdb.connect()
    df = con.execute(sql_trilho_b(con, apo, gsrc, gtm)).fetchdf()
    assert not [c for c in df.columns if c.endswith("_1")]
    assert df.loc[0, "apokasc_E_AgeRGB"] == 1.5
    assert df.loc[0, "apokasc_e_AgeRGB_inf"] == -0.9
    assert df.loc[0, "apokasc_E_AgeRC"] == 0.7
    assert df.loc[0, "apokasc_e_AgeRC_inf"] == -0.4
