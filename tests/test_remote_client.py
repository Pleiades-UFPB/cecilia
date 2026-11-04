"""Testes do cliente HTTP contra o servidor real via ASGI."""

import asyncio

import httpx
import pytest

from cecilia.remote.client import RemoteClient
from cecilia.remote.errors import ClientError


def _headers(servidor) -> dict[str, str]:
    return {"Authorization": f"Bearer {servidor.token}"}


def test_whoami_catalogo_e_manifesto(servidor_remoto):
    async def cenario():
        transporte = httpx.ASGITransport(app=servidor_remoto.app)
        async with httpx.AsyncClient(
            transport=transporte,
            base_url="http://test",
            headers=_headers(servidor_remoto),
        ) as http:
            cliente = RemoteClient(http, "http://test")
            return (
                await cliente.whoami(),
                await cliente.catalog(),
                await cliente.manifest("gaia_teste", "v1"),
            )

    quem, catalogo, manifesto = asyncio.run(cenario())
    assert quem["alias"] == "luan"
    assert catalogo["datasets"][0]["name"] == "gaia_teste"
    assert manifesto["files"][0]["path"] == "gaia.parquet"


def test_sem_chave_vira_client_error(servidor_remoto):
    async def cenario():
        transporte = httpx.ASGITransport(app=servidor_remoto.app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test") as http:
            cliente = RemoteClient(http, "http://test")
            with pytest.raises(ClientError) as excinfo:
                await cliente.catalog()
            return str(excinfo.value)

    assert "chave" in asyncio.run(cenario())


def test_dataset_desconhecido(servidor_remoto):
    async def cenario():
        transporte = httpx.ASGITransport(app=servidor_remoto.app)
        async with httpx.AsyncClient(
            transport=transporte,
            base_url="http://test",
            headers=_headers(servidor_remoto),
        ) as http:
            cliente = RemoteClient(http, "http://test")
            with pytest.raises(ClientError) as excinfo:
                await cliente.manifest("nao_existe", "v1")
            return str(excinfo.value)

    assert "não encontrado" in asyncio.run(cenario())
