"""Monta as tabelas cruzadas de data/interim/ (uma linha por estrela).

    uv run python -m cecilia.data_assembly.build_interim   # depois de clean_sentinels

Trilho A — data/interim/trailA_lamost_gaia_2mass.parquet
    1. LAMOST (interim, sentinelas já nulos): Class == 'STAR', FiberType == 'Obj',
       GaiaDR3 não nulo — o mesmo filtro usado para buscar o Gaia.
    2. Um espectro por estrela (GaiaDR3), pelo maior S/N na banda adequada:
       - estrela tipo M (pelo menos metade dos espectros com subClass dM*, gM* ou sdM*):
         maior snri; empate -> snrg. Estrelas M são fracas no azul, então snri é o S/N
         que importa para elas;
       - demais estrelas: maior snrg; empate -> snri;
       depois MJD mais recente -> maior ObsID. lamost_snr_band diz qual banda decidiu
       ('i' ou 'g') e lamost_n_spectra quantos espectros a estrela tinha.
    3. LEFT JOIN com gaia_dr3_trailA_source e gaia_dr3_trailA_tmass em source_id.

Trilho B — data/interim/trailB_apokasc_gaia_2mass.parquet
    APOKASC-3 table4 (interim) LEFT JOIN gaia_dr3_trailB_source e _tmass em source_id.

Colunas: source_id primeiro; depois as do Gaia (nomes originais), as do 2MASS (nomes
originais da consulta) e as do LAMOST/APOKASC com prefixo lamost_ / apokasc_.

Nomes que diferem só por maiúsculas/minúsculas: o DuckDB não diferencia maiúsculas de
minúsculas. No LAMOST há gmag (Pan-STARRS) e Gmag (Gaia); no APOKASC-3 há E_AgeRGB
(incerteza superior) e e_AgeRGB (inferior), e o mesmo para AgeRC. Ao ler o Parquet, o
DuckDB renomeia a segunda coluna de cada par (Gmag -> Gmag_1), e b."Gmag" passa a ler
gmag. Por isso as colunas são selecionadas pelo nome que o DuckDB deu a cada posição do
esquema (nomes_duckdb) e a saída usa a renomeação explícita de RENOMEAR. Se dois nomes
de saída ainda coincidirem sem diferenciar maiúsculas, a execução para (checar_nomes_unicos).

Nenhum corte de qualidade (RUWE, S/N mínimo, ph_qual...) é aplicado aqui: isso é
decisão de modelagem e fica para depois.

Os Parquet levam metadados do pandas para que pd.read_parquet() devolva inteiros com
nulo como Int64 (e não float64, que arredonda ids de 18-19 dígitos).
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Iterable
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# src/cecilia/data_assembly/build_interim.py -> parents[3] é a raiz do repositório
ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
MANIFEST = INTERIM / "MANIFEST.jsonl"
TMP = INTERIM / ".duckdb_tmp"

# Renomeação explícita das colunas que só diferem de outra por maiúsculas/minúsculas.
# Chave: nome no Parquet de origem; valor: nome na saída (antes do prefixo).
RENOMEAR = {
    "lamost": {
        # G do Gaia DR3 copiado pelo LAMOST; gmag (minúsculo) é o g do Pan-STARRS
        "Gmag": "Gmag_gaia",
    },
    "apokasc": {
        # No VizieR, E_ é a incerteza superior e e_ a inferior (negativa no raw)
        "e_AgeRGB": "e_AgeRGB_inf",
        "e_AgeRC": "e_AgeRC_inf",
    },
}


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def q(name: str) -> str:
    """Identificador entre aspas para o DuckDB (colunas como [Fe/H] e 2MASS)."""
    return '"' + name.replace('"', '""') + '"'


def nomes_duckdb(con: duckdb.DuckDBPyConnection, path: Path) -> dict[str, str]:
    """Nome no Parquet -> nome que o DuckDB dá à mesma coluna (mesma posição no esquema).

    O DuckDB renomeia a segunda coluna de um par que só difere por maiúsculas
    (Gmag -> Gmag_1). A correspondência é feita pela posição, nunca pelo nome.
    """
    parquet = pq.read_schema(path).names
    duck = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchall()]
    if len(parquet) != len(duck):
        raise SystemExit(f"{path.name}: {len(parquet)} colunas no Parquet, {len(duck)} no DuckDB")
    return dict(zip(parquet, duck, strict=True))


def select_list(
    alias: str,
    nomes: dict[str, str],
    prefix: str = "",
    skip: Iterable[str] = (),
    renomear: dict[str, str] | None = None,
) -> list[str]:
    """Itens do SELECT: lê pelo nome do DuckDB e grava com o nome explícito de saída."""
    renomear = renomear or {}
    return [
        f"{alias}.{q(duck)} AS {q(prefix + renomear.get(orig, orig))}"
        for orig, duck in nomes.items()
        if orig not in skip
    ]


def nome_saida(item: str) -> str:
    """Nome de saída de um item 'alias."col" AS "saida"' de select_list."""
    return item.rsplit(" AS ", 1)[1].strip('"').replace('""', '"')


def checar_nomes_unicos(nomes: Iterable[str]) -> None:
    """Falha se dois nomes de saída coincidirem sem diferenciar maiúsculas/minúsculas."""
    vistos: dict[str, str] = {}
    for nome in nomes:
        chave = nome.lower()
        if chave in vistos:
            raise SystemExit(
                f"colunas de saída {vistos[chave]!r} e {nome!r} coincidem sem diferenciar "
                "maiúsculas; acrescente uma renomeação em RENOMEAR"
            )
        vistos[chave] = nome


def add_pandas_int64_metadata(path: Path) -> None:
    """Reescreve o Parquet (por row group) com metadados do pandas marcando int64 como Int64."""
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    empty = schema.empty_table().to_pandas(
        types_mapper=lambda t: pd.Int64Dtype() if t == pa.int64() else None
    )
    meta = pa.Schema.from_pandas(empty, preserve_index=False).metadata
    schema = schema.with_metadata(meta)
    tmp = path.with_suffix(".meta.part")
    with pq.ParquetWriter(tmp, schema, compression="zstd") as w:
        for rg in range(pf.num_row_groups):
            w.write_table(pf.read_row_group(rg).replace_schema_metadata(meta))
    tmp.replace(path)


def build(con, out: Path, sql: str, key_count: int, inputs: list[Path], notes: str) -> None:
    tmp = out.with_suffix(".part")
    con.execute(f"COPY ({sql}) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)")
    n, uniq = con.execute(
        f"SELECT count(*), count(DISTINCT source_id) FROM read_parquet('{tmp}')"
    ).fetchone()
    if n != uniq or n != key_count:
        raise SystemExit(f"{out.name}: {n:,} linhas, {uniq:,} source_id; esperava {key_count:,}")
    tmp.replace(out)
    add_pandas_int64_metadata(out)
    stats = con.execute(
        f"SELECT count(ra), count(designation) FROM read_parquet('{out}')"
    ).fetchone()
    print(f"{out.name}: {n:,} estrelas; com Gaia: {stats[0]:,}; com 2MASS: {stats[1]:,}")
    entry = {
        "file": str(out.relative_to(ROOT)),
        "from": [str(p.relative_to(ROOT)) for p in inputs],
        "step": notes,
        "date": now_utc(),
        "rows": n,
        "with_gaia": stats[0],
        "with_2mass": stats[1],
    }
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def sql_trilho_a(con, lamost: Path, gsrc: Path, gtm: Path) -> str:
    itens = [
        *select_list("g", nomes_duckdb(con, gsrc), skip=("source_id",)),
        *select_list("t", nomes_duckdb(con, gtm), skip=("source_id",)),
        *select_list("b", nomes_duckdb(con, lamost), "lamost_", renomear=RENOMEAR["lamost"]),
    ]
    checar_nomes_unicos(
        ["source_id", *map(nome_saida, itens), "lamost_snr_band", "lamost_n_spectra"]
    )
    return f"""
    WITH stars AS (
        SELECT *,
               count(*) OVER (PARTITION BY GaiaDR3) AS n_spectra,
               avg(CASE WHEN regexp_matches(subClass, '^(d|g|sd)M[0-9]$') THEN 1 ELSE 0 END)
                   OVER (PARTITION BY GaiaDR3) >= 0.5 AS is_m
        FROM read_parquet('{lamost}')
        WHERE Class = 'STAR' AND FiberType = 'Obj' AND GaiaDR3 IS NOT NULL
    ), ranked AS (
        SELECT *,
               row_number() OVER (PARTITION BY GaiaDR3
                   ORDER BY CASE WHEN is_m THEN snri ELSE snrg END DESC NULLS LAST,
                            CASE WHEN is_m THEN snrg ELSE snri END DESC NULLS LAST,
                            MJD DESC, ObsID DESC) AS rank_snr
        FROM stars
    ), best AS (SELECT * FROM ranked WHERE rank_snr = 1)
    SELECT b.GaiaDR3 AS source_id,
           {", ".join(itens)},
           CASE WHEN b.is_m THEN 'i' ELSE 'g' END AS lamost_snr_band,
           b.n_spectra AS lamost_n_spectra
    FROM best b
    LEFT JOIN read_parquet('{gsrc}') g ON g.source_id = b.GaiaDR3
    LEFT JOIN read_parquet('{gtm}') t ON t.source_id = b.GaiaDR3
    """


def sql_trilho_b(con, apo: Path, bsrc: Path, btm: Path) -> str:
    itens = [
        *select_list("g", nomes_duckdb(con, bsrc), skip=("source_id",)),
        *select_list("t", nomes_duckdb(con, btm), skip=("source_id",)),
        *select_list("a", nomes_duckdb(con, apo), "apokasc_", renomear=RENOMEAR["apokasc"]),
    ]
    checar_nomes_unicos(["source_id", *map(nome_saida, itens)])
    return f"""
    SELECT a.GaiaDR3 AS source_id,
           {", ".join(itens)}
    FROM read_parquet('{apo}') a
    LEFT JOIN read_parquet('{bsrc}') g ON g.source_id = a.GaiaDR3
    LEFT JOIN read_parquet('{btm}') t ON t.source_id = a.GaiaDR3
    """


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit = '3GB'")
    con.execute("SET threads = 4")
    con.execute(f"SET temp_directory = '{TMP}'")
    con.execute("SET preserve_insertion_order = false")

    # ------------------------------------------------------------------ Trilho A
    lamost = INTERIM / "lamost_dr11_lrs.parquet"
    gsrc = RAW / "gaia_dr3_trailA_source.parquet"
    gtm = RAW / "gaia_dr3_trailA_tmass.parquet"
    n_a = con.execute(
        f"""SELECT count(DISTINCT GaiaDR3) FROM read_parquet('{lamost}')
        WHERE Class = 'STAR' AND FiberType = 'Obj' AND GaiaDR3 IS NOT NULL"""
    ).fetchone()[0]
    build(
        con,
        INTERIM / "trailA_lamost_gaia_2mass.parquet",
        sql_trilho_a(con, lamost, gsrc, gtm),
        n_a,
        [lamost, gsrc, gtm],
        "LAMOST STAR/Obj, 1 espectro por GaiaDR3 (maior snri se tipo M, senão snrg; "
        "depois a outra banda, MJD, ObsID) "
        "LEFT JOIN Gaia DR3 source + 2MASS em source_id",
    )

    # ------------------------------------------------------------------ Trilho B
    apo = INTERIM / "apokasc3_table4.parquet"
    bsrc = RAW / "gaia_dr3_trailB_source.parquet"
    btm = RAW / "gaia_dr3_trailB_tmass.parquet"
    n_b = con.execute(f"SELECT count(DISTINCT GaiaDR3) FROM read_parquet('{apo}')").fetchone()[0]
    build(
        con,
        INTERIM / "trailB_apokasc_gaia_2mass.parquet",
        sql_trilho_b(con, apo, bsrc, btm),
        n_b,
        [apo, bsrc, btm],
        "APOKASC-3 table4 LEFT JOIN Gaia DR3 source + 2MASS em source_id",
    )

    con.close()
    if TMP.exists() and not any(TMP.iterdir()):
        TMP.rmdir()


if __name__ == "__main__":
    main()
