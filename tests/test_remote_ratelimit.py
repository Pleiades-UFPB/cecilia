"""Testes dos limites em memória e do índice de blobs."""

import asyncio

from cecilia.remote.index import BlobIndex
from cecilia.remote.publish import publish
from cecilia.remote.ratelimit import KeyConcurrency, SlidingWindow


def test_janela_deslizante():
    async def cenario():
        janela = SlidingWindow(2)
        assert await janela.allow("a")
        assert await janela.allow("a")
        assert not await janela.allow("a")
        assert await janela.allow("b")

    asyncio.run(cenario())


def test_concorrencia_por_chave():
    async def cenario():
        limite = KeyConcurrency(1)
        assert await limite.acquire("a")
        assert not await limite.acquire("a")
        assert await limite.acquire("b")
        await limite.release("a")
        assert await limite.acquire("a")

    asyncio.run(cenario())


def test_index_resolve_blob(layout, gravar_parquet, tmp_path):
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1, 2])
    resultado = publish(layout, origem, "gaia_teste", "v1")
    blob = resultado.manifest.files[0].blob

    index = BlobIndex(layout, max_age_seconds=0)
    referencias = index.lookup(blob)
    assert referencias[0].dataset == "gaia_teste"
    assert referencias[0].version == "v1"
    assert referencias[0].path == "gaia.parquet"
    assert index.lookup("c" * 64) == ()
