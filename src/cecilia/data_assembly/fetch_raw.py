"""Baixa os dados brutos do CECILIA para data/raw/ (ver data/README.md).

Etapas (cada uma pode ser retomada; arquivos já existentes são pulados):

    python scripts/fetch_raw.py lamost      # LAMOST DR11 v2.0 LRS (VizieR V/162, espelho CfA)
    python scripts/fetch_raw.py apokasc     # APOKASC-3 table4 (VizieR J/ApJS/276/69, espelho CfA)
    python scripts/fetch_raw.py gaia A      # Gaia DR3 + 2MASS para os source_id do LAMOST
    python scripts/fetch_raw.py gaia B      # Gaia DR3 + 2MASS para os source_id do APOKASC-3
    python scripts/fetch_raw.py all

Regras de data/raw/: guardar exatamente o que o serviço remoto devolveu. Os valores
sentinela (-9999, -999, 99) ficam como vieram. Remover sentinelas, deduplicar e cruzar
tabelas é trabalho de data/interim/.

Toda saída gera uma linha em data/raw/MANIFEST.jsonl (arquivo, fonte, consulta/URL,
data UTC, linhas). Essa é a fonte para a tabela de manifesto em data/README.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "MANIFEST.jsonl"

VIZIER_CFA = "vizier.cfa.harvard.edu"
GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap"


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(f"[{now_utc()}] {msg}", flush=True)


def record(path: Path, source: str, query: str, rows: int) -> None:
    entry = {"file": str(path.relative_to(ROOT)), "source": source, "query": query,
             "date": now_utc(), "rows": int(rows)}
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- LAMOST

LAMOST_DIR = RAW / "lamost"
LAMOST_URL = f"https://{VIZIER_CFA}/ftp/cats/V/162/dr11l.dat.gz"
LAMOST_README_URL = f"https://{VIZIER_CFA}/ftp/cats/V/162/ReadMe"
LAMOST_GZ = LAMOST_DIR / "dr11l.dat.gz"
LAMOST_PARQUET = RAW / "lamost_dr11_lrs.parquet"
LAMOST_NROWS = 11_931_197  # nrows do V/162 ReadMe

# Campos do V/162 dr11l.dat, na ordem (36 campos separados por '|', Lrecl 432).
LAMOST_COLS = [
    "ObsID", "uID", "gpID", "Target", "ObsDate", "LMJD", "MJD", "PlanID", "spID", "FiberID",
    "RAdeg", "DEdeg", "snru", "snrg", "snrr", "snri", "snrz", "Class", "subClass",
    "z", "e_z", "PanSTARRS", "gmag", "rmag", "imag", "zmag", "ymag",
    "GaiaDR3", "Gmag", "FiberType", "offsets", "offsetsv", "RAOdeg", "DEOdeg",
    "FiberMask", "fNFlux",
]
LAMOST_INT = ["ObsID", "LMJD", "MJD", "spID", "FiberID", "PanSTARRS", "GaiaDR3",
              "offsets", "FiberMask", "fNFlux"]
LAMOST_FLOAT = ["RAdeg", "DEdeg", "snru", "snrg", "snrr", "snri", "snrz", "z", "e_z",
                "gmag", "rmag", "imag", "zmag", "ymag", "Gmag", "offsetsv", "RAOdeg", "DEOdeg"]
# gpID é I19 e pode passar de int64, então fica como texto.
LAMOST_STR = [c for c in LAMOST_COLS if c not in LAMOST_INT + LAMOST_FLOAT]

LAMOST_SCHEMA = pa.schema(
    [(c, pa.int64() if c in LAMOST_INT else pa.float64() if c in LAMOST_FLOAT else pa.string())
     for c in LAMOST_COLS]
)


def download(url: str, dest: Path) -> None:
    """Download retomável com curl (-C -), com novas tentativas em caso de queda."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 21):
        r = subprocess.run(["curl", "-fL", "-C", "-", "--retry", "5", "--retry-delay", "10",
                            "-o", str(dest), url])
        if r.returncode == 0:
            return
        # 33 = servidor não aceita Range; 416 com arquivo já completo também cai aqui
        log(f"curl saiu com {r.returncode} (tentativa {attempt}), tentando de novo em 30 s")
        time.sleep(30)
    sys.exit(f"falha ao baixar {url}")


