"""Publicação atômica de um diretório de Parquets como dataset imutável."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pyarrow.parquet as pq

from .catalog import rebuild_catalog
from .clock import utc_now
from .errors import PublishError
from .hashing import sha256_file
from .layout import ServerLayout, validate_relpath, validate_version
from .manifest import FileEntry, Manifest


@dataclass(frozen=True)
class PublishResult:
    """Resumo de uma publicação."""

    manifest: Manifest
    manifest_path: Path
    copied: int
    reused: int


def publish(
    layout: ServerLayout,
    source: str | Path,
    dataset: str,
    version: str,
    *,
    description: str = "",
    provenance: dict[str, str] | None = None,
    license: str = "",
    attribution: str = "",
    supersedes: str | None = None,
) -> PublishResult:
    """Publica ``source`` como ``dataset@version``, sem sobrescrever versão existente."""
    origem = Path(source)
    final_dir = layout.dataset_dir(dataset, version)
    if final_dir.exists():
        raise PublishError(f"versão já publicada: {dataset}@{version}")
    if supersedes is not None:
        validate_version(supersedes)

    arquivos = _list_parquet(origem)
    layout.prepare()

    entries: list[FileEntry] = []
    copiados = 0
    reaproveitados = 0
    for relativo, caminho in arquivos:
        entry = _describe_parquet(caminho, relativo)
        if _store_blob(caminho, layout.blobs / entry.blob, entry.bytes):
            copiados += 1
        else:
            reaproveitados += 1
        entries.append(entry)

    manifest = Manifest(
        dataset=dataset,
        version=version,
        created_at=utc_now(),
        description=description,
        license=license,
        attribution=attribution,
        provenance=provenance or {},
        files=tuple(entries),
        supersedes=supersedes,
    )

    final_dir.mkdir(parents=True)
    temporario = layout.staging / f"{dataset}-{version}-{uuid4().hex}.json"
    try:
        temporario.write_bytes(manifest.to_json_bytes())
        os.replace(temporario, final_dir / "manifest.json")
    finally:
        temporario.unlink(missing_ok=True)

    rebuild_catalog(layout)
    return PublishResult(
        manifest=manifest,
        manifest_path=final_dir / "manifest.json",
        copied=copiados,
        reused=reaproveitados,
    )


def _list_parquet(source: Path) -> list[tuple[str, Path]]:
    if not source.is_dir():
        raise PublishError(f"diretório de origem inexistente: {source}")
    raiz = source.resolve()
    encontrados = []
    for caminho in sorted(source.rglob("*.parquet")):
        if caminho.is_symlink():
            continue
        resolvido = caminho.resolve()
        if not resolvido.is_relative_to(raiz):
            raise PublishError(f"arquivo fora do diretório de origem: {caminho}")
        relativo = caminho.relative_to(source).as_posix()
        encontrados.append((validate_relpath(relativo), caminho))
    if not encontrados:
        raise PublishError(f"nenhum arquivo .parquet em {source}")
    return encontrados


def _describe_parquet(path: Path, relativo: str) -> FileEntry:
    parquet = pq.ParquetFile(path)
    metadata = parquet.metadata
    if metadata is None:
        raise PublishError(f"Parquet sem metadados: {path}")
    schema: tuple[tuple[str, str], ...] = tuple(
        (campo.name, str(campo.type)) for campo in parquet.schema_arrow
    )
    return FileEntry(
        path=relativo,
        blob=sha256_file(path),
        bytes=path.stat().st_size,
        rows=metadata.num_rows,
        schema=schema,
    )


def _store_blob(source: Path, target: Path, expected_bytes: int) -> bool:
    """Copia o blob se necessário; devolve ``True`` quando houve cópia."""
    if target.exists():
        if target.stat().st_size != expected_bytes:
            raise PublishError(
                f"blob existente com tamanho divergente: {target.name} "
                f"({target.stat().st_size} != {expected_bytes})"
            )
        return False

    temporario = target.parent / f".tmp-{uuid4().hex}"
    try:
        shutil.copyfile(source, temporario)
        if temporario.stat().st_size != expected_bytes:
            raise PublishError(
                f"cópia incompleta de {source}: {temporario.stat().st_size} != {expected_bytes}"
            )
        os.replace(temporario, target)
    finally:
        temporario.unlink(missing_ok=True)
    return True


def describe_source(source: str | Path) -> list[tuple[str, Path]]:
    """Lista os Parquets que seriam publicados, sem copiar nada."""
    return _list_parquet(Path(source))


__all__ = ["PublishResult", "describe_source", "publish"]
