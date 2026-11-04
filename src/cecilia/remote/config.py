"""Configuração local do cliente remoto."""

from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from .errors import ClientError

CONFIG_FILE = "config.toml"
CREDENTIALS_FILE = "credentials.toml"
INSECURE_ENV = "CECILIA_INSECURE"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class ClientSettings:
    """Configuração resolvida para uma execução do cliente."""

    url: str
    key: str
    alias: str | None
    config_dir: Path
    cache_dir: Path
    data_dir: Path


def config_dir() -> Path:
    """Diretório de configuração, respeitando XDG e `CECILIA_CONFIG_DIR`."""
    explicito = os.environ.get("CECILIA_CONFIG_DIR")
    if explicito:
        return Path(explicito).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "cecilia"


def cache_dir() -> Path:
    """Diretório de cache de blobs, respeitando XDG e `CECILIA_CACHE_DIR`."""
    explicito = os.environ.get("CECILIA_CACHE_DIR")
    if explicito:
        return Path(explicito).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "cecilia"


def data_dir() -> Path:
    """Diretório de destino dos dados, com `CECILIA_DATA_DIR` opcional."""
    explicito = os.environ.get("CECILIA_DATA_DIR")
    if explicito:
        return Path(explicito).expanduser()
    return Path.cwd() / "data" / "raw"


def normalize_url(value: str) -> str:
    """Valida esquema e host; HTTP só é aceito em localhost ou com opt-in explícito."""
    endereco = value.strip().rstrip("/")
    parsed = urlparse(endereco)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ClientError("URL inválida: use https://host[:porta]")
    if parsed.scheme == "http" and not _inseguro() and parsed.hostname not in LOCAL_HOSTS:
        raise ClientError(
            "HTTP sem TLS só é aceito em localhost; "
            "use https ou defina CECILIA_INSECURE=1 para testes"
        )
    return endereco


def _inseguro() -> bool:
    return os.environ.get(INSECURE_ENV, "").strip().lower() in {"1", "true", "sim", "yes"}


def save_login(
    url: str,
    key: str,
    alias: str | None,
    directory: Path | None = None,
) -> Path:
    """Grava config e credenciais com permissões restritas."""
    endereco = normalize_url(url)
    chave = key.strip()
    if not chave.startswith("ck_"):
        raise ClientError("chave de API inválida: deve começar com 'ck_'")

    destino = Path(directory) if directory is not None else config_dir()
    destino.mkdir(parents=True, exist_ok=True)
    destino.chmod(0o700)

    linhas = ["[remote]", f"url = {json.dumps(endereco)}"]
    if alias:
        linhas.append(f"alias = {json.dumps(alias.strip())}")
    _write_private(destino / CONFIG_FILE, "\n".join(linhas) + "\n")
    _write_private(
        destino / CREDENTIALS_FILE,
        "[remote]\n" + f"key = {json.dumps(chave)}\n",
    )
    return destino


def load_settings(directory: Path | None = None) -> ClientSettings:
    """Resolve URL, chave, alias e diretórios a partir de arquivos e ambiente."""
    base = Path(directory) if directory is not None else config_dir()
    config = _read_toml(base / CONFIG_FILE)
    credenciais = _read_toml(base / CREDENTIALS_FILE)
    remoto = config.get("remote", {})
    segredo = credenciais.get("remote", {})

    url = os.environ.get("CECILIA_API_URL") or remoto.get("url")
    key = os.environ.get("CECILIA_API_KEY") or segredo.get("key")
    alias = remoto.get("alias")

    if not url:
        raise ClientError("servidor não configurado; rode `cecilia remote login --url ...`")
    if not key:
        raise ClientError("chave não configurada; rode `cecilia remote login --url ...`")
    if not os.environ.get("CECILIA_API_KEY"):
        _check_credentials_permissions(base / CREDENTIALS_FILE)

    return ClientSettings(
        url=normalize_url(str(url)),
        key=str(key),
        alias=str(alias) if alias else None,
        config_dir=base,
        cache_dir=cache_dir(),
        data_dir=data_dir(),
    )


def _read_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as arquivo:
            return tomllib.load(arquivo)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ClientError(f"não foi possível ler {path}: {exc}") from exc


def _check_credentials_permissions(path: Path) -> None:
    if not path.is_file():
        return
    modo = path.stat().st_mode & 0o777
    if modo & 0o077:
        raise ClientError(f"permissões de {path} são {oct(modo)}; restrinja com `chmod 600`")


def _write_private(path: Path, conteudo: str) -> None:
    temporario = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporario.write_text(conteudo, encoding="utf-8")
        temporario.chmod(0o600)
        os.replace(temporario, path)
    finally:
        temporario.unlink(missing_ok=True)
