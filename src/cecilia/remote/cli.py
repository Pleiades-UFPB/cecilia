"""CLI do cliente remoto: login, listagem, sync e diagnóstico."""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Annotated, NoReturn

import httpx
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from .client import USER_AGENT, RemoteClient, raise_for_status
from .config import (
    ClientSettings,
    cache_dir,
    data_dir,
    load_settings,
    normalize_url,
    save_login,
)
from .errors import ClientError, RemoteError
from .format import human_bytes
from .sync import (
    SyncResult,
    get_file,
    latest_version,
    manifest_rows,
    state_files,
    sync_dataset,
    verify_data,
)

remote_app = typer.Typer(no_args_is_help=True, help="Cliente de dados remotos.")
console = Console()


def _fail(exc: RemoteError) -> NoReturn:
    typer.echo(f"erro: {exc}", err=True)
    raise typer.Exit(code=1)


def _settings() -> ClientSettings:
    try:
        return load_settings()
    except RemoteError as exc:
        _fail(exc)


def _abrir_cliente(settings: ClientSettings) -> RemoteClient:
    return RemoteClient.from_settings(settings)


async def _whoami_login(url: str, key: str) -> dict:
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": USER_AGENT,
    }
    async with httpx.AsyncClient(
        base_url=url,
        headers=headers,
        timeout=httpx.Timeout(10.0),
        follow_redirects=False,
    ) as http:
        resposta = await http.get("/v1/whoami")
        raise_for_status(resposta)
        return resposta.json()


async def _catalogo(settings: ClientSettings) -> dict:
    cliente = _abrir_cliente(settings)
    try:
        return await cliente.catalog()
    finally:
        await cliente.close()


async def _manifesto(
    settings: ClientSettings,
    dataset: str,
    version: str | None,
) -> dict:
    cliente = _abrir_cliente(settings)
    try:
        versao = version
        if versao is None:
            versao = latest_version(await cliente.catalog(), dataset)
        return await cliente.manifest(dataset, versao)
    finally:
        await cliente.close()


async def _sincronizar(
    settings: ClientSettings,
    dataset: str,
    version: str | None,
    destino: Path,
    cache: Path,
    jobs: int,
    connections: int,
    force: bool,
) -> tuple[SyncResult, str | None]:
    cliente = _abrir_cliente(settings)
    try:
        quem = await cliente.whoami()
        alias = quem.get("alias")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            console=Console(stderr=True),
        ) as progress:
            tarefa = progress.add_task(dataset, total=None)

            def iniciar(total: int) -> None:
                progress.update(tarefa, total=total)

            def avancar(quantidade: int) -> None:
                progress.update(tarefa, advance=quantidade)

            resultado = await sync_dataset(
                cliente,
                dataset,
                version,
                data_dir=destino,
                cache_dir=cache,
                jobs=jobs,
                connections=connections,
                force=force,
                alias=alias,
                on_manifest=iniciar,
                on_progress=avancar,
            )
            progress.update(tarefa, completed=resultado.total_bytes)
        return resultado, alias
    finally:
        await cliente.close()


async def _baixar_arquivo(
    settings: ClientSettings,
    dataset: str,
    caminho: str,
    version: str | None,
    out: Path | None,
    force: bool,
) -> Path:
    cliente = _abrir_cliente(settings)
    try:
        return await get_file(
            cliente,
            dataset,
            caminho,
            version=version,
            data_dir=settings.data_dir,
            cache_dir=settings.cache_dir,
            out=out,
            force=force,
        )
    finally:
        await cliente.close()


async def _diagnostico(settings: ClientSettings, dataset: str | None) -> dict[str, str]:
    cliente = _abrir_cliente(settings)
    try:
        inicio = time.perf_counter()
        quem = await cliente.whoami()
        tempo_whoami = (time.perf_counter() - inicio) * 1000

        inicio = time.perf_counter()
        catalogo = await cliente.catalog()
        tempo_catalogo = (time.perf_counter() - inicio) * 1000

        dados = {
            "url": settings.url,
            "alias": str(quem.get("alias")),
            "expira": str(quem.get("expires_at")),
            "whoami_ms": f"{tempo_whoami:.0f}",
            "catalog_ms": f"{tempo_catalogo:.0f}",
        }
        if dataset:
            versao = latest_version(catalogo, dataset)
            manifesto = await cliente.manifest(dataset, versao)
            arquivos = manifesto.get("files", [])
            if not arquivos:
                raise ClientError(f"manifesto sem arquivos: {dataset}")
            entrada = min(arquivos, key=lambda item: int(item["bytes"]))
            tamanho = min(int(entrada["bytes"]), 1024 * 1024)
            if tamanho:
                inicio = time.perf_counter()
                resposta = await cliente.http.get(
                    f"/v1/blobs/{entrada['blob']}",
                    headers={"Range": f"bytes=0-{tamanho - 1}"},
                )
                raise_for_status(resposta)
                duracao = max(time.perf_counter() - inicio, 1e-9)
                dados["throughput_mb_s"] = f"{len(resposta.content) / duracao / 1e6:.1f}"
                dados["amostra_bytes"] = str(len(resposta.content))
        return dados
    finally:
        await cliente.close()


