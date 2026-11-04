"""Testes da configuração local do cliente."""

import pytest

from cecilia.remote.config import load_settings, normalize_url, save_login
from cecilia.remote.errors import ClientError

TOKEN = "ck_" + "a" * 16 + "_" + "b" * 64
OUTRO = "ck_" + "c" * 16 + "_" + "d" * 64


def _limpar(monkeypatch) -> None:
    for nome in (
        "CECILIA_API_URL",
        "CECILIA_API_KEY",
        "CECILIA_INSECURE",
        "CECILIA_CONFIG_DIR",
        "CECILIA_DATA_DIR",
        "CECILIA_CACHE_DIR",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
    ):
        monkeypatch.delenv(nome, raising=False)


def test_salva_e_carrega_com_permissao_restrita(tmp_path, monkeypatch):
    _limpar(monkeypatch)
    destino = save_login("https://host.tailnet.ts.net/", TOKEN, "luan", tmp_path / "conf")

    assert (destino / "config.toml").stat().st_mode & 0o777 == 0o600
    assert (destino / "credentials.toml").stat().st_mode & 0o777 == 0o600

    settings = load_settings(tmp_path / "conf")
    assert settings.url == "https://host.tailnet.ts.net"
    assert settings.key == TOKEN
    assert settings.alias == "luan"


def test_ambiente_sobrepoe_arquivos(tmp_path, monkeypatch):
    _limpar(monkeypatch)
    save_login("https://a.tailnet.ts.net", TOKEN, "luan", tmp_path)

    monkeypatch.setenv("CECILIA_API_URL", "https://b.tailnet.ts.net")
    monkeypatch.setenv("CECILIA_API_KEY", OUTRO)
    settings = load_settings(tmp_path)

    assert settings.url == "https://b.tailnet.ts.net"
    assert settings.key == OUTRO


def test_http_remoto_recusado(monkeypatch):
    _limpar(monkeypatch)
    with pytest.raises(ClientError):
        normalize_url("http://host.tailnet.ts.net")

    assert normalize_url("http://127.0.0.1:8000") == "http://127.0.0.1:8000"

    monkeypatch.setenv("CECILIA_INSECURE", "1")
    assert normalize_url("http://test") == "http://test"


def test_credenciais_com_permissao_aberta(tmp_path, monkeypatch):
    _limpar(monkeypatch)
    save_login("https://host.tailnet.ts.net", TOKEN, "luan", tmp_path)
    (tmp_path / "credentials.toml").chmod(0o644)

    with pytest.raises(ClientError):
        load_settings(tmp_path)


def test_sem_url_ou_chave(tmp_path, monkeypatch):
    _limpar(monkeypatch)
    with pytest.raises(ClientError):
        load_settings(tmp_path)


def test_url_invalida(tmp_path):
    with pytest.raises(ClientError):
        save_login("ftp://host", TOKEN, "luan", tmp_path)
    with pytest.raises(ClientError):
        save_login("https://host", "nao-e-chave", "luan", tmp_path)
