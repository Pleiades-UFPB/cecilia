"""Gera data/interim/ a partir de data/raw/, trocando valores sentinela por nulo.

    python scripts/clean_sentinels.py

Só os sentinelas documentados nos ReadMe do VizieR são trocados; nenhuma linha é
removida e nenhuma outra coluna muda. Os arquivos do Gaia/2MASS já usam nulos de verdade
e não passam por aqui.

Valores que parecem sentinela mas NÃO são trocados:
- LAMOST snr* == 99 e FiberID == 99 são valores reais;
- APOKASC-3 E_AgeRC/E_AgeRGB == 99 parecem teto, não ausência (decisão de modelagem);
- Gaia logposterior_gspphot <= -999 são log-probabilidades reais.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
MANIFEST = INTERIM / "MANIFEST.jsonl"

# arquivo -> {coluna: valor sentinela}
SENTINELS = {
    "lamost_dr11_lrs.parquet": {
        **{c: -9999 for c in ("snru", "snrg", "snrr", "snri", "snrz", "z", "e_z", "GaiaDR3", "Gmag")},
        **{c: -999 for c in ("gmag", "rmag", "imag", "zmag", "ymag")},  # Pan-STARRS
        "offsetsv": 99,
    },
    "apokasc3_table4.parquet": {
        "[C/Fe]": -9999.99, "[N/Fe]": -9999.99,
        "e_[C/Fe]": -999.99, "e_[N/Fe]": -999.99,
    },
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def null_sentinels(table: pa.Table, sentinels: dict) -> tuple[pa.Table, dict]:
    counts = {}
    for col, value in sentinels.items():
        arr = table[col]
        if pa.types.is_floating(arr.type):
            # comparação com tolerância: -9999.99 em float32 não é exatamente -9999.99
            hit = pc.less(pc.abs(pc.subtract(arr, value)), 1e-3)
        else:
            hit = pc.equal(arr, pa.scalar(int(value), arr.type))
        hit = pc.fill_null(hit, False)
        counts[col] = pc.sum(hit).as_py() or 0
        table = table.set_column(table.schema.get_field_index(col), col,
                                 pc.if_else(hit, pa.scalar(None, arr.type), arr))
    return table, counts


def clean(name: str, sentinels: dict) -> None:
    src, out = RAW / name, INTERIM / name
    pf = pq.ParquetFile(src)
    missing = set(sentinels) - set(pf.schema_arrow.names)
    if missing:
        raise SystemExit(f"{name}: colunas inexistentes {sorted(missing)}")
    totals = dict.fromkeys(sentinels, 0)
    tmp = out.with_suffix(".part")
    with pq.ParquetWriter(tmp, pf.schema_arrow, compression="zstd") as writer:
        for rg in range(pf.num_row_groups):
            table, counts = null_sentinels(pf.read_row_group(rg), sentinels)
            writer.write_table(table)
            for c, n in counts.items():
                totals[c] += n
    if pq.ParquetFile(tmp).metadata.num_rows != pf.metadata.num_rows:
        raise SystemExit(f"{name}: número de linhas mudou")
    tmp.rename(out)
    entry = {"file": str(out.relative_to(ROOT)), "from": str(src.relative_to(ROOT)),
             "step": "sentinelas -> nulo", "sentinels": sentinels, "nulled": totals,
             "date": now_utc(), "rows": pf.metadata.num_rows}
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"{name}: {pf.metadata.num_rows:,} linhas")
    for c, n in totals.items():
        print(f"  {c:>10} = {sentinels[c]:>9} -> nulo: {n:,}")


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    for name, sentinels in SENTINELS.items():
        clean(name, sentinels)


if __name__ == "__main__":
    main()
