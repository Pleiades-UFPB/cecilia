"""Mantém só as estrelas a menos de 200 pc das tabelas cruzadas de data/interim/.

    python scripts/filter_200pc.py          # roda depois de scripts/build_interim.py

Critério: parallax > 5 mas (distância = 1000 / parallax < 200 pc) e
parallax_over_error >= 10. Com erro relativo de paralaxe abaixo de 10%, inverter a
paralaxe é uma boa estimativa de distância; acima disso ela fica enviesada.
Estrelas sem paralaxe no Gaia (solução de 2 parâmetros) não têm distância e saem.

Saídas (as tabelas completas não mudam):
    data/interim/trailA_lamost_gaia_2mass_200pc.parquet
    data/interim/trailB_apokasc_gaia_2mass_200pc.parquet
com uma coluna nova, dist_pc = 1000 / parallax.
"""

from __future__ import annotations

import datetime as dt
import json

import duckdb

from build_interim import INTERIM, MANIFEST, ROOT, add_pandas_int64_metadata

MAX_PC = 200
MIN_PARALLAX_OVER_ERROR = 10
TABLES = ["trailA_lamost_gaia_2mass", "trailB_apokasc_gaia_2mass"]


def main() -> None:
    con = duckdb.connect()
    con.execute("SET memory_limit = '3GB'; SET threads = 4")
    where = f"parallax > {1000 / MAX_PC} AND parallax_over_error >= {MIN_PARALLAX_OVER_ERROR}"
    for name in TABLES:
        src, out = INTERIM / f"{name}.parquet", INTERIM / f"{name}_{MAX_PC}pc.parquet"
        tmp = out.with_suffix(".part")
        con.execute(f"""COPY (SELECT *, 1000 / parallax AS dist_pc FROM read_parquet('{src}')
                         WHERE {where}) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)""")
        tmp.replace(out)
        add_pandas_int64_metadata(out)
        total, kept = con.execute(f"""SELECT (SELECT count(*) FROM read_parquet('{src}')),
                                             (SELECT count(*) FROM read_parquet('{out}'))""").fetchone()
        print(f"{out.name}: {kept:,} de {total:,} estrelas")
        entry = {"file": str(out.relative_to(ROOT)), "from": str(src.relative_to(ROOT)),
                 "step": f"distância < {MAX_PC} pc: {where}; dist_pc = 1000 / parallax",
                 "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "rows": kept}
        with MANIFEST.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
