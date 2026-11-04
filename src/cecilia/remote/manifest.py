"""Manifesto imutável de um dataset publicado."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .hashing import canonical_json_bytes, sha256_bytes
from .layout import validate_blob, validate_dataset, validate_relpath, validate_version

REQUIRED_FIELDS = ("dataset", "version", "created_at", "files")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"campo {field!r} deve ser texto")
    return value


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"campo {field!r} deve ser inteiro não negativo")
    return value


def _schema(value: Any) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        raise ValidationError("campo 'schema' deve ser uma lista")
    campos = []
    for item in value:
        if not isinstance(item, dict):
            raise ValidationError("cada campo do schema deve ser um objeto")
        if not isinstance(item.get("name"), str) or not isinstance(item.get("type"), str):
            raise ValidationError("campo do schema precisa de 'name' e 'type' textuais")
        campos.append((item["name"], item["type"]))
    return tuple(campos)


def _provenance(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValidationError("campo 'provenance' deve ser um objeto")
    for chave, item in value.items():
        if not isinstance(chave, str) or not isinstance(item, str):
            raise ValidationError("'provenance' deve mapear texto para texto")
    return dict(value)


@dataclass(frozen=True)
class FileEntry:
    """Um arquivo Parquet publicado, apontando para um blob."""

    path: str
    blob: str
    bytes: int
    rows: int
    schema: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "blob": self.blob,
            "bytes": self.bytes,
            "rows": self.rows,
            "schema": [{"name": nome, "type": tipo} for nome, tipo in self.schema],
        }

    @classmethod
    def from_dict(cls, data: Any) -> FileEntry:
        if not isinstance(data, dict):
            raise ValidationError("arquivo do manifesto deve ser um objeto")
        faltando = [campo for campo in ("path", "blob", "bytes", "rows") if campo not in data]
        if faltando:
            raise ValidationError(f"arquivo do manifesto sem campo(s): {', '.join(faltando)}")
        return cls(
            path=validate_relpath(_text(data["path"], "path")),
            blob=validate_blob(_text(data["blob"], "blob")),
            bytes=_integer(data["bytes"], "bytes"),
            rows=_integer(data["rows"], "rows"),
            schema=_schema(data.get("schema", [])),
        )


@dataclass(frozen=True)
class Manifest:
    """Descrição completa e imutável de um dataset em uma versão."""

    dataset: str
    version: str
    created_at: str
    description: str
    license: str
    attribution: str
    provenance: dict[str, str]
    files: tuple[FileEntry, ...]
    supersedes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "version": self.version,
            "created_at": self.created_at,
            "description": self.description,
            "license": self.license,
            "attribution": self.attribution,
            "provenance": dict(sorted(self.provenance.items())),
            "files": [entry.to_dict() for entry in self.files],
            "supersedes": self.supersedes,
        }

    def digest(self) -> str:
        """Hash estável do manifesto; muda se qualquer conteúdo mudar."""
        return sha256_bytes(canonical_json_bytes(self.to_dict()))

    def to_json_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False).encode("utf-8") + b"\n"

    @classmethod
    def from_dict(cls, data: Any) -> Manifest:
        if not isinstance(data, dict):
            raise ValidationError("manifesto deve ser um objeto")
        faltando = [campo for campo in REQUIRED_FIELDS if campo not in data]
        if faltando:
            raise ValidationError(f"manifesto sem campo(s): {', '.join(faltando)}")

        arquivos = data["files"]
        if not isinstance(arquivos, list) or not arquivos:
            raise ValidationError("manifesto precisa de pelo menos um arquivo")
        entries = tuple(FileEntry.from_dict(item) for item in arquivos)
        caminhos = [entry.path for entry in entries]
        if len(caminhos) != len(set(caminhos)):
            raise ValidationError("manifesto com caminhos duplicados")

        supersedes = data.get("supersedes")
        if supersedes is not None:
            supersedes = validate_version(_text(supersedes, "supersedes"))

        return cls(
            dataset=validate_dataset(_text(data["dataset"], "dataset")),
            version=validate_version(_text(data["version"], "version")),
            created_at=_text(data["created_at"], "created_at"),
            description=_text(data.get("description", ""), "description"),
            license=_text(data.get("license", ""), "license"),
            attribution=_text(data.get("attribution", ""), "attribution"),
            provenance=_provenance(data.get("provenance", {})),
            files=entries,
            supersedes=supersedes,
        )


def load_manifest(path: Path) -> Manifest:
    """Lê e valida um manifesto do disco."""
    try:
        conteudo = path.read_text(encoding="utf-8")
        data = json.loads(conteudo)
    except OSError as exc:
        raise ValidationError(f"não foi possível ler {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"manifesto inválido em {path}: {exc}") from exc
    return Manifest.from_dict(data)
