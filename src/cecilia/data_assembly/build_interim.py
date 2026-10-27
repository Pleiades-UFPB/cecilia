"""Monta as tabelas cruzadas de data/interim/ (uma linha por estrela).

    python scripts/build_interim.py          # roda depois de scripts/clean_sentinels.py

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

Nenhum corte de qualidade (RUWE, S/N mínimo, ph_qual...) é aplicado aqui: isso é
decisão de modelagem e fica para depois.

Os Parquet levam metadados do pandas para que pd.read_parquet() devolva inteiros com
nulo como Int64 (e não float64, que arredonda ids de 18-19 dígitos).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
MANIFEST = INTERIM / "MANIFEST.jsonl"
TMP = INTERIM / ".duckdb_tmp"


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def q(name: str) -> str:
    """Identificador entre aspas para o DuckDB (colunas como [Fe/H] e 2MASS)."""
    return '"' + name.replace('"', '""') + '"'


def cols(path: Path) -> list[str]:
    return pq.read_schema(path).names


def select_list(alias: str, names: list[str], prefix: str = "", skip=()) -> list[str]:
    return [f"{alias}.{q(c)} AS {q(prefix + c)}" for c in names if c not in skip]


def add_pandas_int64_metadata(path: Path) -> None:
    """Reescreve o Parquet (por row group) com metadados do pandas marcando int64 como Int64."""
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    empty = schema.empty_table().to_pandas(
        types_mapper=lambda t: pd.Int64Dtype() if t == pa.int64() else None)
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
        f"SELECT count(*), count(DISTINCT source_id) FROM read_parquet('{tmp}')").fetchone()
    if n != uniq or n != key_count:
        raise SystemExit(f"{out.name}: {n:,} linhas, {uniq:,} source_id; esperava {key_count:,}")
    tmp.replace(out)
    add_pandas_int64_metadata(out)
    stats = con.execute(
        f"SELECT count(ra), count(designation) FROM read_parquet('{out}')").fetchone()
    print(f"{out.name}: {n:,} estrelas; com Gaia: {stats[0]:,}; com 2MASS: {stats[1]:,}")
    entry = {"file": str(out.relative_to(ROOT)), "from": [str(p.relative_to(ROOT)) for p in inputs],
             "step": notes, "date": now_utc(), "rows": n,
             "with_gaia": stats[0], "with_2mass": stats[1]}
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"SET memory_limit = '3GB'; SET threads = 4; SET temp_directory = '{TMP}'; SET preserve_insertion_order = false")

    # ------------------------------------------------------------------ Trilho A
    lamost = INTERIM / "lamost_dr11_lrs.parquet"
    gsrc, gtm = RAW / "gaia_dr3_trailA_source.parquet", RAW / "gaia_dr3_trailA_tmass.parquet"
    lam_cols = cols(lamost)
    sql_a = f"""
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
           {", ".join(select_list("g", cols(gsrc), skip=("source_id",)))},
           {", ".join(select_list("t", cols(gtm), skip=("source_id",)))},
           {", ".join(select_list("b", lam_cols, "lamost_"))},
           CASE WHEN b.is_m THEN 'i' ELSE 'g' END AS lamost_snr_band,
           b.n_spectra AS lamost_n_spectra
    FROM best b
    LEFT JOIN read_parquet('{gsrc}') g ON g.source_id = b.GaiaDR3
    LEFT JOIN read_parquet('{gtm}') t ON t.source_id = b.GaiaDR3
    """
    n_a = con.execute(f"""SELECT count(DISTINCT GaiaDR3) FROM read_parquet('{lamost}')
        WHERE Class = 'STAR' AND FiberType = 'Obj' AND GaiaDR3 IS NOT NULL""").fetchone()[0]
    build(con, INTERIM / "trailA_lamost_gaia_2mass.parquet", sql_a, n_a, [lamost, gsrc, gtm],
          "LAMOST STAR/Obj, 1 espectro por GaiaDR3 (maior snri se tipo M, senão snrg; "
          "depois a outra banda, MJD, ObsID) "
          "LEFT JOIN Gaia DR3 source + 2MASS em source_id")

    # ------------------------------------------------------------------ Trilho B
    apo = INTERIM / "apokasc3_table4.parquet"
    bsrc, btm = RAW / "gaia_dr3_trailB_source.parquet", RAW / "gaia_dr3_trailB_tmass.parquet"
    sql_b = f"""
    SELECT a.GaiaDR3 AS source_id,
           {", ".join(select_list("g", cols(bsrc), skip=("source_id",)))},
           {", ".join(select_list("t", cols(btm), skip=("source_id",)))},
           {", ".join(select_list("a", cols(apo), "apokasc_"))}
    FROM read_parquet('{apo}') a
    LEFT JOIN read_parquet('{bsrc}') g ON g.source_id = a.GaiaDR3
    LEFT JOIN read_parquet('{btm}') t ON t.source_id = a.GaiaDR3
    """
    n_b = con.execute(f"SELECT count(DISTINCT GaiaDR3) FROM read_parquet('{apo}')").fetchone()[0]
    build(con, INTERIM / "trailB_apokasc_gaia_2mass.parquet", sql_b, n_b, [apo, bsrc, btm],
          "APOKASC-3 table4 LEFT JOIN Gaia DR3 source + 2MASS em source_id")

    con.close()
    TMP.rmdir() if TMP.exists() and not any(TMP.iterdir()) else None


if __name__ == "__main__":
    main()