@remote_app.command("login")
def login_command(
    url: Annotated[str | None, typer.Option("--url", help="URL do servidor.")] = None,
    alias: Annotated[str | None, typer.Option("--alias", help="Apelido para o log.")] = None,
    diretorio: Annotated[
        Path | None,
        typer.Option("--config-dir", help="Diretório de configuração."),
    ] = None,
) -> None:
    """Valida a chave em `/v1/whoami` e grava a configuração local."""
    endereco = url or os.environ.get("CECILIA_API_URL")
    if not endereco:
        _fail(ClientError("informe --url https://host..."))
    try:
        endereco = normalize_url(endereco)
    except RemoteError as exc:
        _fail(exc)

    chave = typer.prompt("Chave de API", hide_input=True).strip()
    if not chave:
        _fail(ClientError("chave vazia"))

    try:
        quem = asyncio.run(_whoami_login(endereco, chave))
    except RemoteError as exc:
        _fail(exc)
    except httpx.HTTPError as exc:
        _fail(ClientError(f"não foi possível conectar: {exc}"))

    apelido = alias or quem.get("alias")
    try:
        destino = save_login(endereco, chave, apelido, diretorio)
    except RemoteError as exc:
        _fail(exc)

    typer.echo(f"conectado como {apelido} em {endereco}")
    typer.echo(f"configuração: {destino / 'config.toml'}")
    typer.echo(f"credenciais: {destino / 'credentials.toml'}")


@remote_app.command("list")
def list_command(
    json_output: Annotated[bool, typer.Option("--json", help="Saída JSON.")] = False,
) -> None:
    """Lista datasets e versões disponíveis."""
    settings = _settings()
    try:
        catalogo = asyncio.run(_catalogo(settings))
    except RemoteError as exc:
        _fail(exc)
    except httpx.HTTPError as exc:
        _fail(ClientError(f"falha de rede: {exc}"))

    if json_output:
        typer.echo(json.dumps(catalogo, indent=2, ensure_ascii=False))
        return

    tabela = Table(title="Datasets disponíveis")
    for coluna in ("DATASET", "VERSÃO", "ARQUIVOS", "LINHAS", "BYTES", "HASH"):
        tabela.add_column(coluna)
    for item in catalogo.get("datasets", []):
        for versao in item.get("versions", []):
            tabela.add_row(
                item["name"],
                versao["version"],
                str(versao.get("files", 0)),
                str(versao.get("rows", 0)),
                human_bytes(int(versao.get("bytes", 0))),
                str(versao.get("manifest", ""))[:12],
            )
    console.print(tabela)


