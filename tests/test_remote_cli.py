"""Testes de ponta a ponta da CLI remota."""

import httpx
from typer.testing import CliRunner

import cecilia.remote.cli as remote_cli
from cecilia.cli import app
from cecilia.remote.client import RemoteClient

runner = CliRunner()
TOKEN = "ck_" + "a" * 16 + "_" + "b" * 64


def _ambiente(monkeypatch, servidor, tmp_path) -> None:
    monkeypatch.setenv("CECILIA_API_URL", "http://test")
    monkeypatch.setenv("CECILIA_API_KEY", servidor.token)
    monkeypatch.setenv("CECILIA_INSECURE", "1")
    monkeypatch.setenv("CECILIA_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("CECILIA_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("CECILIA_CONFIG_DIR", str(tmp_path / "conf"))


def _abrir(servidor):
    def _factory(settings):
        http = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=servidor.app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {servidor.token}"},
        )
        return RemoteClient(http, "http://test")

    return _factory


def test_cli_list_e_manifest(servidor_remoto, tmp_path, monkeypatch):
    _ambiente(monkeypatch, servidor_remoto, tmp_path)
    monkeypatch.setattr(remote_cli, "_abrir_cliente", _abrir(servidor_remoto))

    listagem = runner.invoke(app, ["remote", "list"])
    assert listagem.exit_code == 0, listagem.output
    assert "gaia_teste" in listagem.output

    manifesto = runner.invoke(app, ["remote", "manifest", "gaia_teste"])
    assert manifesto.exit_code == 0, manifesto.output
    assert "gaia.parquet" in manifesto.output


def test_cli_sync_e_verify(servidor_remoto, tmp_path, monkeypatch):
    _ambiente(monkeypatch, servidor_remoto, tmp_path)
    monkeypatch.setattr(remote_cli, "_abrir_cliente", _abrir(servidor_remoto))

    sincronizado = runner.invoke(
        app,
        [
            "remote",
            "sync",
            "gaia_teste",
            "--version",
            "v1",
            "--connections",
            "1",
            "--jobs",
            "1",
        ],
    )
    assert sincronizado.exit_code == 0, sincronizado.output
    assert (tmp_path / "data" / "gaia_teste" / "v1" / "gaia.parquet").is_file()

    verificado = runner.invoke(app, ["remote", "verify"])
    assert verificado.exit_code == 0, verificado.output


def test_cli_login_grava_credenciais(tmp_path, monkeypatch):
    async def _whoami(url, key):
        return {"alias": "luan"}

    monkeypatch.setattr(remote_cli, "_whoami_login", _whoami)
    monkeypatch.delenv("CECILIA_API_URL", raising=False)
    monkeypatch.delenv("CECILIA_API_KEY", raising=False)

    resultado = runner.invoke(
        app,
        [
            "remote",
            "login",
            "--url",
            "https://host.tailnet.ts.net",
            "--config-dir",
            str(tmp_path / "conf"),
        ],
        input=TOKEN + "\n",
    )

    assert resultado.exit_code == 0, resultado.output
    credenciais = tmp_path / "conf" / "credentials.toml"
    config = tmp_path / "conf" / "config.toml"
    assert credenciais.is_file()
    assert config.is_file()
    assert credenciais.stat().st_mode & 0o777 == 0o600


def test_cli_doctor(servidor_remoto, tmp_path, monkeypatch):
    _ambiente(monkeypatch, servidor_remoto, tmp_path)
    monkeypatch.setattr(remote_cli, "_abrir_cliente", _abrir(servidor_remoto))

    resultado = runner.invoke(app, ["remote", "doctor"])

    assert resultado.exit_code == 0, resultado.output
    assert "alias: luan" in resultado.output
