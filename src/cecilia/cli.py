"""CLI do CECILIA: administração local do servidor de datasets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from .remote.audit import AuditLog, parse_since
from .remote.auth import KeyStore
from .remote.catalog import rebuild_catalog
from .remote.cli import remote_app
from .remote.errors import RemoteError
from .remote.format import human_bytes
from .remote.gc import collect_garbage
from .remote.layout import ServerLayout
from .remote.publish import publish
from .remote.settings import MIN_PEPPER_LENGTH, Settings
from .remote.verify import verify

app = typer.Typer(no_args_is_help=True, help="Ferramentas do projeto CECILIA.")
admin_app = typer.Typer(
    no_args_is_help=True,
    help="Administração local do servidor de datasets (rodar no servidor).",
)
app.add_typer(admin_app, name="admin")
app.add_typer(remote_app, name="remote")

RootOption = Annotated[
    Path | None,
    typer.Option(
        "--root",
        envvar="CECILIA_SERVER_ROOT",
        help="Raiz do servidor (padrão: /srv/cecilia).",
    ),
]

key_app = typer.Typer(
    no_args_is_help=True,
    help="Emissão, listagem e revogação de chaves.",
)
admin_app.add_typer(key_app, name="key")


def _layout(root: Path | None) -> ServerLayout:
    return ServerLayout.resolve(root)


def _fail(exc: RemoteError) -> NoReturn:
    typer.echo(f"erro: {exc}", err=True)
    raise typer.Exit(code=1)


def _pepper() -> str:
    pepper = os.environ.get("CECILIA_KEY_PEPPER", "")
    if len(pepper) < MIN_PEPPER_LENGTH:
        _fail(
            RemoteError(
                f"CECILIA_KEY_PEPPER ausente ou curta (mínimo {MIN_PEPPER_LENGTH} caracteres)"
            )
        )
    return pepper


@admin_app.command("publish")
def publish_command(
    source: Annotated[Path, typer.Argument(help="Diretório com os arquivos .parquet.")],
    dataset: Annotated[str, typer.Option("--dataset", help="Nome do dataset (a-z, 0-9, _, -).")],
    version: Annotated[
        str,
        typer.Option("--version", help="Versão imutável (v1, v2, ...)."),
    ] = "v1",
    root: RootOption = None,
    description: Annotated[
        str,
        typer.Option("--description", help="Descrição curta do dataset."),
    ] = "",
    source_name: Annotated[
        str,
        typer.Option("--source", help="Catálogo de origem (ex.: Gaia DR3)."),
    ] = "",
    query: Annotated[
        str,
        typer.Option("--query", help="Consulta ou URL de origem."),
    ] = "",
    license: Annotated[
        str,
        typer.Option("--license", help="Licença dos dados."),
    ] = "",
    attribution: Annotated[
        str,
        typer.Option("--attribution", help="Texto de atribuição exigido."),
    ] = "",
    supersedes: Annotated[
        str | None,
        typer.Option("--supersedes", help="Versão anterior substituída por esta."),
    ] = None,
) -> None:
    """Publica um diretório de Parquets como dataset imutável."""
    provenance = {
        chave: valor for chave, valor in {"source": source_name, "query": query}.items() if valor
    }
    try:
        resultado = publish(
            _layout(root),
            source,
            dataset,
            version,
            description=description,
            provenance=provenance,
            license=license,
            attribution=attribution,
            supersedes=supersedes,
        )
    except RemoteError as exc:
        _fail(exc)

    typer.echo(
        f"publicado {dataset}@{version}: {len(resultado.manifest.files)} arquivo(s), "
        f"{resultado.copied} blob(s) novo(s), {resultado.reused} reaproveitado(s)"
    )
    typer.echo(f"manifesto: {resultado.manifest_path}")


@admin_app.command("verify")
def verify_command(
    root: RootOption = None,
    deep: Annotated[
        bool,
        typer.Option("--deep", help="Relê os Parquets para conferir linhas e schema."),
    ] = False,
) -> None:
    """Verifica blobs, manifestos e catálogo."""
    problemas = verify(_layout(root), deep=deep)
    if not problemas:
        typer.echo("ok: nenhum problema encontrado")
        return
    for problema in problemas:
        typer.echo(
            f"{problema.kind}: {problema.subject} — {problema.detail}",
            err=True,
        )
    typer.echo(f"{len(problemas)} problema(s) encontrado(s)", err=True)
    raise typer.Exit(code=1)


@admin_app.command("gc")
def gc_command(
    root: RootOption = None,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Remove de fato os blobs órfãos (sem esta opção, só lista)."),
    ] = False,
) -> None:
    """Lista ou remove blobs que nenhum manifesto referencia."""
    orfaos = collect_garbage(_layout(root), apply=apply)
    if not orfaos:
        typer.echo("ok: nenhum blob órfão")
        return
    for caminho in orfaos:
        typer.echo(caminho.name)
    if apply:
        typer.echo(f"{len(orfaos)} blob(s) removido(s)")
    else:
        typer.echo(f"{len(orfaos)} blob(s) órfão(s); use --apply para remover")


@admin_app.command("catalog")
def catalog_command(root: RootOption = None) -> None:
    """Reconstrói o catálogo a partir dos manifestos."""
    try:
        catalogo = rebuild_catalog(_layout(root))
    except RemoteError as exc:
        _fail(exc)
    versoes = sum(len(item["versions"]) for item in catalogo["datasets"])
    typer.echo(
        f"catálogo reconstruído: {len(catalogo['datasets'])} dataset(s), {versoes} versão(ões)"
    )


@admin_app.command("log")
def log_command(
    root: RootOption = None,
    since: Annotated[
        str,
        typer.Option("--since", help="Período: 7d, 24h ou data ISO."),
    ] = "7d",
    alias: Annotated[
        str | None,
        typer.Option("--alias", help="Filtra por apelido."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", help="Máximo de linhas."),
    ] = 50,
) -> None:
    """Mostra os acessos registrados, do mais recente para o mais antigo."""
    try:
        desde = parse_since(since)
    except RemoteError as exc:
        _fail(exc)

    registros = AuditLog(_layout(root)).recent(limit=limit, since=desde, alias=alias)
    if not registros:
        typer.echo("nenhum acesso no período")
        return

    typer.echo("QUANDO\tALIAS\tACAO\tDATASET\tARQUIVO\tBYTES\tSTATUS")
    total = 0
    for registro in registros:
        bytes_enviados = int(registro["bytes_sent"])
        total += bytes_enviados
        arquivo = str(registro["file"] or registro["blob"] or "-")
        if len(arquivo) > 40:
            arquivo = arquivo[:37] + "..."
        typer.echo(
            "\t".join(
                [
                    str(registro["ts"]),
                    str(registro["alias"] or "-"),
                    str(registro["action"]),
                    str(registro["dataset"] or "-"),
                    arquivo,
                    human_bytes(bytes_enviados),
                    str(registro["status"]),
                ]
            )
        )
    typer.echo(f"{len(registros)} acesso(s), {human_bytes(total)} no total")


@key_app.command("create")
def key_create(
    alias: Annotated[str, typer.Option("--alias", help="Apelido da pessoa.")],
    root: RootOption = None,
    days: Annotated[
        int,
        typer.Option("--days", help="Validade da chave em dias."),
    ] = 90,
) -> None:
    """Emite uma chave nova; o token aparece uma única vez."""
    try:
        emitida = KeyStore(_layout(root), _pepper()).create(alias, days)
    except RemoteError as exc:
        _fail(exc)
    typer.echo(f"key_id: {emitida.key_id}")
    typer.echo(f"alias: {emitida.alias}")
    typer.echo(f"expira: {emitida.expires_at}")
    typer.echo(f"token: {emitida.token}")
    typer.echo("guarde o token agora: ele não será exibido de novo.")


@key_app.command("list")
def key_list(root: RootOption = None) -> None:
    """Lista as chaves emitidas, sem mostrar segredos."""
    chaves = KeyStore(_layout(root)).list()
    if not chaves:
        typer.echo("nenhuma chave emitida")
        return
    typer.echo("KEY_ID\tALIAS\tCRIADA\tEXPIRA\tREVOGADA\tULTIMO_USO")
    for chave in chaves:
        typer.echo(
            "\t".join(
                [
                    chave.key_id,
                    chave.alias,
                    chave.created_at,
                    chave.expires_at,
                    chave.revoked_at or "-",
                    chave.last_used_at or "-",
                ]
            )
        )


@key_app.command("revoke")
def key_revoke(
    key_id: Annotated[str, typer.Argument(help="key_id da chave a revogar.")],
    root: RootOption = None,
) -> None:
    """Revoga uma chave imediatamente."""
    if KeyStore(_layout(root)).revoke(key_id):
        typer.echo(f"chave {key_id} revogada")
    else:
        typer.echo(f"erro: chave {key_id} não encontrada ou já revogada", err=True)
        raise typer.Exit(code=1)


@app.command("serve")
def serve_command(
    host: Annotated[
        str,
        typer.Option("--host", help="Endereço de escuta."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", help="Porta HTTP."),
    ] = 8000,
    root: RootOption = None,
) -> None:
    """Sobe o servidor HTTP (deixe o TLS para o tailscale serve)."""
    try:
        settings = Settings.from_env(root)
    except RemoteError as exc:
        _fail(exc)

    import uvicorn

    from .remote.server import create_app

    typer.echo(f"servindo em http://{host}:{port}")
    uvicorn.run(create_app(settings), host=host, port=port, log_level="info")


def main() -> None:
    """Ponto de entrada do console script ``cecilia``."""
    app()


if __name__ == "__main__":
    main()
