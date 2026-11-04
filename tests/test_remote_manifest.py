"""Testes do hash, do manifesto e da validação de nomes e caminhos."""

import pytest

from cecilia.remote.errors import ValidationError
from cecilia.remote.hashing import sha256_file
from cecilia.remote.layout import ServerLayout, validate_relpath
from cecilia.remote.manifest import FileEntry, Manifest, load_manifest

BLOB = "a" * 64


def _manifesto(**mudancas: object) -> Manifest:
    dados = {
        "dataset": "gaia_teste",
        "version": "v1",
        "created_at": "2026-11-04T00:00:00Z",
        "description": "teste",
        "license": "MIT",
        "attribution": "",
        "provenance": {"source": "Gaia DR3"},
        "files": (FileEntry(path="gaia.parquet", blob=BLOB, bytes=10, rows=2),),
    }
    dados.update(mudancas)
    return Manifest(**dados)


def test_sha256_de_arquivo_conhecido(tmp_path):
    arquivo = tmp_path / "abc.txt"
    arquivo.write_bytes(b"abc")
    assert (
        sha256_file(arquivo) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_manifesto_ida_e_volta():
    original = _manifesto()
    reconstruido = Manifest.from_dict(original.to_dict())
    assert reconstruido == original
    assert reconstruido.digest() == original.digest()


def test_manifesto_sem_campo_obrigatorio():
    dados = _manifesto().to_dict()
    del dados["dataset"]
    with pytest.raises(ValidationError):
        Manifest.from_dict(dados)


def test_manifesto_com_caminho_duplicado():
    dados = _manifesto().to_dict()
    dados["files"].append(dict(dados["files"][0]))
    with pytest.raises(ValidationError):
        Manifest.from_dict(dados)


@pytest.mark.parametrize(
    "caminho",
    [
        "../x.parquet",
        "/abs.parquet",
        "a/../../b.parquet",
        "a\\b.parquet",
        "a//b.parquet",
        "",
    ],
)
def test_caminho_invalido(caminho):
    with pytest.raises(ValidationError):
        validate_relpath(caminho)


def test_caminho_valido():
    assert validate_relpath("sub/gaia.parquet") == "sub/gaia.parquet"


def test_layout_usa_variavel_de_ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("CECILIA_SERVER_ROOT", str(tmp_path / "srv"))
    assert ServerLayout.resolve().root == (tmp_path / "srv").resolve()


def test_load_manifest_corrompido(tmp_path):
    caminho = tmp_path / "manifest.json"
    caminho.write_text("{", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_manifest(caminho)
