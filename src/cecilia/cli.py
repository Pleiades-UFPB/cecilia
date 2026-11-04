"""CLI do CECILIA: administração local do servidor de datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer

from .remote.catalog import rebuild_catalog
from .remote.errors import RemoteError
from .remote.gc import collect_garbage
from .remote.layout import ServerLayout
from .remote.publish import publish
from .remote.verify import verify

app = typer.Typer(no_args_is_help=True, help="Ferramentas do projeto CECILIA.")
admin_app = typer.Typer(
    no_args_is_help=True,
    help="Administração local do servidor de datasets (rodar no servidor).",
)
app.add_typer(admin_app, name="admin")

RootOption = Annotated[
    Path | None,
    typer.Option(
        "--root",
        envvar="CECILIA_SERVER_ROOT",
        help="Raiz do servidor (padrão: /srv/cecilia).",
    ),
]


def _layout(root: Path | None) -> ServerLayout:
    return ServerLayout.resolve(root)


def _fail(exc: RemoteError) -> NoReturn:
    typer.echo(f"erro: {exc}", err=True)
    raise typer.Exit(code=1)


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


def main() -> None:
    """Ponto de entrada do console script ``cecilia``."""
    app()


if __name__ == "__main__":
    main()
