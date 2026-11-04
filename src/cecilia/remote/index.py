"""Índice blob → arquivo lógico, derivado dos manifestos publicados."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .errors import RemoteError
from .layout import ServerLayout
from .manifest import load_manifest


@dataclass(frozen=True)
class BlobRef:
    """Um arquivo lógico que aponta para um blob."""

    dataset: str
    version: str
    path: str


class BlobIndex:
    """Mantém um mapa em memória e o reconstrói quando envelhece."""

    def __init__(self, layout: ServerLayout, max_age_seconds: float = 30.0):
        self._layout = layout
        self._max_age = max_age_seconds
        self._lock = threading.Lock()
        self._built_at = 0.0
        self._map: dict[str, tuple[BlobRef, ...]] = {}

    def lookup(self, blob: str, *, force: bool = False) -> tuple[BlobRef, ...]:
        """Devolve os arquivos que usam o blob; reconstruir é barato."""
        with self._lock:
            if force or (time.monotonic() - self._built_at) > self._max_age:
                self._rebuild()
            return self._map.get(blob, ())

    def _rebuild(self) -> None:
        mapa: dict[str, list[BlobRef]] = {}
        for caminho in sorted(self._layout.datasets.glob("*/*/manifest.json")):
            try:
                manifest = load_manifest(caminho)
            except RemoteError:
                continue
            for entry in manifest.files:
                mapa.setdefault(entry.blob, []).append(
                    BlobRef(
                        dataset=manifest.dataset,
                        version=manifest.version,
                        path=entry.path,
                    )
                )
        self._map = {blob: tuple(refs) for blob, refs in mapa.items()}
        self._built_at = time.monotonic()
