"""Relógio do subsistema remoto."""

from datetime import UTC, datetime


def iso(moment: datetime) -> str:
    """Formata um datetime em ISO 8601 UTC, com sufixo ``Z``."""
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def utc_now() -> str:
    """Data e hora UTC em ISO 8601, com sufixo ``Z``."""
    return iso(datetime.now(UTC))
