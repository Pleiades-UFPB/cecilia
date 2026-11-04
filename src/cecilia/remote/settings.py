"""Configuração do servidor de datasets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import RemoteError
from .layout import ServerLayout

MIN_PEPPER_LENGTH = 32


@dataclass(frozen=True)
class Settings:
    """Parâmetros do servidor; em produção vêm do ambiente."""

    layout: ServerLayout
    pepper: str
    max_streams_per_key: int = 4
    catalog_per_minute: int = 60
    blob_per_minute: int = 600
    global_per_minute: int = 120
    audit_retention_days: int = 90
    trust_proxy: bool = False

    @classmethod
    def from_env(cls, root: str | Path | None = None) -> Settings:
        """Monta a configuração a partir das variáveis ``CECILIA_*``."""
        pepper = os.environ.get("CECILIA_KEY_PEPPER", "")
        if len(pepper) < MIN_PEPPER_LENGTH:
            raise RemoteError(
                f"CECILIA_KEY_PEPPER ausente ou curta (mínimo {MIN_PEPPER_LENGTH} caracteres)"
            )
        return cls(
            layout=ServerLayout.resolve(root),
            pepper=pepper,
            max_streams_per_key=_env_int("CECILIA_MAX_STREAMS_PER_KEY", 4, minimum=1),
            catalog_per_minute=_env_int("CECILIA_CATALOG_PER_MINUTE", 60, minimum=1),
            blob_per_minute=_env_int("CECILIA_BLOB_PER_MINUTE", 600, minimum=1),
            global_per_minute=_env_int("CECILIA_GLOBAL_PER_MINUTE", 120, minimum=1),
            audit_retention_days=_env_int("CECILIA_AUDIT_RETENTION_DAYS", 90, minimum=1),
            trust_proxy=_env_bool("CECILIA_TRUST_PROXY", False),
        )


def _env_int(name: str, default: int, *, minimum: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RemoteError(f"{name} deve ser inteiro") from exc
    if value < minimum:
        raise RemoteError(f"{name} deve ser >= {minimum}")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "sim", "yes"}
