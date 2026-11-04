"""Sincronização de datasets para o cache local e `data/raw`."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from uuid import uuid4

from .client import RemoteClient
from .clock import utc_now
from .download import download_blob
from .errors import ClientError
from .hashing import sha256_file, sha256_json


@dataclass(frozen=True)
class SyncResult:
    """Resultado de uma sincronização completa."""

    dataset: str
    version: str
    manifest_hash: str
    files: tuple[dict, ...]
    downloaded: int
    reused: int
    total_bytes: int
    data_path: Path


def latest_version(catalog: dict, dataset: str) -> str:
    """Escolhe a versão mais recente do dataset no catálogo."""
    for item in catalog.get("datasets", []):
        if item.get("name") != dataset:
            continue
        versoes = item.get("versions", [])
        if not versoes:
            break
        return max(
            versoes,
            key=lambda versao: (versao.get("created_at", ""), versao.get("version", "")),
        )["version"]
    raise ClientError(f"dataset não encontrado no catálogo: {dataset}")


def find_entry(manifest: dict, path: str) -> dict:
    """Localiza um arquivo lógico no manifesto."""
    for entry in manifest.get("files", []):
        if entry.get("path") == path:
            return entry
    raise ClientError(f"arquivo não encontrado no manifesto: {path}")


async def sync_dataset(
    remote: RemoteClient,
    dataset: str,
    version: str | None,
    *,
    data_dir: Path,
    cache_dir: Path,
    jobs: int = 4,
    connections: int = 4,
    force: bool = False,
    alias: str | None = None,
    on_manifest: Callable[[int], None] | None = None,
    on_progress: Callable[[int], None] | None = None,
) -> SyncResult:
    """Baixa todos os arquivos de uma versão e materializa em `data_dir`."""
    versao = version
    if versao is None:
        catalogo = await remote.catalog()
        versao = latest_version(catalogo, dataset)

    manifest = await remote.manifest(dataset, versao)
    arquivos = tuple(manifest.get("files", []))
    if not arquivos:
        raise ClientError(f"manifesto vazio: {dataset}@{versao}")

    por_blob: dict[str, dict] = {}
    for entry in arquivos:
        por_blob.setdefault(entry["blob"], entry)
    total_bytes = sum(int(entry["bytes"]) for entry in por_blob.values())
    if on_manifest is not None:
        on_manifest(total_bytes)

    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    destino = Path(data_dir) / dataset / versao
    destino.mkdir(parents=True, exist_ok=True)

    limite_conexoes = asyncio.Semaphore(max(1, connections))
    limite_jobs = asyncio.Semaphore(max(1, jobs))
    baixados = 0
    reusados = 0

    async def _baixar(entry: dict):
        nonlocal baixados, reusados
        async with limite_jobs:
            resultado = await download_blob(
                remote.http,
                remote.base_url,
                entry["blob"],
                int(entry["bytes"]),
                cache / entry["blob"],
                connections=connections,
                force=force,
                on_progress=on_progress,
                semaphore=limite_conexoes,
            )
        if resultado.downloaded:
            baixados += 1
        else:
            reusados += 1
        return entry["blob"], resultado

    resultados = await asyncio.gather(*(_baixar(entry) for entry in por_blob.values()))
    por_blob_resultado = dict(resultados)

    for entry in arquivos:
        resultado = por_blob_resultado[entry["blob"]]
        alvo = destino / entry["path"]
        alvo.parent.mkdir(parents=True, exist_ok=True)
        _materialize(resultado.path, alvo)

    manifest_hash = sha256_json(manifest)
    estado = {
        "dataset": dataset,
        "version": versao,
        "manifest": manifest_hash,
        "synced_at": utc_now(),
        "alias": alias,
        "files": list(arquivos),
    }
    _write_json(destino / ".cecilia.json", estado)

    return SyncResult(
        dataset=dataset,
        version=versao,
        manifest_hash=manifest_hash,
        files=arquivos,
        downloaded=baixados,
        reused=reusados,
        total_bytes=total_bytes,
        data_path=destino,
    )


async def get_file(
    remote: RemoteClient,
    dataset: str,
    path: str,
    *,
    version: str | None,
    data_dir: Path,
    cache_dir: Path,
    out: Path | None = None,
    connections: int = 4,
    force: bool = False,
    on_progress: Callable[[int], None] | None = None,
) -> Path:
    """Baixa um único arquivo lógico, sem sincronizar o dataset inteiro."""
    versao = version
    if versao is None:
        catalogo = await remote.catalog()
        versao = latest_version(catalogo, dataset)

    manifest = await remote.manifest(dataset, versao)
    entry = find_entry(manifest, path)
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)

    resultado = await download_blob(
        remote.http,
        remote.base_url,
        entry["blob"],
        int(entry["bytes"]),
        cache / entry["blob"],
        connections=connections,
        force=force,
        on_progress=on_progress,
        semaphore=asyncio.Semaphore(max(1, connections)),
    )

    if out is None:
        alvo = Path(data_dir) / dataset / versao / path
    elif out.is_dir():
        alvo = out / Path(path).name
    else:
        alvo = out
    alvo.parent.mkdir(parents=True, exist_ok=True)
    _materialize(resultado.path, alvo)
    return alvo


def verify_data(
    data_dir: Path,
    cache_dir: Path,
    *,
    quick: bool = False,
) -> list[str]:
    """Confere tamanho e SHA-256 dos arquivos materializados."""
    problemas: list[str] = []
    vistos: set[str] = set()
    for estado_path in sorted(Path(data_dir).glob("*/*/.cecilia.json")):
        try:
            estado = json.loads(estado_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problemas.append(f"estado ilegível: {estado_path}: {exc}")
            continue
        for entry in estado.get("files", []):
            alvo = estado_path.parent / entry["path"]
            if not alvo.is_file():
                problemas.append(f"ausente: {alvo}")
                continue
            if alvo.stat().st_size != int(entry["bytes"]):
                problemas.append(f"tamanho: {alvo}")
                continue
            cache = Path(cache_dir) / entry["blob"]
            if not cache.is_file():
                problemas.append(f"cache ausente: {cache.name}")
            if not quick and entry["blob"] not in vistos:
                vistos.add(entry["blob"])
                if sha256_file(alvo) != entry["blob"]:
                    problemas.append(f"hash: {alvo}")
    return problemas


def manifest_rows(
    result: SyncResult,
    alias: str | None,
    when: str | None = None,
) -> list[str]:
    """Linhas prontas para a tabela do `data/README.md`."""
    data = when or date.today().isoformat()
    linhas = []
    for entry in result.files:
        linhas.append(
            f"| `{result.dataset}/{result.version}/{entry['path']}` "
            f"| CECILIA API "
            f"| `{result.dataset}@{result.version}` "
            f"(manifest `{result.manifest_hash[:12]}`) "
            f"| {data} "
            f"| {entry.get('rows', 0)} "
            f"| {alias or '-'} |"
        )
    return linhas


def _materialize(origem: Path, destino: Path) -> None:
    """Hardlink quando possível; cópia quando cache e dados estão em filesystems distintos."""
    if destino.exists():
        try:
            if os.path.samefile(origem, destino):
                return
        except OSError:
            pass
        destino.unlink()
    try:
        os.link(origem, destino)
    except OSError:
        shutil.copyfile(origem, destino)


def _write_json(path: Path, dados: dict) -> None:
    temporario = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporario.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporario, path)
    finally:
        temporario.unlink(missing_ok=True)


def state_files(data_dir: Path) -> list[Path]:
    """Lista os estados de sincronização encontrados."""
    return sorted(Path(data_dir).glob("*/*/.cecilia.json"))
