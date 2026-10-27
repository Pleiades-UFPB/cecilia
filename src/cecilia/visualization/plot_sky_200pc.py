"""Mapa do céu em coordenadas galácticas das estrelas a menos de 200 pc.

    python scripts/plot_sky_200pc.py         # roda depois de scripts/filter_200pc.py

Projeção Mollweide (área igual), convenção astronômica: centro galáctico (l = 0°) no
meio, l crescendo para a esquerda. Trilho A aparece como densidade (estrelas por grau
quadrado, em células de área igual: passos iguais em l e em sen b); Trilho B, com só
algumas dezenas de estrelas, aparece ponto a ponto.

Saída: figures/sky_galactic_200pc.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "figures" / "sky_galactic_200pc.png"

# Paleta de referência (skill dataviz): superfície, tintas, rampa azul, laranja categórico.
SURFACE, INK, INK_2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ORANGE = "#eb6834"

N_L, N_SINB = 240, 120  # 1,5° em l; 120 passos iguais em sen b


def to_x(l_deg: np.ndarray) -> np.ndarray:
    """Longitude galáctica -> x da projeção (radianos), com l crescendo para a esquerda."""
    return -np.radians((np.asarray(l_deg) + 180) % 360 - 180)


def main() -> None:
    a = pd.read_parquet(INTERIM / "trailA_lamost_gaia_2mass_200pc.parquet", columns=["l", "b"])
    b = pd.read_parquet(INTERIM / "trailB_apokasc_gaia_2mass_200pc.parquet", columns=["l", "b"])

    x_edges = np.linspace(-np.pi, np.pi, N_L + 1)
    s_edges = np.linspace(-1, 1, N_SINB + 1)
    counts, _, _ = np.histogram2d(to_x(a.l), np.sin(np.radians(a.b)), bins=[x_edges, s_edges])
    cell_deg2 = (2 * np.pi / N_L) * (2 / N_SINB) * (180 / np.pi) ** 2
    density = np.ma.masked_equal(counts.T, 0) / cell_deg2
    b_edges = np.arcsin(s_edges)

    fig = plt.figure(figsize=(11, 6.2), facecolor=SURFACE)
    ax = fig.add_subplot(projection="mollweide", facecolor=SURFACE)
    cmap = LinearSegmentedColormap.from_list("azul", BLUE_RAMP)
    mesh = ax.pcolormesh(x_edges, b_edges, density, cmap=cmap,
                         norm=LogNorm(vmin=density.min(), vmax=density.max()),
                         shading="flat", rasterized=True)
    ax.scatter(to_x(b.l), np.radians(b.b), s=30, color=ORANGE, edgecolor=SURFACE,
               linewidth=1.2, zorder=3)

    # Grade e eixos recessivos; rótulos de l na convenção astronômica.
    ax.grid(color=GRID, linewidth=0.6)
    ticks = np.arange(-150, 181, 30)
    ax.set_xticks(np.radians(ticks))
    # contorno da cor da superfície para os rótulos de l continuarem legíveis sobre os dados
    halo = [pe.withStroke(linewidth=2.5, foreground=SURFACE)]
    ax.set_xticklabels([f"{int((-t) % 360)}°" for t in ticks], color=INK_2, fontsize=8,
                       path_effects=halo)
    ax.tick_params(axis="y", colors=MUTED, labelsize=8)
    ax.set_xlabel("longitude galáctica l", color=INK_2, fontsize=9)
    ax.set_ylabel("latitude galáctica b", color=INK_2, fontsize=9)
    for s in ax.spines.values():
        s.set_edgecolor("#c3c2b7")

    ax.set_title(f"Estrelas a menos de 200 pc em coordenadas galácticas\n"
                 f"{len(a):,} do Trilho A (LAMOST) e {len(b)} do Trilho B (APOKASC-3)"
                 .replace(",", "."), color=INK, fontsize=12, pad=38)

    legend = [Line2D([], [], marker="s", linestyle="", markersize=9, color=BLUE_RAMP[4],
                     label="Trilho A — LAMOST (densidade)"),
              Line2D([], [], marker="o", linestyle="", markersize=7, color=ORANGE,
                     markeredgecolor=SURFACE, label="Trilho B — APOKASC-3 (cada estrela)")]
    leg = ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 1.0),
                    frameon=False, fontsize=9, labelcolor=INK_2, ncol=2)
    leg.set_zorder(5)

    cb = fig.colorbar(mesh, ax=ax, orientation="horizontal", fraction=0.04, pad=0.1,
                      shrink=0.45, anchor=(0.5, 1))
    cb.set_label("estrelas do Trilho A por grau quadrado", color=INK_2, fontsize=9)
    cb.ax.tick_params(colors=MUTED, labelsize=8)
    cb.outline.set_visible(False)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor=SURFACE, bbox_inches="tight")
    print(OUT)


if __name__ == "__main__":
    main()