def remote_size(url: str) -> int:
    out = subprocess.run(["curl", "-sIL", url], capture_output=True, text=True, check=True).stdout
    sizes = [int(line.split(":", 1)[1]) for line in out.splitlines()
             if line.lower().startswith("content-length:")]
    return sizes[-1]


def fetch_lamost() -> None:
    if LAMOST_PARQUET.exists():
        log(f"{LAMOST_PARQUET.name} já existe, pulando LAMOST")
        return
    LAMOST_DIR.mkdir(parents=True, exist_ok=True)
    readme = LAMOST_DIR / "ReadMe"
    if not readme.exists():
        part = readme.with_suffix(".part")
        part.unlink(missing_ok=True)
        download(LAMOST_README_URL, part)
        part.rename(readme)
        record(readme, "LAMOST DR11 v2.0 LRS (VizieR V/162)", LAMOST_README_URL, 0)

    expected = remote_size(LAMOST_URL)
    if not LAMOST_GZ.exists() or LAMOST_GZ.stat().st_size != expected:
        log(f"baixando {LAMOST_URL} ({expected / 1e9:.2f} GB)")
        download(LAMOST_URL, LAMOST_GZ)
        if LAMOST_GZ.stat().st_size != expected:
            sys.exit(f"tamanho de {LAMOST_GZ} difere do remoto ({expected} B)")
        record(LAMOST_GZ, "LAMOST DR11 v2.0 LRS (VizieR V/162)", LAMOST_URL, LAMOST_NROWS)

    log("convertendo dr11l.dat.gz para Parquet")
    tmp = LAMOST_PARQUET.with_suffix(".parquet.part")
    rows = 0
    with pq.ParquetWriter(tmp, LAMOST_SCHEMA, compression="zstd") as writer:
        reader = pd.read_csv(LAMOST_GZ, sep="|", header=None, names=LAMOST_COLS, dtype=str,
                             keep_default_na=False, na_filter=False, chunksize=500_000,
                             compression="gzip")
        for chunk in reader:
            if chunk.shape[1] != len(LAMOST_COLS):
                sys.exit(f"esperava {len(LAMOST_COLS)} campos, vieram {chunk.shape[1]}")
            for c in LAMOST_COLS:
                chunk[c] = chunk[c].str.strip()
            for c in LAMOST_INT:
                # Direto de texto para Int64: passar por float64 (to_numeric com nulos)
                # arredonda ids de 18-19 dígitos (PanSTARRS, GaiaDR3).
                text = chunk[c].mask(chunk[c] == "")
                chunk[c] = text.astype("Int64")
                ok = text.isna() | (chunk[c].astype("string") == text.astype("string"))
                if not ok.all():
                    sys.exit(f"{c}: {(~ok).sum()} inteiros não batem com o texto original")
            for c in LAMOST_FLOAT:
                chunk[c] = pd.to_numeric(chunk[c].mask(chunk[c] == ""), errors="raise").astype("float64")
            writer.write_table(pa.Table.from_pandas(chunk, schema=LAMOST_SCHEMA, preserve_index=False))
            rows += len(chunk)
            log(f"  {rows:,} linhas")
    if rows != LAMOST_NROWS:
        sys.exit(f"esperava {LAMOST_NROWS:,} linhas, li {rows:,}; {tmp} mantido para inspeção")
    tmp.rename(LAMOST_PARQUET)
    record(LAMOST_PARQUET, "LAMOST DR11 v2.0 LRS (VizieR V/162)",
           f"{LAMOST_URL} convertido sem filtros (36 campos do ReadMe; sentinelas preservadas)", rows)


