"""Coleta de blobs não referenciados por nenhum manifesto."""

from __future__ import annotations

from pathlib import Path

from .catalog import iter_manifests
from .layout import BLOB_PATTERN, ServerLayout


def referenced_blobs(layout: ServerLayout) -> set[str]:
    """Conjunto de hashes citados por algum manifesto publicado."""
    referencias: set[str] = set()
    for _, manifest in iter_manifests(layout):
        referencias.update(entry.blob for entry in manifest.files)
    return referencias


def find_orphans(layout: ServerLayout) -> list[Path]:
    """Blobs no diretório que nenhum manifesto referencia."""
    if not layout.blobs.exists():
        return []
    referencias = referenced_blobs(layout)
    return sorted(
        caminho
        for caminho in layout.blobs.iterdir()
        if caminho.is_file()
        and BLOB_PATTERN.fullmatch(caminho.name)
        and caminho.name not in referencias
    )


def collect_garbage(layout: ServerLayout, *, apply: bool = False) -> list[Path]:
    """Lista órfãos e, com ``apply=True``, remove apenas eles."""
    orfaos = find_orphans(layout)
    if apply:
        for caminho in orfaos:
            caminho.unlink(missing_ok=True)
    return orfaos
