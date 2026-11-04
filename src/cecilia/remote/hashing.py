"""Funções de hash usadas na publicação e na verificação."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path, chunk_size: int = CHUNK_SIZE) -> str:
    """Calcula o SHA-256 de um arquivo em streaming, sem carregá-lo inteiro."""
    digest = hashlib.sha256()
    with path.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(chunk_size), b""):
            digest.update(bloco)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Calcula o SHA-256 de um bloco de bytes."""
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(data: Any) -> bytes:
    """Serializa JSON de forma canônica para que o hash não dependa da ordem das chaves."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_json(data: Any) -> str:
    """SHA-256 da serialização canônica de um objeto JSON."""
    return sha256_bytes(canonical_json_bytes(data))
