"""Registro de auditoria dos acessos ao servidor."""

from __future__ import annotations

import re
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .clock import iso, utc_now
from .errors import ValidationError
from .layout import ServerLayout, secure_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    request_id TEXT NOT NULL,
    transfer_id TEXT,
    alias TEXT,
    key_id TEXT,
    action TEXT NOT NULL,
    path TEXT,
    dataset TEXT,
    version TEXT,
    file TEXT,
    blob TEXT,
    bytes_sent INTEGER NOT NULL,
    status INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    client_ip TEXT,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_access_ts ON access(ts);
CREATE INDEX IF NOT EXISTS idx_access_alias ON access(alias, ts);
CREATE INDEX IF NOT EXISTS idx_access_blob ON access(blob, ts);
"""

SINCE_PATTERN = re.compile(r"^(\d+)([dh])$")


@dataclass(frozen=True)
class AuditEntry:
    """Uma linha de acesso registrada."""

    request_id: str
    action: str
    status: int
    bytes_sent: int
    duration_ms: int
    ts: str = ""
    transfer_id: str | None = None
    alias: str | None = None
    key_id: str | None = None
    path: str | None = None
    dataset: str | None = None
    version: str | None = None
    file: str | None = None
    blob: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None

    def __post_init__(self) -> None:
        if not self.ts:
            object.__setattr__(self, "ts", utc_now())


def parse_since(value: str) -> str:
    """Converte ``7d``, ``24h`` ou uma data ISO em um limite inferior ISO."""
    value = value.strip()
    match = SINCE_PATTERN.fullmatch(value)
    if match:
        quantidade = int(match.group(1))
        delta = timedelta(days=quantidade) if match.group(2) == "d" else timedelta(hours=quantidade)
        return iso(datetime.now(UTC) - delta)
    try:
        momento = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"data inválida: {value!r} (use 7d, 24h ou ISO)") from exc
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=UTC)
    return iso(momento)


class AuditLog:
    """Banco append-only de acessos, com consulta por alias e período."""

    def __init__(self, layout: ServerLayout):
        self._path = layout.audit_db
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        secure_db(self._path)

    def record(self, entry: AuditEntry) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO access (
                    ts, request_id, transfer_id, alias, key_id, action, path,
                    dataset, version, file, blob, bytes_sent, status,
                    duration_ms, client_ip, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.ts,
                    entry.request_id,
                    entry.transfer_id,
                    entry.alias,
                    entry.key_id,
                    entry.action,
                    entry.path,
                    entry.dataset,
                    entry.version,
                    entry.file,
                    entry.blob,
                    entry.bytes_sent,
                    entry.status,
                    entry.duration_ms,
                    entry.client_ip,
                    entry.user_agent,
                ),
            )
            self._conn.commit()
            secure_db(self._path)

    def recent(
        self,
        *,
        limit: int = 50,
        since: str | None = None,
        alias: str | None = None,
    ) -> list[dict[str, object]]:
        limite = max(1, min(limit, 1000))
        clausulas = []
        parametros: list[object] = []
        if since is not None:
            clausulas.append("ts >= ?")
            parametros.append(since)
        if alias is not None:
            clausulas.append("alias = ?")
            parametros.append(alias)
        where = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        parametros.append(limite)
        with self._lock:
            linhas = self._conn.execute(
                f"SELECT * FROM access {where} ORDER BY ts DESC, id DESC LIMIT ?",
                parametros,
            ).fetchall()
        return [dict(linha) for linha in linhas]

    def prune(self, retention_days: int) -> int:
        """Remove entradas mais antigas que a retenção configurada."""
        if retention_days < 1:
            raise ValidationError("retention_days deve ser >= 1")
        corte = iso(datetime.now(UTC) - timedelta(days=retention_days))
        with self._lock:
            cursor = self._conn.execute("DELETE FROM access WHERE ts < ?", (corte,))
            self._conn.commit()
            secure_db(self._path)
            return cursor.rowcount

    def close(self) -> None:
        with self._lock:
            self._conn.close()
