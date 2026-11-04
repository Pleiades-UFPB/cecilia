"""Testes da CLI de administração do servidor."""

from typer.testing import CliRunner

from cecilia.cli import app

runner = CliRunner()


def test_cli_publica_e_verifica(tmp_path, gravar_parquet):
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1, 2, 3])
    raiz = tmp_path / "srv"

    resultado = runner.invoke(
        app,
        [
            "admin",
            "publish",
            str(origem),
            "--dataset",
            "gaia_teste",
            "--version",
            "v1",
            "--root",
            str(raiz),
        ],
    )
    assert resultado.exit_code == 0, resultado.output

    resultado = runner.invoke(app, ["admin", "verify", "--root", str(raiz)])
    assert resultado.exit_code == 0, resultado.output
    assert "ok" in resultado.output


def test_cli_falha_com_dataset_invalido(tmp_path, gravar_parquet):
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1])

    resultado = runner.invoke(
        app,
        [
            "admin",
            "publish",
            str(origem),
            "--dataset",
            "Gaia",
            "--root",
            str(tmp_path / "srv"),
        ],
    )
    assert resultado.exit_code == 1


def test_cli_gc_sem_apply_nao_remove(tmp_path, gravar_parquet):
    origem = tmp_path / "entrada"
    gravar_parquet(origem / "gaia.parquet", [1])
    raiz = tmp_path / "srv"
    runner.invoke(
        app,
        ["admin", "publish", str(origem), "--dataset", "gaia_teste", "--root", str(raiz)],
    )

    orfao = raiz / "blobs" / ("f" * 64)
    orfao.write_bytes(b"lixo")
    resultado = runner.invoke(app, ["admin", "gc", "--root", str(raiz)])

    assert resultado.exit_code == 0
    assert orfao.exists()
