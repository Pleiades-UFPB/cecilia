"""Fixtures comuns aos testes de acesso remoto."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from cecilia.remote.layout import ServerLayout


@pytest.fixture
def gravar_parquet():
    """Devolve uma função que grava um Parquet sintético com duas colunas."""

    def _gravar(path: Path, ids: list[int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tabela = pa.table(
            {
                "source_id": pa.array(ids, type=pa.int64()),
                "ra": pa.array([float(item) for item in ids], type=pa.float64()),
            }
        )
        pq.write_table(tabela, path)

    return _gravar


@pytest.fixture
def layout(tmp_path: Path) -> ServerLayout:
    """Raiz de servidor isolada por teste."""
    return ServerLayout(tmp_path / "srv")
