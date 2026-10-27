"""Diagramas cor-magnitude e cor-cor do catálogo LAMOST com a fotometria Pan-STARRS.

    python scripts/plot_lamost_color.py      # roda depois de scripts/clean_sentinels.py

Amostra: data/interim/lamost_dr11_lrs.parquet, todas as classes (STAR, GALAXY, QSO),
FiberType == 'Obj', com gmag, rmag e imag do Pan-STARRS. Um espectro por objeto (uID):
o de maior snrg. Não há banda u no catálogo (Pan-STARRS é g, r, i, z, y), por isso o
diagrama cor-cor é g-r x r-i, não u-g x g-r.

Figuras (cada uma com 11 painéis de densidade, escala log):
    figures/lamost_cor_magnitude.png   g-r x gmag (eixo y invertido)
    figures/lamost_cor_cor.png         g-r x r-i
- linha 1: uma classe por painel (STAR, GALAXY, QSO);
- linhas 2-3: estrelas por tipo espectral (O, B, A, F, G, K, M, WD), cada tipo em azul
  sobre todas as estrelas em cinza. Painéis separados em vez de 8 cores num painel só:
  com milhões de pontos as cores se sobrepõem e 8 cores não ficam distinguíveis.

Pan-STARRS satura por volta de g ~ 14: abaixo disso as cores ficam pouco confiáveis.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "interim" / "lamost_dr11_lrs.parquet"
FIG = ROOT / "figures"

SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE = LinearSegmentedColormap.from_list(
    "azul", ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
GRAY = LinearSegmentedColormap.from_list("cinza", ["#efeee9", "#c9c7bf"])

# tipo espectral a partir de subClass (ordem de temperatura, da mais quente para a mais fria)
TYPES = ["O", "B", "A", "F", "G", "K", "M", "WD"]
TYPE_SQL = """CASE
    WHEN regexp_matches(subClass, '^O([0-9]|$)') THEN 'O'
    WHEN regexp_matches(subClass, '^B([0-9]|$)') THEN 'B'
    WHEN regexp_matches(subClass, '^A([0-9]|$)') THEN 'A'
    WHEN regexp_matches(subClass, '^F([0-9]|$)') THEN 'F'
    WHEN regexp_matches(subClass, '^G([0-9]|$)') THEN 'G'
    WHEN regexp_matches(subClass, '^d?K([0-9]|$)') THEN 'K'
    WHEN regexp_matches(subClass, '^(d|g|sd)?M[0-9]') THEN 'M'
    WHEN subClass IN ('WD', 'WDMagnetic') THEN 'WD'
    ELSE 'outros' END"""

DIAGRAMS = {
    "cor_magnitude": dict(x="gr", y="gmag", xlabel="g − r (mag)", ylabel="g (mag, Pan-STARRS)",
                          xlim=(-0.8, 2.2), ylim=(23, 10.5), title="Diagrama cor-magnitude aparente"),
    "cor_cor": dict(x="gr", y="ri", xlabel="g − r (mag)", ylabel="r − i (mag)",
                    xlim=(-0.8, 2.2), ylim=(-0.7, 2.5), title="Diagrama cor-cor"),
}
NBINS = 220


def load() -> dict:
    con = duckdb.connect()
    con.execute("SET memory_limit = '3GB'; SET threads = 4")
    q = f"""
    SELECT Class, {TYPE_SQL} AS sptype, gmag - rmag AS gr, rmag - imag AS ri, gmag
    FROM (SELECT *, row_number() OVER (PARTITION BY uID ORDER BY snrg DESC NULLS LAST, ObsID DESC) AS k
          FROM read_parquet('{SRC}')
          WHERE FiberType = 'Obj' AND gmag IS NOT NULL AND rmag IS NOT NULL AND imag IS NOT NULL)
    WHERE k = 1"""
    return con.execute(q).fetchnumpy()


def density(ax, x, y, cfg, cmap, alpha=1.0):
    xb = np.linspace(*cfg["xlim"], NBINS + 1)
    yb = np.linspace(min(cfg["ylim"]), max(cfg["ylim"]), NBINS + 1)
    h, _, _ = np.histogram2d(x, y, bins=[xb, yb])
    h = np.ma.masked_equal(h.T, 0)
    if h.count() == 0:
        return None
    return ax.pcolormesh(xb, yb, h, cmap=cmap, norm=LogNorm(vmin=1, vmax=max(h.max(), 2)),
                         alpha=alpha, rasterized=True, shading="flat")


def style(ax, cfg, title, n, first_col, last_row):
    ax.set_facecolor(SURFACE)
    ax.set_xlim(*cfg["xlim"]); ax.set_ylim(*cfg["ylim"])
    ax.set_title(f"{title}  ({n:,})".replace(",", "."), color=INK, fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=7.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    if first_col:
        ax.set_ylabel(cfg["ylabel"], color=INK_2, fontsize=8.5)
    if last_row:
        ax.set_xlabel(cfg["xlabel"], color=INK_2, fontsize=8.5)


def plot(d: dict, key: str, cfg: dict) -> None:
    x, y = d[cfg["x"]], d[cfg["y"]]
    cls, typ = d["Class"], d["sptype"]
    fig = plt.figure(figsize=(16, 12.5), facecolor=SURFACE)
    gs = fig.add_gridspec(3, 4, hspace=0.32, wspace=0.12)

    mesh = None
    for j, c in enumerate(["STAR", "GALAXY", "QSO"]):
        ax = fig.add_subplot(gs[0, j])
        m = cls == c
        mesh = density(ax, x[m], y[m], cfg, BLUE) or mesh
        style(ax, cfg, c, int(m.sum()), j == 0, False)
    note = fig.add_subplot(gs[0, 3]); note.axis("off")
    note.text(0, 0.95, "Como ler", color=INK, fontsize=10, va="top", weight="bold")
    note.text(0, 0.82, "Cada painel é um histograma 2D:\na cor mostra quantos objetos\n"
              "caem em cada célula (escala log;\nazul escuro = mais objetos).\n\n"
              "Linha 1: por classe LAMOST.\nLinhas 2-3: estrelas por tipo\nespectral (azul) sobre todas as\n"
              "estrelas (cinza).\n\nUm espectro por objeto (uID).\nPan-STARRS satura em g ≲ 14.",
              color=INK_2, fontsize=8.8, va="top", linespacing=1.35)

    star = cls == "STAR"
    for i, t in enumerate(TYPES):
        ax = fig.add_subplot(gs[1 + i // 4, i % 4])
        density(ax, x[star], y[star], cfg, GRAY)
        m = star & (typ == t)
        density(ax, x[m], y[m], cfg, BLUE)
        style(ax, cfg, f"tipo {t}", int(m.sum()), i % 4 == 0, i >= 4)
        if not m.any():
            ax.text(0.5, 0.5, "nenhuma estrela deste tipo\ncom g, r e i do Pan-STARRS", ha="center",
                    va="center", transform=ax.transAxes, color=INK_2, fontsize=9)

    n_other = int((star & (typ == "outros")).sum())
    fig.suptitle(f"LAMOST DR11 LRS — {cfg['title']} com fotometria Pan-STARRS", color=INK,
                 fontsize=14, x=0.065, ha="left", y=0.955)
    n_other_txt = f"{n_other:,}".replace(",", ".")
    fig.text(0.065, 0.025, f"Estrelas fora de O-M/WD (DoubleStar, Carbon, CV, EM…): {n_other_txt} "
             "— aparecem só no cinza.", color=MUTED, fontsize=8.5)
    if mesh is not None:
        cax = note.inset_axes([0, -0.02, 0.85, 0.045])  # abaixo do texto, dentro do painel de notas
        cb = fig.colorbar(mesh, cax=cax, orientation="horizontal")
        cb.set_label("objetos por célula (painel da linha 1)", color=INK_2, fontsize=8)
        cb.ax.tick_params(colors=MUTED, labelsize=7); cb.outline.set_visible(False)
    out = FIG / f"lamost_{key}.png"
    fig.savefig(out, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(out)


def main() -> None:
    d = load()
    FIG.mkdir(exist_ok=True)
    print({c: int((d["Class"] == c).sum()) for c in ("STAR", "GALAXY", "QSO")},
          {t: int(((d["Class"] == "STAR") & (d["sptype"] == t)).sum()) for t in TYPES + ["outros"]})
    for key, cfg in DIAGRAMS.items():
        plot(d, key, cfg)


if __name__ == "__main__":
    main()
