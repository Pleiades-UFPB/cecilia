"""Verificação de integridade dos blobs, manifestos e catálogo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq

from .catalog import build_catalog
from .errors import RemoteError
from .hashing import sha256_file
from .layout import ServerLayout
from .manifest import FileEntry, Manifest, load_manifest


@dataclass(frozen=True)
class VerifyIssue:
    """Um problema encontrado durante a verificação."""

    kind: str
    subject: str
    detail: str


def verify(layout: ServerLayout, *, deep: bool = False) -> list[VerifyIssue]:
    """Confere blobs, manifestos e catálogo; devolve todos os problemas encontrados."""
    problemas: list[VerifyIssue] = []
    if not layout.datasets.exists():
        return [
            VerifyIssue(
                kind="datasets",
                subject=str(layout.datasets),
                detail="diretório de datasets ausente",
            )
        ]

    for caminho in sorted(layout.datasets.glob("*/*/manifest.json")):
        try:
            manifest = load_manifest(caminho)
        except RemoteError as exc:
            problemas.append(VerifyIssue("manifest", str(caminho), str(exc)))
            continue
        problemas.extend(_verify_localizacao(caminho, manifest))
        for entry in manifest.files:
            problemas.extend(_verify_entry(layout, manifest, entry, deep=deep))

    problemas.extend(_verify_catalog(layout))
    return problemas


def _verify_localizacao(path: Path, manifest: Manifest) -> list[VerifyIssue]:
    if path.parent.name == manifest.version and path.parent.parent.name == manifest.dataset:
        return []
    return [
        VerifyIssue(
            kind="manifest-path",
            subject=str(path),
            detail=f"caminho não corresponde a {manifest.dataset}@{manifest.version}",
        )
    ]


def _verify_entry(
    layout: ServerLayout,
    manifest: Manifest,
    entry: FileEntry,
    *,
    deep: bool,
) -> list[VerifyIssue]:
    referencia = f"{manifest.dataset}@{manifest.version}:{entry.path}"
    blob = layout.blobs / entry.blob
    if not blob.is_file():
        return [VerifyIssue("blob-missing", entry.blob, referencia)]
    if blob.stat().st_size != entry.bytes:
        return [
            VerifyIssue(
                "blob-size",
                entry.blob,
                f"{referencia} ({blob.stat().st_size} != {entry.bytes})",
            )
        ]
    if sha256_file(blob) != entry.blob:
        return [VerifyIssue("blob-hash", entry.blob, referencia)]
    if not deep:
        return []
    return _verify_parquet(blob, entry, referencia)


def _verify_parquet(blob: Path, entry: FileEntry, referencia: str) -> list[VerifyIssue]:
    try:
        parquet = pq.ParquetFile(blob)
    except Exception as exc:
        return [VerifyIssue("blob-read", entry.blob, f"{referencia}: {exc}")]
    metadata = parquet.metadata
    if metadata is None:
        return [VerifyIssue("blob-read", entry.blob, f"{referencia}: sem metadados")]
    problemas = []
    if metadata.num_rows != entry.rows:
        problemas.append(
            VerifyIssue(
                "blob-rows",
                entry.blob,
                f"{referencia} ({metadata.num_rows} != {entry.rows})",
            )
        )
    schema = tuple((campo.name, str(campo.type)) for campo in parquet.schema_arrow)
    if schema != entry.schema:
        problemas.append(VerifyIssue("blob-schema", entry.blob, referencia))
    return problemas


def _verify_catalog(layout: ServerLayout) -> list[VerifyIssue]:
    if not layout.catalog.is_file():
        return [VerifyIssue("catalog", str(layout.catalog), "catálogo ausente")]
    try:
        armazenado = json.loads(layout.catalog.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [VerifyIssue("catalog", str(layout.catalog), str(exc))]
    try:
        esperado = build_catalog(layout)
    except RemoteError as exc:
        return [VerifyIssue("catalog", str(layout.catalog), str(exc))]
    if armazenado.get("datasets") != esperado.get("datasets"):
        return [
            VerifyIssue(
                "catalog",
                str(layout.catalog),
                "catálogo desatualizado em relação aos manifestos",
            )
        ]
    return []
