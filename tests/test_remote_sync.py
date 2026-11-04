"""Testes de sincronização, materialização e verificação local."""

import asyncio
import os
import shutil

import httpx

from cecilia.remote.client import RemoteClient
from cecilia.remote.publish import publish
from cecilia.remote.sync import (
    get_file,
    latest_version,
    manifest_rows,
    sync_dataset,
    verify_data,
)


class CountingTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner: httpx.AsyncBaseTransport):
        self.inner = inner
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return await self.inner.handle_async_request(request)


async def _sync(servidor, data, cache, *, transporte=None, **kwargs):
    transporte = transporte or httpx.ASGITransport(app=servidor.app)
    async with httpx.AsyncClient(
        transport=transporte,
        base_url="http://test",
        headers={"Authorization": f"Bearer {servidor.token}"},
    ) as http:
        cliente = RemoteClient(http, "http://test")
        resultado = await sync_dataset(
            cliente,
            "gaia_teste",
            "v1",
            data_dir=data,
            cache_dir=cache,
            connections=1,
            alias="luan",
            **kwargs,
        )
    return resultado


def test_sync_materializa_com_hardlink(servidor_remoto, tmp_path):
    dados = tmp_path / "data"
    cache = tmp_path / "cache"

    resultado = asyncio.run(_sync(servidor_remoto, dados, cache))

    assert resultado.downloaded == 1
    arquivo = dados / "gaia_teste" / "v1" / "gaia.parquet"
    assert (
        arquivo.read_bytes() == (servidor_remoto.layout.blobs / servidor_remoto.blob).read_bytes()
    )
    assert os.path.samefile(cache / servidor_remoto.blob, arquivo)
    assert (dados / "gaia_teste" / "v1" / ".cecilia.json").is_file()

    linhas = manifest_rows(resultado, "luan", when="2026-11-04")
    assert len(linhas) == 1
    assert "gaia_teste/v1/gaia.parquet" in linhas[0]
    assert "luan" in linhas[0]


def test_segundo_sync_nao_baixa(servidor_remoto, tmp_path):
    dados = tmp_path / "data"
    cache = tmp_path / "cache"
    asyncio.run(_sync(servidor_remoto, dados, cache))

    transporte = CountingTransport(httpx.ASGITransport(app=servidor_remoto.app))
    resultado = asyncio.run(_sync(servidor_remoto, dados, cache, transporte=transporte))

    assert resultado.downloaded == 0
    assert resultado.reused == 1
    assert not [request for request in transporte.requests if "/v1/blobs/" in request.url.path]


def test_verify_ok_e_corrupcao(servidor_remoto, tmp_path):
    dados = tmp_path / "data"
    cache = tmp_path / "cache"
    asyncio.run(_sync(servidor_remoto, dados, cache))
    assert verify_data(dados, cache) == []

    arquivo = dados / "gaia_teste" / "v1" / "gaia.parquet"
    arquivo.write_bytes(b"x" * arquivo.stat().st_size)

    problemas = verify_data(dados, cache)
    assert any(problema.startswith("hash") for problema in problemas)


def test_get_file_com_saida(servidor_remoto, tmp_path):
    dados = tmp_path / "data"
    cache = tmp_path / "cache"
    saida = tmp_path / "saida.parquet"

    async def cenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=servidor_remoto.app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {servidor_remoto.token}"},
        ) as http:
            cliente = RemoteClient(http, "http://test")
            return await get_file(
                cliente,
                "gaia_teste",
                "gaia.parquet",
                version="v1",
                data_dir=dados,
                cache_dir=cache,
                out=saida,
            )

    caminho = asyncio.run(cenario())
    assert caminho == saida
    assert saida.read_bytes() == (servidor_remoto.layout.blobs / servidor_remoto.blob).read_bytes()


def test_latest_version():
    catalogo = {
        "datasets": [
            {
                "name": "x",
                "versions": [
                    {"version": "v1", "created_at": "2026-01-01T00:00:00Z"},
                    {"version": "v2", "created_at": "2026-02-01T00:00:00Z"},
                ],
            }
        ]
    }
    assert latest_version(catalogo, "x") == "v2"


def test_sync_deduplica_blobs_identicos(servidor_remoto, layout, gravar_parquet, tmp_path):
    origem = tmp_path / "entrada_dup"
    gravar_parquet(origem / "a.parquet", [1, 2])
    shutil.copyfile(origem / "a.parquet", origem / "b.parquet")
    publish(layout, origem, "dup_teste", "v1")

    dados = tmp_path / "data_dup"
    cache = tmp_path / "cache_dup"

    async def cenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=servidor_remoto.app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {servidor_remoto.token}"},
        ) as http:
            cliente = RemoteClient(http, "http://test")
            return await sync_dataset(
                cliente,
                "dup_teste",
                "v1",
                data_dir=dados,
                cache_dir=cache,
                connections=1,
                jobs=2,
            )

    resultado = asyncio.run(cenario())

    assert resultado.downloaded == 1
    a = dados / "dup_teste" / "v1" / "a.parquet"
    b = dados / "dup_teste" / "v1" / "b.parquet"
    assert a.is_file() and b.is_file()
    assert os.path.samefile(a, b)
    assert len([caminho for caminho in cache.iterdir() if caminho.is_file()]) == 1
