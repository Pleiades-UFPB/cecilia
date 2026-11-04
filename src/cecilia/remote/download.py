"""Download de blobs com retomada, chunks paralelos e verificação de hash."""

from __future__ import annotations

import asyncio
import json
import os
import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx

from .client import raise_for_status
from .errors import ClientError
from .hashing import sha256_file

CHUNK_SIZE = 32 * 1024 * 1024
PARALLEL_THRESHOLD = 64 * 1024 * 1024
MAX_ATTEMPTS = 5
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class DownloadResult:
    """Resultado de um download já verificado."""

    path: Path
    bytes: int
    downloaded: bool


class _Retry(Exception):
    """Falha transitória que pode ser repetida."""


async def download_blob(
    http: httpx.AsyncClient,
    base_url: str,
    blob: str,
    size: int,
    dest: Path,
    *,
    connections: int = 4,
    chunk_size: int = CHUNK_SIZE,
    threshold: int = PARALLEL_THRESHOLD,
    force: bool = False,
    on_progress: Callable[[int], None] | None = None,
    semaphore: asyncio.Semaphore | None = None,
) -> DownloadResult:
    """Baixa um blob para ``dest``, reaproveitando o que já estiver íntegro."""
    destino = Path(dest)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists():
        if not force and destino.stat().st_size == size and await _hash_ok(destino, blob):
            return DownloadResult(destino, size, False)
        destino.unlink()

    parcial = destino.with_name(destino.name + ".part")
    estado = destino.with_name(destino.name + ".part.json")
    if force:
        parcial.unlink(missing_ok=True)
        estado.unlink(missing_ok=True)

    url = f"{base_url.rstrip('/')}/v1/blobs/{blob}"
    transfer_id = uuid4().hex
    limite = semaphore or asyncio.Semaphore(max(1, connections))

    if size >= threshold and connections > 1:
        await _download_chunks(
            http,
            url,
            parcial,
            estado,
            blob,
            size,
            connections=connections,
            chunk_size=chunk_size,
            transfer_id=transfer_id,
            semaphore=limite,
            on_progress=on_progress,
        )
    else:
        await _download_single(
            http,
            url,
            parcial,
            size,
            transfer_id=transfer_id,
            semaphore=limite,
            on_progress=on_progress,
        )

    if not await _hash_ok(parcial, blob):
        parcial.unlink(missing_ok=True)
        estado.unlink(missing_ok=True)
        raise ClientError(f"hash não confere para {blob[:12]}...")

    os.replace(parcial, destino)
    estado.unlink(missing_ok=True)
    return DownloadResult(destino, size, True)


async def _hash_ok(path: Path, blob: str) -> bool:
    if not path.is_file():
        return False
    return await asyncio.to_thread(sha256_file, path) == blob


async def _download_single(
    http: httpx.AsyncClient,
    url: str,
    parcial: Path,
    size: int,
    *,
    transfer_id: str,
    semaphore: asyncio.Semaphore,
    on_progress: Callable[[int], None] | None,
) -> None:
    for tentativa in range(MAX_ATTEMPTS):
        deslocamento = parcial.stat().st_size if parcial.exists() else 0
        if deslocamento > size:
            parcial.unlink()
            deslocamento = 0
        headers = {"X-Cecilia-Transfer-Id": transfer_id}
        if deslocamento:
            headers["Range"] = f"bytes={deslocamento}-"
        try:
            async with semaphore:
                async with http.stream("GET", url, headers=headers) as resposta:
                    if resposta.status_code in RETRY_STATUS:
                        raise _Retry(f"status {resposta.status_code}")
                    if resposta.status_code == 416 and deslocamento == size:
                        return
                    raise_for_status(resposta)
                    if resposta.status_code not in (200, 206):
                        raise ClientError(
                            f"resposta inesperada do servidor: {resposta.status_code}"
                        )
                    modo = "ab" if resposta.status_code == 206 else "wb"
                    with parcial.open(modo) as arquivo:
                        async for bloco in resposta.aiter_bytes():
                            arquivo.write(bloco)
                            if on_progress is not None:
                                on_progress(len(bloco))
        except (httpx.TransportError, _Retry) as exc:
            if tentativa == MAX_ATTEMPTS - 1:
                raise ClientError(f"falha ao baixar blob: {exc}") from exc
            await _backoff(tentativa)
            continue

        if parcial.exists() and parcial.stat().st_size == size:
            return
        await _backoff(tentativa)

    raise ClientError("download incompleto após novas tentativas")


