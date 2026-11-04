"""Testes do download: simples, paralelo, retomada e integridade."""

import asyncio
import json

import httpx
import pytest

from cecilia.remote.download import download_blob
from cecilia.remote.errors import ClientError


class CountingTransport(httpx.AsyncBaseTransport):
    """Encapsula o transporte ASGI e registra cada requisição."""

    def __init__(self, inner: httpx.AsyncBaseTransport):
        self.inner = inner
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return await self.inner.handle_async_request(request)


async def _baixar(servidor, destino, *, autorizado=True, **kwargs):
    transporte = CountingTransport(httpx.ASGITransport(app=servidor.app))
    headers = {"Authorization": f"Bearer {servidor.token}"} if autorizado else {}
    async with httpx.AsyncClient(
        transport=transporte,
        base_url="http://test",
        headers=headers,
    ) as http:
        resultado = await download_blob(
            http,
            "http://test",
            servidor.blob,
            servidor.size,
            destino,
            **kwargs,
        )
    return resultado, transporte


def _conteudo(servidor) -> bytes:
    return (servidor.layout.blobs / servidor.blob).read_bytes()


def test_download_simples(servidor_remoto, tmp_path):
    destino = tmp_path / "cache" / servidor_remoto.blob
    resultado, _ = asyncio.run(_baixar(servidor_remoto, destino, connections=1, threshold=0))

    assert resultado.downloaded is True
    assert destino.exists()
    assert destino.read_bytes() == _conteudo(servidor_remoto)


def test_download_paralelo(servidor_remoto, tmp_path):
    destino = tmp_path / "cache" / servidor_remoto.blob
    resultado, transporte = asyncio.run(
        _baixar(
            servidor_remoto,
            destino,
            connections=2,
            chunk_size=64,
            threshold=0,
        )
    )

    assert resultado.downloaded is True
    assert destino.read_bytes() == _conteudo(servidor_remoto)
    ranges = [
        request.headers.get("range")
        for request in transporte.requests
        if request.url.path.endswith(servidor_remoto.blob)
    ]
    assert any(ranges)
    assert all(rango.startswith("bytes=") for rango in ranges)


def test_retomada_simples(servidor_remoto, tmp_path):
    destino = tmp_path / "cache" / servidor_remoto.blob
    parcial = destino.with_name(destino.name + ".part")
    parcial.parent.mkdir(parents=True)
    parcial.write_bytes(_conteudo(servidor_remoto)[:100])

    resultado, transporte = asyncio.run(
        _baixar(servidor_remoto, destino, connections=1, threshold=0)
    )

    assert resultado.downloaded is True
    assert destino.read_bytes() == _conteudo(servidor_remoto)
    ranges = [
        request.headers.get("range")
        for request in transporte.requests
        if request.url.path.endswith(servidor_remoto.blob)
    ]
    assert ranges[0] == "bytes=100-"


def test_retomada_em_chunks(servidor_remoto, tmp_path):
    destino = tmp_path / "cache" / servidor_remoto.blob
    parcial = destino.with_name(destino.name + ".part")
    estado = destino.with_name(destino.name + ".part.json")
    parcial.parent.mkdir(parents=True)

    conteudo = _conteudo(servidor_remoto)
    with parcial.open("wb") as arquivo:
        arquivo.write(conteudo)
        arquivo.truncate(servidor_remoto.size)
    estado.write_text(
        json.dumps(
            {
                "blob": servidor_remoto.blob,
                "size": servidor_remoto.size,
                "chunk_size": 64,
                "completed": [0],
            }
        ),
        encoding="utf-8",
    )

    resultado, transporte = asyncio.run(
        _baixar(
            servidor_remoto,
            destino,
            connections=2,
            chunk_size=64,
            threshold=0,
        )
    )

    assert resultado.downloaded is True
    assert destino.read_bytes() == conteudo
    ranges = [
        request.headers.get("range")
        for request in transporte.requests
        if request.url.path.endswith(servidor_remoto.blob)
    ]
    assert ranges
    assert all(rango != "bytes=0-63" for rango in ranges)
    assert any(rango.startswith("bytes=64-") for rango in ranges)


def test_hash_divergente_remove_parcial(servidor_remoto, tmp_path):
    blob = servidor_remoto.layout.blobs / servidor_remoto.blob
    blob.write_bytes(b"x" * servidor_remoto.size)
    destino = tmp_path / "cache" / servidor_remoto.blob

    with pytest.raises(ClientError):
        asyncio.run(_baixar(servidor_remoto, destino, connections=2, chunk_size=64, threshold=0))

    assert not destino.exists()
    assert not destino.with_name(destino.name + ".part").exists()


def test_sem_autorizacao(servidor_remoto, tmp_path):
    destino = tmp_path / "cache" / servidor_remoto.blob

    with pytest.raises(ClientError):
        asyncio.run(_baixar(servidor_remoto, destino, autorizado=False, connections=1, threshold=0))

    assert not destino.exists()


def test_reaproveita_blob_em_cache(servidor_remoto, tmp_path):
    destino = tmp_path / "cache" / servidor_remoto.blob
    asyncio.run(_baixar(servidor_remoto, destino, connections=1, threshold=0))

    resultado, transporte = asyncio.run(
        _baixar(servidor_remoto, destino, connections=1, threshold=0)
    )

    assert resultado.downloaded is False
    assert transporte.requests == []