# -------------------------------------------------------------------------- APOKASC-3

APOKASC_CAT = "J/ApJS/276/69/table4"
APOKASC_PARQUET = RAW / "apokasc3_table4.parquet"


def fetch_apokasc() -> None:
    if APOKASC_PARQUET.exists():
        log(f"{APOKASC_PARQUET.name} já existe, pulando")
        return
    from astroquery.vizier import Vizier

    v = Vizier(columns=["**"], row_limit=-1, vizier_server=VIZIER_CFA)
    t = v.get_catalogs(APOKASC_CAT)[0]
    df = t.to_pandas()
    if len(df) != 15_808 or df["GaiaDR3"].isna().any():
        sys.exit(f"APOKASC-3 inesperado: {len(df)} linhas, {df['GaiaDR3'].isna().sum()} sem GaiaDR3")
    df.to_parquet(APOKASC_PARQUET, index=False)
    record(APOKASC_PARQUET, "APOKASC-3 (Pinsonneault+ 2025, VizieR J/ApJS/276/69)",
           f"astroquery Vizier(columns=['**'], row_limit=-1, server={VIZIER_CFA})"
           f".get_catalogs('{APOKASC_CAT}')", len(df))
    log(f"APOKASC-3: {len(df):,} linhas")


# ------------------------------------------------------------------------------ Gaia

GAIA_COLS = [
    "source_id", "ra", "dec", "parallax", "parallax_error", "parallax_over_error",
    "pmra", "pmra_error", "pmdec", "pmdec_error", "ruwe", "astrometric_excess_noise",
    "astrometric_params_solved", "visibility_periods_used", "ipd_frac_multi_peak",
    "ipd_gof_harmonic_amplitude", "duplicated_source",
    "phot_g_mean_mag", "phot_g_mean_flux_over_error", "phot_bp_mean_mag",
    "phot_bp_mean_flux_over_error", "phot_rp_mean_mag", "phot_rp_mean_flux_over_error",
    "phot_bp_n_obs", "phot_rp_n_obs", "bp_rp", "phot_bp_rp_excess_factor",
    "phot_bp_n_blended_transits", "phot_rp_n_blended_transits", "phot_variable_flag",
    "non_single_star", "radial_velocity", "radial_velocity_error", "l", "b",
    "has_xp_continuous", "has_xp_sampled", "has_rvs", "classprob_dsc_combmod_star",
]
# GSP-Phot: só para baseline/análise, nunca feature (data/README.md).
AP_COLS = [
    f"{p}{s}" for p in ("teff_gspphot", "logg_gspphot", "mh_gspphot", "distance_gspphot",
                        "azero_gspphot", "ag_gspphot", "ebpminrp_gspphot", "radius_gspphot",
                        "mg_gspphot")
    for s in ("", "_lower", "_upper")
] + ["libname_gspphot", "logposterior_gspphot", "mcmcaccept_gspphot"]

QUERY_SOURCE = (
    "SELECT " + ", ".join(f"g.{c}" for c in GAIA_COLS) + ", "
    + ", ".join(f"ap.{c}" for c in AP_COLS) + "\n"
    "FROM tap_upload.ids AS u\n"
    "JOIN gaiadr3.gaia_source AS g ON g.source_id = u.source_id\n"
    "LEFT OUTER JOIN gaiadr3.astrophysical_parameters AS ap ON ap.source_id = u.source_id"
)
# Nunca juntar esta consulta com a de cima num único LEFT OUTER JOIN: estoura o
# limite de 60 s de usuário anônimo mesmo com 3 ids.
QUERY_TMASS = (
    "SELECT u.source_id, xm.original_ext_source_id, xm.angular_distance,\n"
    "  xm.number_of_neighbours, xm.number_of_mates, xm.xm_flag,\n"
    "  tm.designation, tm.ra AS tmass_ra, tm.dec AS tmass_dec, tm.j_m, tm.j_msigcom,\n"
    "  tm.h_m, tm.h_msigcom, tm.ks_m, tm.ks_msigcom, tm.ph_qual, tm.ext_key, tm.j_date\n"
    "FROM tap_upload.ids AS u\n"
    "JOIN gaiadr3.tmass_psc_xsc_best_neighbour AS xm ON xm.source_id = u.source_id\n"
    "JOIN gaiadr3.tmass_psc_xsc_join AS xj ON xj.clean_tmass_psc_xsc_oid = xm.clean_tmass_psc_xsc_oid\n"
    "JOIN gaiadr1.tmass_original_valid AS tm ON tm.designation = xj.original_psc_source_id\n"
    "  AND tm.designation = xm.original_ext_source_id"
)
QUERIES = {"source": QUERY_SOURCE, "tmass": QUERY_TMASS}