async def _download_chunks(
    http: httpx.AsyncClient,
    url: str,
    parcial: Path,
    estado: Path,
    blob: str,
    size: int,
    *,
    connections: int,
    chunk_size: int,
    transfer_id: str,
    semaphore: asyncio.Semaphore,
    on_progress: Callable[[int], None] | None,
) -> None:
    if chunk_size <= 0:
        raise ClientError("chunk_size deve ser positivo")
    total = (size + chunk_size - 1) // chunk_size
    concluidos = _load_completed(estado, blob, size, chunk_size)
    concluidos = {indice for indice in concluidos if 0 <= indice < total}

    if parcial.exists() and parcial.stat().st_size != size:
        parcial.unlink()
        concluidos = set()
    if not parcial.exists():
        with parcial.open("wb") as arquivo:
            arquivo.truncate(size)

    pendentes = [indice for indice in range(total) if indice not in concluidos]
    fila: asyncio.Queue[int] = asyncio.Queue()
    for indice in pendentes:
        fila.put_nowait(indice)
    trava = asyncio.Lock()

    descritor = os.open(parcial, os.O_RDWR)
    try:

        async def trabalhador() -> None:
            while True:
                try:
                    indice = fila.get_nowait()
                except asyncio.QueueEmpty:
                    return
                await _download_chunk(
                    http,
                    url,
                    descritor,
                    indice,
                    chunk_size,
                    size,
                    transfer_id,
                    semaphore,
                    on_progress,
                )
                async with trava:
                    concluidos.add(indice)
                    _save_state(estado, blob, size, chunk_size, concluidos)

        tarefas = [
            asyncio.create_task(trabalhador()) for _ in range(min(connections, len(pendentes)))
        ]
        try:
            await asyncio.gather(*tarefas)
        except BaseException:
            for tarefa in tarefas:
                tarefa.cancel()
            await asyncio.gather(*tarefas, return_exceptions=True)
            raise
    finally:
        os.close(descritor)

    if len(concluidos) != total:
        raise ClientError("download em chunks incompleto")


async def _download_chunk(
    http: httpx.AsyncClient,
    url: str,
    descritor: int,
    indice: int,
    chunk_size: int,
    size: int,
    transfer_id: str,
    semaphore: asyncio.Semaphore,
    on_progress: Callable[[int], None] | None,
) -> None:
    inicio = indice * chunk_size
    fim = min(inicio + chunk_size, size) - 1
    for tentativa in range(MAX_ATTEMPTS):
        headers = {
            "Range": f"bytes={inicio}-{fim}",
            "X-Cecilia-Transfer-Id": transfer_id,
        }
        try:
            async with semaphore:
                async with http.stream("GET", url, headers=headers) as resposta:
                    if resposta.status_code in RETRY_STATUS:
                        raise _Retry(f"status {resposta.status_code}")
                    raise_for_status(resposta)
                    if resposta.status_code != 206:
                        raise ClientError("servidor ignorou Range; use --connections 1")
                    escrito = 0
                    async for bloco in resposta.aiter_bytes():
                        os.pwrite(descritor, bloco, inicio + escrito)
                        escrito += len(bloco)
                        if on_progress is not None:
                            on_progress(len(bloco))
                    if escrito != fim - inicio + 1:
                        raise _Retry("chunk incompleto")
                    return
        except (httpx.TransportError, _Retry) as exc:
            if tentativa == MAX_ATTEMPTS - 1:
                raise ClientError(f"falha no chunk {indice}: {exc}") from exc
            await _backoff(tentativa)


def _load_completed(estado: Path, blob: str, size: int, chunk_size: int) -> set[int]:
    try:
        dados = json.loads(estado.read_text(encoding="utf-8"))
        if (
            dados.get("blob") == blob
            and dados.get("size") == size
            and dados.get("chunk_size") == chunk_size
        ):
            return {int(indice) for indice in dados.get("completed", [])}
    except (OSError, ValueError, TypeError):
        pass
    estado.unlink(missing_ok=True)
    return set()


def _save_state(
    estado: Path,
    blob: str,
    size: int,
    chunk_size: int,
    concluidos: set[int],
) -> None:
    dados = {
        "blob": blob,
        "size": size,
        "chunk_size": chunk_size,
        "completed": sorted(concluidos),
    }
    temporario = estado.with_name(f".{estado.name}.{uuid4().hex}.tmp")
    try:
        temporario.write_text(json.dumps(dados), encoding="utf-8")
        os.replace(temporario, estado)
    finally:
        temporario.unlink(missing_ok=True)


async def _backoff(tentativa: int) -> None:
    espera = min(0.2 * (2**tentativa) + random.random() * 0.2, 10.0)
    await asyncio.sleep(espera)
