"""Recorta a região das Plêiades (Melotte 22 / M45) do Trilho A e marca candidatos a membro.

    python scripts/pleiades_region.py        # roda depois de scripts/build_interim.py

1. Cone de 5° em torno de (RA, Dec) = (56.75°, +24.12°). A 136 pc, 5° são ~12 pc, o
   raio de maré do aglomerado; o cone inclui também estrelas de campo na mesma direção.
2. Busca phot_g_mean_flux (e o erro) no Gaia DR3 para essas estrelas — essas colunas não
   estavam na consulta original. Cache em data/raw/gaia_dr3_pleiades_gflux.parquet.
3. Candidato a membro (is_member): movimento próprio a menos de 4 mas/ano de
   (pmra, pmdec) = (20.0, -45.5) mas/ano e paralaxe entre 6.5 e 8.3 mas (~120-154 pc).
   O centro foi conferido nos dados: a mediana dos candidatos é (19.99, -45.45) mas/ano
   e 7.37 mas. É um corte simples, não uma análise de pertinência probabilística.

Saída: data/interim/pleiades_region.parquet (com dist_pc = 1000 / parallax).
"""

from __future__ import annotations

import datetime as dt
import json

import duckdb
import numpy as np
import pandas as pd

import fetch_raw
from build_interim import INTERIM, MANIFEST, ROOT, add_pandas_int64_metadata

CENTER_RA, CENTER_DEC, RADIUS_DEG = 56.75, 24.12, 5.0
PM_CENTER, PM_RADIUS = (20.0, -45.5), 4.0
PLX_MIN, PLX_MAX = 6.5, 8.3

GFLUX_RAW = fetch_raw.RAW / "gaia_dr3_pleiades_gflux.parquet"
QUERY_GFLUX = (
    "SELECT u.source_id, g.phot_g_mean_flux, g.phot_g_mean_flux_error\n"
    "FROM tap_upload.ids AS u\n"
    "JOIN gaiadr3.gaia_source AS g ON g.source_id = u.source_id"
)
OUT = INTERIM / "pleiades_region.parquet"


def fetch_gflux(ids: np.ndarray) -> None:
    if GFLUX_RAW.exists():
        print(f"{GFLUX_RAW.name} já existe, pulando consulta ao Gaia")
        return
    fetch_raw.QUERIES["gflux"] = QUERY_GFLUX
    parts = []
    for i in range(0, len(ids), 20_000):
        part = GFLUX_RAW.with_name(f"gflux_{i // 20_000:03d}.parquet")
        if not part.exists():
            fetch_raw.run_chunk("gflux", ids[i:i + 20_000], part)
        parts.append(part)
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    if not df.source_id.is_unique or len(df) != len(ids):
        raise SystemExit(f"gflux: {len(df)} linhas para {len(ids)} ids")
    df.to_parquet(GFLUX_RAW, index=False)
    for p in parts:
        p.unlink()
    fetch_raw.record(GFLUX_RAW, f"Gaia DR3 ({fetch_raw.GAIA_TAP})",
                     f"{len(ids):,} source_id do cone de {RADIUS_DEG}° nas Plêiades, "
                     f"lotes de 20,000 via tap_upload.ids:\n{QUERY_GFLUX}", len(df))


def main() -> None:
    con = duckdb.connect()
    con.execute("SET memory_limit = '3GB'; SET threads = 4")
    src = INTERIM / "trailA_lamost_gaia_2mass.parquet"
    sep = (f"degrees(acos(least(1, sin(radians(dec)) * sin(radians({CENTER_DEC})) + "
           f"cos(radians(dec)) * cos(radians({CENTER_DEC})) * cos(radians(ra - {CENTER_RA})))))")
    con.execute(f"CREATE TABLE cone AS SELECT *, {sep} AS sep_deg FROM read_parquet('{src}') "
                f"WHERE {sep} < {RADIUS_DEG}")
    ids = np.sort(con.execute("SELECT source_id FROM cone").fetchnumpy()["source_id"].astype("int64"))
    fetch_gflux(ids)

    tmp = OUT.with_suffix(".part")
    con.execute(f"""COPY (
        SELECT c.*, f.phot_g_mean_flux, f.phot_g_mean_flux_error,
               1000 / c.parallax AS dist_pc,
               coalesce(sqrt((c.pmra - {PM_CENTER[0]})^2 + (c.pmdec - ({PM_CENTER[1]}))^2) < {PM_RADIUS}
                        AND c.parallax BETWEEN {PLX_MIN} AND {PLX_MAX}, false) AS is_member
        FROM cone c LEFT JOIN read_parquet('{GFLUX_RAW}') f USING (source_id)
    ) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)""")
    tmp.replace(OUT)
    add_pandas_int64_metadata(OUT)
    n, members = con.execute(f"SELECT count(*), count(*) FILTER (WHERE is_member) "
                             f"FROM read_parquet('{OUT}')").fetchone()
    print(f"{OUT.name}: {n:,} estrelas no cone, {members:,} candidatos a membro")
    entry = {"file": str(OUT.relative_to(ROOT)), "from": [str(src.relative_to(ROOT)),
             str(GFLUX_RAW.relative_to(ROOT))],
             "step": f"cone {RADIUS_DEG}° em ({CENTER_RA}, {CENTER_DEC}); is_member: |pm - "
                     f"{PM_CENTER}| < {PM_RADIUS} mas/ano e {PLX_MIN} <= parallax <= {PLX_MAX}",
             "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "rows": n, "members": members}
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
