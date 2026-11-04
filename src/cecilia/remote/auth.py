"""Chaves de API: emissão, verificação, expiração e revogação."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .clock import iso, utc_now
from .errors import RemoteError, ValidationError
from .layout import ServerLayout, secure_db

KEY_PREFIX = "ck_"
KEY_ID_BYTES = 8
SECRET_BYTES = 32
TOUCH_INTERVAL_SECONDS = 60

ALIAS_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS keys (
    key_id TEXT PRIMARY KEY,
    alias TEXT NOT NULL,
    secret_hmac TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    last_used_at TEXT
)
"""


@dataclass(frozen=True)
class IssuedKey:
    """Chave recém-emitida; o token só existe neste retorno."""

    key_id: str
    alias: str
    token: str
    created_at: str
    expires_at: str


@dataclass(frozen=True)
class Principal:
    """Identidade autenticada em uma requisição."""

    key_id: str
    alias: str
    expires_at: str


@dataclass(frozen=True)
class KeyRecord:
    """Chave listada sem o segredo."""

    key_id: str
    alias: str
    created_at: str
    expires_at: str
    revoked_at: str | None
    last_used_at: str | None


def validate_alias(alias: str) -> str:
    """Alias minúsculo, começando por letra ou dígito."""
    if not ALIAS_PATTERN.fullmatch(alias):
        raise ValidationError(
            f"alias inválido: {alias!r} "
            "(use minúsculas, dígitos, '.', '_' ou '-', começando por letra ou dígito)"
        )
    return alias


def parse_token(token: str) -> tuple[str, str] | None:
    """Separa ``ck_<key_id>_<segredo>`` e valida o formato hexadecimal."""
    if not token.startswith(KEY_PREFIX):
        return None
    partes = token.split("_")
    if len(partes) != 3:
        return None
    _, key_id, segredo = partes
    if len(key_id) != KEY_ID_BYTES * 2 or len(segredo) != SECRET_BYTES * 2:
        return None
    try:
        int(key_id, 16)
        int(segredo, 16)
    except ValueError:
        return None
    return key_id, segredo


def _hmac_secret(pepper: str, segredo: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        bytes.fromhex(segredo),
        hashlib.sha256,
    ).hexdigest()


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class KeyStore:
    """Armazenamento local de chaves, com apenas o HMAC do segredo."""

    def __init__(self, layout: ServerLayout, pepper: str | None = None):
        if pepper is not None and len(pepper) < 32:
            raise RemoteError("pepper curto: mínimo de 32 caracteres")
        self._pepper = pepper
        self._path = layout.keys_db
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute(SCHEMA)
        self._conn.commit()
        secure_db(self._path)

    def _require_pepper(self) -> str:
        if self._pepper is None:
            raise RemoteError("pepper obrigatório para emitir ou verificar chaves")
        return self._pepper

    def _secure(self) -> None:
        secure_db(self._path)

    def create(self, alias: str, ttl_days: int) -> IssuedKey:
        """Emite uma chave nova; o token não é recuperável depois."""
        validate_alias(alias)
        if ttl_days < 0:
            raise ValidationError("ttl_days deve ser >= 0")
        pepper = self._require_pepper()
        key_id = secrets.token_hex(KEY_ID_BYTES)
        segredo = secrets.token_hex(SECRET_BYTES)
        agora = datetime.now(UTC)
        expira = agora + timedelta(days=ttl_days)
        token = f"{KEY_PREFIX}{key_id}_{segredo}"

        with self._lock:
            self._conn.execute(
                "INSERT INTO keys (key_id, alias, secret_hmac, created_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (key_id, alias, _hmac_secret(pepper, segredo), iso(agora), iso(expira)),
            )
            self._conn.commit()
            self._secure()

        return IssuedKey(
            key_id=key_id,
            alias=alias,
            token=token,
            created_at=iso(agora),
            expires_at=iso(expira),
        )

    def verify(self, token: str) -> Principal | None:
        """Devolve o principal quando o token é válido, não expirou e não foi revogado."""
        partes = parse_token(token)
        if partes is None:
            return None
        key_id, segredo = partes
        pepper = self._require_pepper()

        with self._lock:
            linha = self._conn.execute(
                "SELECT alias, secret_hmac, expires_at, revoked_at, last_used_at "
                "FROM keys WHERE key_id = ?",
                (key_id,),
            ).fetchone()
            if linha is None or linha["revoked_at"] is not None:
                return None
            try:
                expira = _parse_timestamp(linha["expires_at"])
            except ValueError:
                return None
            if expira <= datetime.now(UTC):
                return None
            if not hmac.compare_digest(_hmac_secret(pepper, segredo), linha["secret_hmac"]):
                return None
            self._touch_locked(key_id, linha["last_used_at"])
            return Principal(
                key_id=key_id,
                alias=linha["alias"],
                expires_at=linha["expires_at"],
            )

    def _touch_locked(self, key_id: str, last_used_at: str | None) -> None:
        agora = datetime.now(UTC)
        if last_used_at is not None:
            try:
                if (
                    agora - _parse_timestamp(last_used_at)
                ).total_seconds() < TOUCH_INTERVAL_SECONDS:
                    return
            except ValueError:
                pass
        self._conn.execute(
            "UPDATE keys SET last_used_at = ? WHERE key_id = ?",
            (iso(agora), key_id),
        )
        self._conn.commit()
        self._secure()

    def list(self) -> list[KeyRecord]:
        """Lista as chaves sem expor o segredo."""
        with self._lock:
            linhas = self._conn.execute(
                "SELECT key_id, alias, created_at, expires_at, revoked_at, last_used_at "
                "FROM keys ORDER BY created_at DESC, key_id"
            ).fetchall()
        return [
            KeyRecord(
                key_id=linha["key_id"],
                alias=linha["alias"],
                created_at=linha["created_at"],
                expires_at=linha["expires_at"],
                revoked_at=linha["revoked_at"],
                last_used_at=linha["last_used_at"],
            )
            for linha in linhas
        ]

    def revoke(self, key_id: str) -> bool:
        """Revoga uma chave; devolve ``False`` se não havia o que revogar."""
        with self._lock:
            cursor = self._conn.execute(
                "UPDATE keys SET revoked_at = ? WHERE key_id = ? AND revoked_at IS NULL",
                (utc_now(), key_id),
            )
            self._conn.commit()
            self._secure()
            return cursor.rowcount > 0

    def close(self) -> None:
        with self._lock:
            self._conn.close()
