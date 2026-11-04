"""Catálogo global reconstruído a partir dos manifestos."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from .clock import utc_now
from .layout import ServerLayout
from .manifest import Manifest, load_manifest


def iter_manifests(layout: ServerLayout):
    """Percorre os manifestos publicados em ordem determinística."""
    for path in sorted(layout.datasets.glob("*/*/manifest.json")):
        yield path, load_manifest(path)


def build_catalog(layout: ServerLayout) -> dict[str, Any]:
    """Monta o catálogo em memória, sem gravar no disco."""
    por_dataset: dict[str, dict[str, Any]] = {}
    for _, manifest in iter_manifests(layout):
        item = por_dataset.setdefault(
            manifest.dataset,
            {"name": manifest.dataset, "versions": []},
        )
        item["versions"].append(_version_entry(manifest))

    datasets = []
    for nome in sorted(por_dataset):
        versoes = sorted(
            por_dataset[nome]["versions"],
            key=lambda versao: (versao["created_at"], versao["version"]),
        )
        datasets.append({"name": nome, "versions": versoes})

    return {"generated_at": utc_now(), "datasets": datasets}


def _version_entry(manifest: Manifest) -> dict[str, Any]:
    return {
        "version": manifest.version,
        "manifest": manifest.digest(),
        "created_at": manifest.created_at,
        "supersedes": manifest.supersedes,
        "files": len(manifest.files),
        "bytes": sum(entry.bytes for entry in manifest.files),
        "rows": sum(entry.rows for entry in manifest.files),
    }


def write_catalog(layout: ServerLayout, catalog: dict[str, Any]) -> Path:
    """Grava o catálogo de forma atômica."""
    layout.root.mkdir(parents=True, exist_ok=True)
    temporario = layout.root / f".catalog-{uuid4().hex}.json"
    temporario.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporario, layout.catalog)
    return layout.catalog


def rebuild_catalog(layout: ServerLayout) -> dict[str, Any]:
    """Reconstrói e grava o catálogo a partir dos manifestos."""
    catalog = build_catalog(layout)
    write_catalog(layout, catalog)
    return catalog
