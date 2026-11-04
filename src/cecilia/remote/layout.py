"""Layout do servidor de dados: raiz, blobs, datasets e staging."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import ValidationError

DATASET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
VERSION_PATTERN = re.compile(r"^v[0-9]+$")
BLOB_PATTERN = re.compile(r"^[0-9a-f]{64}$")

DEFAULT_ROOT = Path("/srv/cecilia")


def validate_dataset(dataset: str) -> str:
    """Aceita apenas nomes minúsculos, com dígitos, ``_`` e ``-``."""
    if not DATASET_PATTERN.fullmatch(dataset):
        raise ValidationError(
            f"dataset inválido: {dataset!r} "
            "(use minúsculas, dígitos, '_' ou '-', começando por letra ou dígito)"
        )
    return dataset


def validate_version(version: str) -> str:
    """Aceita apenas ``v`` seguido de dígitos (v1, v2, ...)."""
    if not VERSION_PATTERN.fullmatch(version):
        raise ValidationError(f"versão inválida: {version!r} (esperado v1, v2, ...)")
    return version


def validate_blob(blob: str) -> str:
    """Aceita apenas SHA-256 em hexadecimal minúsculo."""
    if not BLOB_PATTERN.fullmatch(blob):
        raise ValidationError(f"blob inválido: {blob!r} (esperado SHA-256 hexadecimal)")
    return blob


def validate_relpath(path: str) -> str:
    """Aceita apenas caminho relativo POSIX, sem ``..``, absoluto ou barra invertida."""
    if not path or "\\" in path:
        raise ValidationError(f"caminho inválido: {path!r}")
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or str(pure) != path:
        raise ValidationError(f"caminho inválido: {path!r}")
    return path


def secure_db(path: Path) -> None:
    """Restringe o banco e os arquivos WAL/SHM à leitura do dono."""
    for sufixo in ("", "-wal", "-shm"):
        candidato = Path(f"{path}{sufixo}")
        try:
            candidato.chmod(0o600)
        except OSError:
            continue


@dataclass(frozen=True)
class ServerLayout:
    """Diretórios do servidor de datasets."""

    root: Path

    @classmethod
    def resolve(cls, root: str | Path | None = None) -> ServerLayout:
        """Resolve a raiz por argumento, ``CECILIA_SERVER_ROOT`` ou ``/srv/cecilia``."""
        if root is None:
            root = os.environ.get("CECILIA_SERVER_ROOT", str(DEFAULT_ROOT))
        return cls(Path(root).expanduser().resolve())

    @property
    def blobs(self) -> Path:
        return self.root / "blobs"

    @property
    def datasets(self) -> Path:
        return self.root / "datasets"

    @property
    def staging(self) -> Path:
        return self.root / "staging"

    @property
    def catalog(self) -> Path:
        return self.root / "catalog.json"

    @property
    def keys_db(self) -> Path:
        return self.root / "keys.sqlite"

    @property
    def audit_db(self) -> Path:
        return self.root / "audit.sqlite"

    def dataset_dir(self, dataset: str, version: str) -> Path:
        return self.datasets / validate_dataset(dataset) / validate_version(version)

    def manifest_path(self, dataset: str, version: str) -> Path:
        return self.dataset_dir(dataset, version) / "manifest.json"

    def prepare(self) -> None:
        """Cria os diretórios necessários, sem tocar em conteúdo existente."""
        for directory in (self.root, self.blobs, self.datasets, self.staging):
            directory.mkdir(parents=True, exist_ok=True)
