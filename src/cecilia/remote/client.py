"""Cliente HTTP do servidor de datasets."""

from __future__ import annotations

from urllib.parse import quote

import httpx

from cecilia import __version__

from .config import ClientSettings
from .errors import ClientError

USER_AGENT = f"cecilia/{__version__}"
TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)


def raise_for_status(response: httpx.Response) -> None:
    """Converte códigos de erro do servidor em mensagens acionáveis."""
    if response.status_code < 400:
        return
    if response.status_code in (401, 403):
        raise ClientError("chave inválida, expirada ou revogada; rode `cecilia remote login`")
    if response.status_code == 404:
        raise ClientError("recurso não encontrado no servidor")
    if response.status_code == 429:
        raise ClientError("limite do servidor excedido; tente novamente mais tarde")
    raise ClientError(f"servidor respondeu {response.status_code}")


class RemoteClient:
    """Acesso assíncrono ao catálogo, manifestos e blobs."""

    def __init__(self, http: httpx.AsyncClient, base_url: str):
        self.http = http
        self.base_url = base_url.rstrip("/")

    @classmethod
    def from_settings(cls, settings: ClientSettings) -> RemoteClient:
        http = httpx.AsyncClient(
            base_url=settings.url,
            headers={
                "Authorization": f"Bearer {settings.key}",
                "User-Agent": USER_AGENT,
            },
            timeout=TIMEOUT,
            follow_redirects=False,
        )
        return cls(http, settings.url)

    async def close(self) -> None:
        await self.http.aclose()

    async def _get_json(self, path: str) -> dict:
        resposta = await self.http.get(path)
        raise_for_status(resposta)
        try:
            return resposta.json()
        except ValueError as exc:
            raise ClientError(f"resposta inválida do servidor em {path}") from exc

    async def whoami(self) -> dict:
        return await self._get_json("/v1/whoami")

    async def catalog(self) -> dict:
        return await self._get_json("/v1/catalog")

    async def manifest(self, dataset: str, version: str) -> dict:
        rota = f"/v1/datasets/{quote(dataset, safe='')}/versions/{quote(version, safe='')}"
        return await self._get_json(rota)
