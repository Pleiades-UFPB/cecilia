"""Testes do registro de auditoria e da consulta de acessos."""

import pytest

from cecilia.remote.audit import AuditEntry, AuditLog, parse_since
from cecilia.remote.errors import ValidationError


def _entrada(**mudancas) -> AuditEntry:
    dados = {
        "request_id": "req-1",
        "action": "blob",
        "status": 200,
        "bytes_sent": 1234,
        "duration_ms": 7,
        "alias": "luan",
        "key_id": "a" * 16,
        "dataset": "gaia_teste",
        "version": "v1",
        "file": "gaia.parquet",
        "blob": "b" * 64,
        "client_ip": "100.64.0.10",
        "user_agent": "pytest",
    }
    dados.update(mudancas)
    return AuditEntry(**dados)


def test_registra_e_consulta(layout):
    audit = AuditLog(layout)
    audit.record(_entrada())

    registros = audit.recent()
    assert len(registros) == 1
    assert registros[0]["alias"] == "luan"
    assert registros[0]["file"] == "gaia.parquet"
    assert registros[0]["bytes_sent"] == 1234
    assert registros[0]["status"] == 200


def test_filtra_por_alias_e_periodo(layout):
    audit = AuditLog(layout)
    audit.record(_entrada(alias="luan", ts="2020-01-01T00:00:00Z"))
    audit.record(_entrada(alias="maria"))

    assert [item["alias"] for item in audit.recent(alias="maria")] == ["maria"]
    assert audit.recent(alias="luan", since=parse_since("7d")) == []
    assert len(audit.recent(since=parse_since("7d"))) == 1


def test_parse_since():
    assert parse_since("24h") > parse_since("7d")
    assert parse_since("2026-11-01").endswith("Z")
    with pytest.raises(ValidationError):
        parse_since("ontem")


def test_prune_remove_antigos(layout):
    audit = AuditLog(layout)
    audit.record(_entrada(ts="2020-01-01T00:00:00Z"))
    audit.record(_entrada())

    assert audit.prune(90) == 1
    assert len(audit.recent()) == 1


def test_banco_com_permissao_restrita(layout):
    AuditLog(layout).record(_entrada())
    assert (layout.audit_db.stat().st_mode & 0o777) == 0o600