ANON_ROW_LIMIT = 50_000
_local = threading.local()


class TruncatedResult(RuntimeError):
    pass


def gaia_client():
    if not hasattr(_local, "gaia"):
        from astroquery.gaia import GaiaClass

        g = GaiaClass(show_server_messages=False)
        g.ROW_LIMIT = -1
        _local.gaia = g
    return _local.gaia


def trail_ids(trail: str) -> np.ndarray:
    if trail == "A":
        # numpy_nullable: sem isso uma coluna int64 com nulos vira float64 e arredonda os ids
        df = pd.read_parquet(LAMOST_PARQUET, columns=["Class", "FiberType", "GaiaDR3"],
                             dtype_backend="numpy_nullable")
        ids = df.loc[(df.Class == "STAR") & (df.FiberType == "Obj") & (df.GaiaDR3 != -9999),
                     "GaiaDR3"]
    else:
        ids = pd.read_parquet(APOKASC_PARQUET, columns=["GaiaDR3"],
                              dtype_backend="numpy_nullable")["GaiaDR3"]
    return np.unique(ids.dropna().astype("int64").to_numpy())


def run_chunk(kind: str, ids: np.ndarray, out: Path) -> int:
    from astropy.table import Table

    upload = Table({"source_id": ids})
    for attempt in range(1, 7):
        try:
            job = gaia_client().launch_job_async(QUERIES[kind], upload_resource=upload,
                                                 upload_table_name="ids", dump_to_file=False,
                                                 verbose=False)
            t = job.get_results()
            if len(t) >= ANON_ROW_LIMIT:
                raise TruncatedResult(f"{out.name}: {len(t)} linhas, possível truncamento "
                                      f"pelo limite anônimo; use --chunk-size menor")
            # Sob carga o arquivo devolve resultados cortados sem erro (visto no trilho A:
            # 3.161 de 20.000). Todo id enviado existe no gaia_source, então menos linhas
            # que ids é falha transitória.
            if kind == "source" and len(t) != len(ids):
                raise RuntimeError(f"{len(t)} linhas para {len(ids)} ids (resultado cortado?)")
            df = t.to_pandas()
            for c in df.columns:  # colunas de texto vêm como bytes em alguns casos
                if df[c].dtype == object:
                    df[c] = df[c].map(lambda x: x.decode() if isinstance(x, bytes) else x)
            tmp = out.with_suffix(".part")
            df.to_parquet(tmp, index=False)
            tmp.rename(out)
            return len(df)
        except TruncatedResult:
            raise
        except Exception as e:  # rede, 408/500 do arquivo, reset de conexão
            wait = min(300, 15 * 2 ** (attempt - 1))
            log(f"  {out.name}: {type(e).__name__}: {str(e)[:200]} — nova tentativa em {wait} s")
            _local.__dict__.pop("gaia", None)
            time.sleep(wait)
    raise RuntimeError(f"{out.name} falhou após 6 tentativas")


