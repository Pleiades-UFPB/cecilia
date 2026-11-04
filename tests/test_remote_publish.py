"""Testes da publicação atômica e do catálogo."""

import json
import shutil

import pytest

from cecilia.remote.errors import PublishError, ValidationError
from cecilia.remote.hashing import sha256_file
from cecilia.remote.manifest import load_manifest
from cecilia.remote.publish import publish


def _fonte(gravar_parquet, tmp_path):
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1, 2, 3])
    gravar_parquet(origem / "sub" / "lamost.parquet", [4, 5])
    (origem / "ignorar.txt").write_text("não é parquet", encoding="utf-8")
    return origem


def test_publica_manifesto_e_catalogo(layout, gravar_parquet, tmp_path):
    resultado = publish(
        layout,
        _fonte(gravar_parquet, tmp_path),
        "gaia_teste",
        "v1",
        description="teste",
        provenance={"source": "Gaia DR3"},
    )

    assert resultado.copied == 2
    assert resultado.reused == 0
    assert len(resultado.manifest.files) == 2

    manifesto = load_manifest(layout.manifest_path("gaia_teste", "v1"))
    por_caminho = {entrada.path: entrada for entrada in manifesto.files}
    assert set(por_caminho) == {"gaia.parquet", "sub/lamost.parquet"}

    gaia = por_caminho["gaia.parquet"]
    blob = layout.blobs / gaia.blob
    assert gaia.rows == 3
    assert gaia.bytes == blob.stat().st_size
    assert sha256_file(blob) == gaia.blob
    assert [nome for nome, _ in gaia.schema] == ["source_id", "ra"]

    catalogo = json.loads(layout.catalog.read_text(encoding="utf-8"))
    assert catalogo["datasets"][0]["name"] == "gaia_teste"
    versao = catalogo["datasets"][0]["versions"][0]
    assert versao["version"] == "v1"
    assert versao["files"] == 2
    assert versao["bytes"] == sum(entrada.bytes for entrada in manifesto.files)
    assert versao["manifest"] == manifesto.digest()


def test_deduplica_conteudo_entre_datasets(layout, gravar_parquet, tmp_path):
    origem_a = _fonte(gravar_parquet, tmp_path)
    primeiro = publish(layout, origem_a, "gaia_a", "v1")
    assert primeiro.copied == 2

    origem_b = tmp_path / "entrada_b"
    origem_b.mkdir()
    shutil.copyfile(origem_a / "gaia.parquet", origem_b / "copia.parquet")
    segundo = publish(layout, origem_b, "gaia_b", "v1")

    assert segundo.copied == 0
    assert segundo.reused == 1
    assert len(list(layout.blobs.iterdir())) == 2

    catalogo = json.loads(layout.catalog.read_text(encoding="utf-8"))
    assert [item["name"] for item in catalogo["datasets"]] == ["gaia_a", "gaia_b"]


def test_recusa_sobrescrever_versao(layout, gravar_parquet, tmp_path):
    origem = _fonte(gravar_parquet, tmp_path)
    publish(layout, origem, "gaia_teste", "v1")
    antes = load_manifest(layout.manifest_path("gaia_teste", "v1")).digest()

    with pytest.raises(PublishError):
        publish(layout, origem, "gaia_teste", "v1")

    depois = load_manifest(layout.manifest_path("gaia_teste", "v1")).digest()
    assert depois == antes


def test_fonte_sem_parquet(layout, tmp_path):
    origem = tmp_path / "vazia"
    origem.mkdir()
    (origem / "leiame.txt").write_text("x", encoding="utf-8")
    with pytest.raises(PublishError):
        publish(layout, origem, "gaia_teste", "v1")


@pytest.mark.parametrize(
    ("dataset", "version"),
    [
        ("Gaia", "v1"),
        ("gaia teste", "v1"),
        ("gaia_teste", "1"),
        ("gaia_teste", "v1.2"),
    ],
)
def test_rejeita_nomes_invalidos(layout, gravar_parquet, tmp_path, dataset, version):
    with pytest.raises(ValidationError):
        publish(layout, _fonte(gravar_parquet, tmp_path), dataset, version)


def test_v2_supersedes_mantem_v1(layout, gravar_parquet, tmp_path):
    origem = _fonte(gravar_parquet, tmp_path)
    publish(layout, origem, "gaia_teste", "v1")
    publish(layout, origem, "gaia_teste", "v2", supersedes="v1")

    assert layout.manifest_path("gaia_teste", "v1").is_file()
    catalogo = json.loads(layout.catalog.read_text(encoding="utf-8"))
    versoes = {versao["version"]: versao for versao in catalogo["datasets"][0]["versions"]}
    assert versoes["v2"]["supersedes"] == "v1"
    assert versoes["v1"]["supersedes"] is None
