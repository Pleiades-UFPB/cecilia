"""Relógio do subsistema remoto."""

from datetime import UTC, datetime


def utc_now() -> str:
    """Data e hora UTC em ISO 8601, com sufixo ``Z``."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