def fetch_gaia(trail: str, chunk_size: int, workers: int) -> None:
    ids = trail_ids(trail)
    n_chunks = (len(ids) + chunk_size - 1) // chunk_size
    log(f"Trilho {trail}: {len(ids):,} source_id únicos, {n_chunks} lotes de {chunk_size:,}")
    chunk_dir = RAW / "gaia" / f"trail_{trail}"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    # Os ids de cada lote são salvos junto, para o lote ser reproduzível mesmo se a lista mudar.
    tasks = []
    for i in range(n_chunks):
        part = ids[i * chunk_size:(i + 1) * chunk_size]
        idfile = chunk_dir / f"ids_{i:05d}.npy"
        if idfile.exists():
            if not np.array_equal(np.load(idfile), part):
                sys.exit(f"{idfile} não bate com a lista atual; apague {chunk_dir} para recomeçar")
        else:
            np.save(idfile, part)
        for kind in QUERIES:
            out = chunk_dir / f"{kind}_{i:05d}.parquet"
            if not out.exists():
                tasks.append((kind, part, out))
    log(f"  {len(tasks)} consultas pendentes (de {2 * n_chunks})")

    done = 0
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = {pool.submit(run_chunk, k, p, o): o for k, p, o in tasks}
        for fut in as_completed(futures):
            n = fut.result()
            done += 1
            if done % 10 == 0 or done == len(tasks):
                log(f"  {done}/{len(tasks)} consultas ({futures[fut].name}: {n:,} linhas)")
    except BaseException:
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    pool.shutdown()

    for kind, query in QUERIES.items():
        out = RAW / f"gaia_dr3_trail{trail}_{kind}.parquet"
        parts = sorted(chunk_dir.glob(f"{kind}_*.parquet"))
        if len(parts) != n_chunks:
            sys.exit(f"{kind}: {len(parts)} de {n_chunks} lotes presentes")
        if out.exists() and out.stat().st_mtime >= max(p.stat().st_mtime for p in parts):
            log(f"  {out.name} já está atualizado")
            continue
        df = pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True)
        if not df.source_id.is_unique:
            sys.exit(f"{kind}: source_id repetido em {df.source_id.duplicated().sum()} linhas")
        tmp = out.with_suffix(".part")
        df.to_parquet(tmp, index=False)
        tmp.rename(out)
        record(out, f"Gaia DR3 ({GAIA_TAP})",
               f"{len(ids):,} source_id do trilho {trail} em lotes de {chunk_size:,} via "
               f"tap_upload.ids (lotes em {chunk_dir.relative_to(ROOT)}):\n{query}", len(df))
        missing = len(ids) - df.source_id.nunique()
        log(f"  {out.name}: {len(df):,} linhas, {df.source_id.nunique():,} source_id "
            f"({missing:,} ids sem linha)")


# ------------------------------------------------------------------------------ main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["lamost", "apokasc", "gaia", "all"])
    ap.add_argument("trail", nargs="?", choices=["A", "B"])
    ap.add_argument("--chunk-size", type=int, default=20_000)
    ap.add_argument("--workers", type=int, default=4,
                    help="consultas simultâneas ao Gaia Archive (manter ≤ 4)")
    a = ap.parse_args()
    if not 0 < a.chunk_size < ANON_ROW_LIMIT:
        ap.error(f"--chunk-size precisa estar entre 1 e {ANON_ROW_LIMIT - 1}")
    RAW.mkdir(parents=True, exist_ok=True)

    if a.step in ("lamost", "all"):
        fetch_lamost()
    if a.step in ("apokasc", "all"):
        fetch_apokasc()
    if a.step == "gaia":
        if not a.trail:
            ap.error("gaia precisa do trilho: A ou B")
        fetch_gaia(a.trail, a.chunk_size, a.workers)
    if a.step == "all":
        fetch_gaia("B", a.chunk_size, a.workers)
        fetch_gaia("A", a.chunk_size, a.workers)


if __name__ == "__main__":
    main()
