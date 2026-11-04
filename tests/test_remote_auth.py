"""Testes da emissão, verificação e revogação de chaves."""

import sqlite3

import pytest

from cecilia.remote.auth import KeyStore, parse_token
from cecilia.remote.errors import ValidationError

PEPPER = "p" * 48


def _store(layout) -> KeyStore:
    return KeyStore(layout, PEPPER)


def test_cria_e_verifica_chave(layout):
    emitida = _store(layout).create("luan", 90)

    assert emitida.token.startswith("ck_")
    principal = _store(layout).verify(emitida.token)
    assert principal is not None
    assert principal.alias == "luan"
    assert principal.key_id == emitida.key_id
    assert principal.expires_at == emitida.expires_at


def test_banco_guarda_apenas_hmac(layout):
    emitida = _store(layout).create("luan", 90)
    segredo = emitida.token.split("_")[2]

    with sqlite3.connect(layout.keys_db) as conexao:
        linha = conexao.execute("SELECT secret_hmac FROM keys").fetchone()

    assert linha is not None
    assert linha[0] != segredo
    assert len(linha[0]) == 64
    assert segredo not in layout.keys_db.read_text(encoding="latin-1")


def test_token_errado_e_formato_invalido(layout):
    store = _store(layout)
    emitida = store.create("luan", 90)
    key_id, segredo = emitida.token.removeprefix("ck_").split("_")
    errado = f"ck_{key_id}_{'0' * len(segredo)}"

    assert store.verify(errado) is None
    assert store.verify("nao-e-uma-chave") is None
    assert store.verify("") is None


@pytest.mark.parametrize(
    "token",
    [
        "ck_abc_def",
        "ck_" + "a" * 16 + "_" + "b" * 63,
        "xx_" + "a" * 16 + "_" + "b" * 64,
        "ck_" + "z" * 16 + "_" + "b" * 64,
    ],
)
def test_parse_token_invalido(token):
    assert parse_token(token) is None


def test_chave_expirada(layout):
    store = _store(layout)
    emitida = store.create("luan", 0)
    assert store.verify(emitida.token) is None


def test_chave_revogada(layout):
    store = _store(layout)
    emitida = store.create("luan", 90)
    assert store.revoke(emitida.key_id) is True
    assert store.verify(emitida.token) is None
    assert store.revoke(emitida.key_id) is False


def test_lista_sem_segredo(layout):
    store = _store(layout)
    store.create("luan", 90)
    store.create("maria", 90)

    chaves = store.list()
    assert {chave.alias for chave in chaves} == {"luan", "maria"}
    assert all(len(chave.key_id) == 16 for chave in chaves)
    assert all(not hasattr(chave, "secret_hmac") for chave in chaves)


def test_alias_invalido(layout):
    with pytest.raises(ValidationError):
        _store(layout).create("Luan Motta", 90)


def test_banco_com_permissao_restrita(layout):
    _store(layout).create("luan", 90)
    assert (layout.keys_db.stat().st_mode & 0o777) == 0o600
