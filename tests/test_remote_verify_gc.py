"""Testes da verificação de integridade e da coleta de blobs órfãos."""

from cecilia.remote.gc import collect_garbage
from cecilia.remote.publish import publish
from cecilia.remote.verify import verify


def _publica(layout, gravar_parquet, tmp_path):
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1, 2, 3])
    return publish(layout, origem, "gaia_teste", "v1")


def test_verify_sem_problemas(layout, gravar_parquet, tmp_path):
    _publica(layout, gravar_parquet, tmp_path)
    assert verify(layout) == []


def test_verify_detecta_blob_corrompido(layout, gravar_parquet, tmp_path):
    _publica(layout, gravar_parquet, tmp_path)
    blob = next(layout.blobs.iterdir())
    blob.write_bytes(b"x" * blob.stat().st_size)

    problemas = verify(layout)
    assert any(problema.kind == "blob-hash" for problema in problemas)


def test_verify_detecta_catalogo_ausente(layout, gravar_parquet, tmp_path):
    _publica(layout, gravar_parquet, tmp_path)
    layout.catalog.unlink()

    problemas = verify(layout)
    assert any(problema.kind == "catalog" for problema in problemas)


def test_verify_deep_confere_linhas(layout, gravar_parquet, tmp_path):
    _publica(layout, gravar_parquet, tmp_path)
    assert verify(layout, deep=True) == []


def test_gc_dry_run_nao_remove_e_apply_remove(layout, gravar_parquet, tmp_path):
    _publica(layout, gravar_parquet, tmp_path)
    orfao = layout.blobs / ("f" * 64)
    orfao.write_bytes(b"lixo")

    encontrados = collect_garbage(layout)
    assert orfao in encontrados
    assert orfao.exists()

    removidos = collect_garbage(layout, apply=True)
    assert orfao in removidos
    assert not orfao.exists()
    assert len(list(layout.blobs.iterdir())) == 1


def test_gc_ignora_arquivos_que_nao_sao_hash(layout, gravar_parquet, tmp_path):
    _publica(layout, gravar_parquet, tmp_path)
    leiame = layout.blobs / "LEIAME.txt"
    leiame.write_text("não é blob", encoding="utf-8")

    assert leiame not in collect_garbage(layout)
    collect_garbage(layout, apply=True)
    assert leiame.exists()