@remote_app.command("manifest")
def manifest_command(
    dataset: Annotated[str, typer.Argument(help="Nome do dataset.")],
    version: Annotated[
        str | None,
        typer.Option("--version", help="Versão; padrão: a mais recente."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Saída JSON.")] = False,
) -> None:
    """Mostra os arquivos de uma versão."""
    settings = _settings()
    try:
        manifesto = asyncio.run(_manifesto(settings, dataset, version))
    except RemoteError as exc:
        _fail(exc)
    except httpx.HTTPError as exc:
        _fail(ClientError(f"falha de rede: {exc}"))

    if json_output:
        typer.echo(json.dumps(manifesto, indent=2, ensure_ascii=False))
        return

    tabela = Table(title=f"{dataset}@{manifesto.get('version')}")
    for coluna in ("CAMINHO", "BYTES", "LINHAS", "BLOB"):
        tabela.add_column(coluna)
    for entry in manifesto.get("files", []):
        tabela.add_row(
            entry["path"],
            human_bytes(int(entry["bytes"])),
            str(entry.get("rows", 0)),
            str(entry["blob"])[:12],
        )
    console.print(tabela)


@remote_app.command("sync")
def sync_command(
    dataset: Annotated[str, typer.Argument(help="Nome do dataset.")],
    version: Annotated[
        str | None,
        typer.Option("--version", help="Versão; padrão: a mais recente."),
    ] = None,
    out: Annotated[Path | None, typer.Option("--out", help="Diretório de dados.")] = None,
    jobs: Annotated[int, typer.Option("--jobs", help="Blobs simultâneos.")] = 4,
    connections: Annotated[
        int,
        typer.Option("--connections", help="Conexões HTTP simultâneas."),
    ] = 4,
    force: Annotated[bool, typer.Option("--force", help="Rebaixa mesmo em cache.")] = False,
) -> None:
    """Baixa e materializa uma versão em `data/raw`."""
    settings = _settings()
    destino = out or settings.data_dir
    try:
        resultado, alias = asyncio.run(
            _sincronizar(
                settings,
                dataset,
                version,
                destino,
                settings.cache_dir,
                jobs,
                connections,
                force,
            )
        )
    except RemoteError as exc:
        _fail(exc)
    except httpx.HTTPError as exc:
        _fail(ClientError(f"falha de rede: {exc}"))

    typer.echo(
        f"sincronizado {resultado.dataset}@{resultado.version}: "
        f"{resultado.downloaded} baixado(s), {resultado.reused} reaproveitado(s), "
        f"{human_bytes(resultado.total_bytes)}"
    )
    typer.echo(f"dados: {resultado.data_path}")
    for linha in manifest_rows(resultado, alias):
        typer.echo(linha)


@remote_app.command("get")
def get_command(
    dataset: Annotated[str, typer.Argument(help="Nome do dataset.")],
    file: Annotated[str, typer.Option("--file", help="Caminho lógico no manifesto.")],
    version: Annotated[
        str | None,
        typer.Option("--version", help="Versão; padrão: a mais recente."),
    ] = None,
    out: Annotated[
        Path | None, typer.Option("--out", help="Arquivo ou diretório de saída.")
    ] = None,
    force: Annotated[bool, typer.Option("--force", help="Rebaixa mesmo em cache.")] = False,
) -> None:
    """Baixa um único arquivo lógico."""
    settings = _settings()
    try:
        caminho = asyncio.run(_baixar_arquivo(settings, dataset, file, version, out, force))
    except RemoteError as exc:
        _fail(exc)
    except httpx.HTTPError as exc:
        _fail(ClientError(f"falha de rede: {exc}"))
    typer.echo(str(caminho))


@remote_app.command("verify")
def verify_command(
    quick: Annotated[bool, typer.Option("--quick", help="Confere só tamanho.")] = False,
    diretorio_dados: Annotated[
        Path | None,
        typer.Option("--data-dir", help="Diretório de dados."),
    ] = None,
    diretorio_cache: Annotated[
        Path | None,
        typer.Option("--cache-dir", help="Diretório de cache."),
    ] = None,
) -> None:
    """Confere tamanho e SHA-256 dos arquivos sincronizados."""
    dados = diretorio_dados or data_dir()
    cache = diretorio_cache or cache_dir()
    estados = state_files(dados)
    if not estados:
        typer.echo(f"nada sincronizado em {dados}")
        return

    problemas = verify_data(dados, cache, quick=quick)
    if not problemas:
        typer.echo(f"ok: {len(estados)} dataset(s) verificado(s)")
        return
    for problema in problemas:
        typer.echo(problema, err=True)
    typer.echo(f"{len(problemas)} problema(s) encontrado(s)", err=True)
    raise typer.Exit(code=1)


@remote_app.command("doctor")
def doctor_command(
    dataset: Annotated[
        str | None,
        typer.Option("--dataset", help="Mede throughput deste dataset."),
    ] = None,
) -> None:
    """Diagnostica autenticação, latência e throughput."""
    settings = _settings()
    try:
        dados = asyncio.run(_diagnostico(settings, dataset))
    except RemoteError as exc:
        _fail(exc)
    except httpx.HTTPError as exc:
        _fail(ClientError(f"falha de rede: {exc}"))
    for chave, valor in dados.items():
        typer.echo(f"{chave}: {valor}")
