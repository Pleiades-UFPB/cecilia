"""Perfil de valores das tabelas interim dos Trilhos A e B (plano 03-01).

    uv run python scripts/perfil_interim.py

Saídas (todas regeneradas a cada execução, nada é editado à mão):
- outputs/perfil/trail{A,B}_perfil.csv — uma linha por coluna: tipo, ausentes, faixa,
  valores mais frequentes e a categoria do catálogo de colunas;
- outputs/perfil/trail{A,B}_perfil.md — a mesma tabela em Markdown, para o relatório;
- outputs/perfil/trailA_subclasse.csv — contagem de estrelas por subclasse LAMOST;
- outputs/figures/perfil/{A,B}/{coluna}.png — histograma de cada coluna numérica.

Lê uma coluna por vez (a tabela do Trilho A tem ~7,7 milhões de linhas e ~3 GB).
Não remove linhas nem colunas: só descreve.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from cecilia.limpeza.catalogo_colunas import catalogo  # noqa: E402
from cecilia.limpeza.perfil import perfil_serie  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
SAIDA = ROOT / "outputs" / "perfil"
FIGURAS = ROOT / "outputs" / "figures" / "perfil"
TABELAS = {
    "A": INTERIM / "trailA_lamost_gaia_2mass.parquet",
    "B": INTERIM / "trailB_apokasc_gaia_2mass.parquet",
}
# ids não fazem sentido em histograma
SEM_HISTOGRAMA = {"identificador"}


def nome_arquivo(coluna: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", coluna).strip("_")


def histograma(s: pd.Series, linha: dict, destino: Path) -> None:
    """Histograma entre p01 e p99, contagem em escala log; título com n e % ausentes."""
    v = s.dropna().astype("float64").to_numpy()
    if len(v) == 0:
        return
    lo, hi = linha["p01"], linha["p99"]
    if lo == hi:
        lo, hi = linha["min"], linha["max"]
    usar_log = lo > 0 and hi / lo > 1e3
    if usar_log:
        bins = np.logspace(np.log10(lo), np.log10(hi), 81)
    else:
        bins = np.linspace(lo, hi, 81) if hi > lo else 10
    fora = int(((v < lo) | (v > hi)).sum())
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.hist(v, bins=bins, color="#3b6ea5")
    ax.set_yscale("log")
    if usar_log:
        ax.set_xscale("log")
    ax.set_xlabel(f"{s.name}  (faixa p01–p99; {fora:,} valores fora)")
    ax.set_ylabel("contagem")
    ax.set_title(f"{s.name}: n={linha['n'] - linha['n_ausentes']:,}, "
                 f"ausentes={100 * linha['frac_ausentes']:.1f}%", fontsize=10)
    fig.tight_layout()
    fig.savefig(destino, dpi=90, metadata={"Software": None})
    plt.close(fig)


def tabela_markdown(p: pd.DataFrame) -> str:
    def fmt(x):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return ""
        return f"{x:.4g}" if isinstance(x, float) else str(x)

    linhas = ["| coluna | categoria | verificar | % ausentes | p01 | p50 | p99 | top |",
              "|---|---|---|---|---|---|---|---|"]
    for r in p.itertuples():
        top = r.top.replace("|", "/") if isinstance(r.top, str) else ""
        linhas.append(
            f"| `{r.coluna}` | {r.categoria} | {'sim' if r.verificar else ''} | "
            f"{100 * r.frac_ausentes:.1f} | {fmt(r.p01)} | {fmt(r.p50)} | {fmt(r.p99)} | "
            f"{top} |")
    return "\n".join(linhas) + "\n"


def perfilar(trilho: str) -> pd.DataFrame:
    caminho = TABELAS[trilho]
    cat = catalogo(trilho)
    figs = FIGURAS / trilho
    figs.mkdir(parents=True, exist_ok=True)
    linhas = []
    for coluna in pq.read_schema(caminho).names:
        s = pd.read_parquet(caminho, columns=[coluna],
                            dtype_backend="numpy_nullable")[coluna]
        linha = perfil_serie(s)
        info = cat[coluna]
        linha.update(categoria=info.categoria.value, verificar=info.verificar,
                     justificativa=info.justificativa)
        if linha["min"] is not None and info.categoria.value not in SEM_HISTOGRAMA:
            histograma(s, linha, figs / f"{nome_arquivo(coluna)}.png")
        if trilho == "A" and coluna == "lamost_subClass":
            (s.value_counts(dropna=False).rename_axis("subclasse").rename("n")
             .reset_index().to_csv(SAIDA / "trailA_subclasse.csv", index=False))
        linhas.append(linha)
        del s
    p = pd.DataFrame(linhas)
    p.to_csv(SAIDA / f"trail{trilho}_perfil.csv", index=False)
    (SAIDA / f"trail{trilho}_perfil.md").write_text(tabela_markdown(p))
    print(f"Trilho {trilho}: {len(p)} colunas, {int(p['n'].iloc[0]):,} linhas")
    return p


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    for trilho in TABELAS:
        perfilar(trilho)


if __name__ == "__main__":
    main()
