"""Testes da CLI local de chaves e de consulta da auditoria."""

from typer.testing import CliRunner

from cecilia.cli import app
from cecilia.remote.audit import AuditEntry, AuditLog
from cecilia.remote.auth import KeyStore
from cecilia.remote.layout import ServerLayout

PEPPER = "p" * 48
runner = CliRunner()


def _token(saida: str) -> str:
    for linha in saida.splitlines():
        if linha.startswith("token: "):
            return linha.removeprefix("token: ").strip()
    raise AssertionError("token não encontrado na saída")


def test_cli_cria_lista_e_revoga(tmp_path, monkeypatch):
    monkeypatch.setenv("CECILIA_KEY_PEPPER", PEPPER)
    raiz = tmp_path / "srv"

    criada = runner.invoke(
        app,
        ["admin", "key", "create", "--alias", "luan", "--root", str(raiz)],
    )
    assert criada.exit_code == 0, criada.output
    token = _token(criada.output)
    assert KeyStore(ServerLayout(raiz), PEPPER).verify(token) is not None

    listada = runner.invoke(app, ["admin", "key", "list", "--root", str(raiz)])
    assert listada.exit_code == 0
    assert "luan" in listada.output

    key_id = token.split("_")[1]
    revogada = runner.invoke(
        app,
        ["admin", "key", "revoke", key_id, "--root", str(raiz)],
    )
    assert revogada.exit_code == 0
    assert KeyStore(ServerLayout(raiz), PEPPER).verify(token) is None


def test_cli_sem_pepper(tmp_path, monkeypatch):
    monkeypatch.delenv("CECILIA_KEY_PEPPER", raising=False)

    resultado = runner.invoke(
        app,
        ["admin", "key", "create", "--alias", "luan", "--root", str(tmp_path / "srv")],
    )
    assert resultado.exit_code == 1


def test_cli_log(tmp_path):
    layout = ServerLayout(tmp_path / "srv")
    AuditLog(layout).record(
        AuditEntry(
            request_id="req-1",
            action="blob",
            status=200,
            bytes_sent=10,
            duration_ms=1,
            alias="luan",
            dataset="gaia_teste",
            file="gaia.parquet",
        )
    )

    resultado = runner.invoke(
        app,
        ["admin", "log", "--since", "7d", "--root", str(layout.root)],
    )
    assert resultado.exit_code == 0
    assert "luan" in resultado.output
    assert "gaia.parquet" in resultado.output
