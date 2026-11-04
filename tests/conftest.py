"""Fixtures comuns aos testes de acesso remoto."""

from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from cecilia.remote.auth import KeyStore
from cecilia.remote.layout import ServerLayout
from cecilia.remote.publish import publish
from cecilia.remote.server import create_app
from cecilia.remote.settings import Settings

PEPPER = "p" * 48


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


@pytest.fixture
def servidor_remoto(layout, gravar_parquet, tmp_path):
    """Servidor real (via ASGI) com um dataset publicado e uma chave válida."""
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1, 2, 3])
    resultado = publish(layout, origem, "gaia_teste", "v1")
    chave = KeyStore(layout, PEPPER).create("luan", 90)
    app = create_app(
        Settings(
            layout=layout,
            pepper=PEPPER,
            catalog_per_minute=1000,
            blob_per_minute=1000,
            global_per_minute=1000,
        )
    )
    arquivo = resultado.manifest.files[0]
    return SimpleNamespace(
        app=app,
        layout=layout,
        resultado=resultado,
        chave=chave,
        token=chave.token,
        base_url="http://test",
        blob=arquivo.blob,
        size=arquivo.bytes,
    )
