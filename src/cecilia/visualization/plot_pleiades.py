"""Gráficos da região das Plêiades (Melotte 22 / M45).

    python scripts/plot_pleiades.py          # roda depois de scripts/pleiades_region.py

Saídas:
    figures/pleiades_parametros.png   8 painéis: movimento próprio (pmra x pmdec, pmra,
                                      pmdec), céu (ra x dec), paralaxe, magnitude G,
                                      fluxo G e phot_variable_flag
    figures/pleiades_3d.html          mapa 3D interativo (plotly), coordenadas
                                      galácticas cartesianas centradas no Sol

Candidatos a membro (is_member) em azul; estrelas de campo do mesmo cone em cinza.
Os histogramas mostram a fração de cada grupo por intervalo, para que os 717 membros
fiquem comparáveis às ~49 mil estrelas de campo.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "interim" / "pleiades_region.parquet"
FIG = ROOT / "figures"

# Paleta de referência (skill dataviz)
SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
MEMBER, FIELD = "#2a78d6", "#b4b2a9"

COLS = ["source_id", "ra", "dec", "l", "b", "pmra", "pmdec", "parallax", "dist_pc",
        "phot_g_mean_mag", "phot_g_mean_flux", "phot_variable_flag", "is_member"]


def style(ax, title, xlabel, ylabel):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    ax.set_xlabel(xlabel, color=INK_2, fontsize=8.5)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=8.5)
    ax.tick_params(colors=MUTED, labelsize=7.5)
    ax.grid(color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)


def hist(ax, d, col, bins, logx=False):
    for mask, color, alpha in ((~d.is_member, FIELD, 0.85), (d.is_member, MEMBER, 0.75)):
        v = d.loc[mask, col].dropna()
        ax.hist(v, bins=bins, weights=np.full(len(v), 1 / len(v)), color=color, alpha=alpha,
                edgecolor=SURFACE, linewidth=0.4)
    if logx:
        ax.set_xscale("log")


def scatter(ax, d, x, y):
    f, m = d[~d.is_member], d[d.is_member]
    ax.scatter(f[x], f[y], s=1.5, color=FIELD, alpha=0.5, linewidths=0, rasterized=True)
    ax.scatter(m[x], m[y], s=6, color=MEMBER, edgecolor=SURFACE, linewidths=0.3, rasterized=True)


def panels(d: pd.DataFrame) -> None:
    n_m, n_f = int(d.is_member.sum()), int((~d.is_member).sum())
    fig, axes = plt.subplots(2, 4, figsize=(17, 8.6), facecolor=SURFACE)
    (a1, a2, a3, a4), (b1, b2, b3, b4) = axes

    scatter(a1, d, "pmra", "pmdec")
    a1.set_xlim(-20, 55); a1.set_ylim(-70, 15)
    style(a1, "Movimento próprio", "pmra (mas/ano)", "pmdec (mas/ano)")

    hist(a2, d, "pmra", np.arange(-20, 55.5, 1))
    style(a2, "pmra", "pmra (mas/ano)", "fração do grupo")
    hist(a3, d, "pmdec", np.arange(-70, 15.5, 1))
    style(a3, "pmdec", "pmdec (mas/ano)", "fração do grupo")

    scatter(a4, d, "ra", "dec")
    a4.invert_xaxis()  # leste à esquerda, como no céu
    a4.set_aspect(1 / np.cos(np.radians(24.12)))
    style(a4, "Posição no céu (cone de 5°)", "ra (graus)", "dec (graus)")

    hist(b1, d, "parallax", np.arange(-1, 12.01, 0.2))
    style(b1, "Paralaxe", "parallax (mas)", "fração do grupo")
    b1.annotate("7,37 mas ≈ 136 pc", xy=(7.37, 0), xytext=(8.6, 0.12), color=INK_2, fontsize=8,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))

    hist(b2, d, "phot_g_mean_mag", np.arange(5, 21.01, 0.25))
    style(b2, "Magnitude G", "phot_g_mean_mag", "fração do grupo")
    b2.invert_xaxis()  # mais brilhante à direita

    hist(b3, d, "phot_g_mean_flux", np.logspace(2, 8, 61), logx=True)
    style(b3, "Fluxo G (mesma informação que a magnitude)", "phot_g_mean_flux (e⁻/s)", "fração do grupo")

    groups = [("campo", ~d.is_member, FIELD), ("membros", d.is_member, MEMBER)]
    shares = [(d.loc[m, "phot_variable_flag"] == "VARIABLE").mean() for _, m, _ in groups]
    counts = [int((d.loc[m, "phot_variable_flag"] == "VARIABLE").sum()) for _, m, _ in groups]
    bars = b4.bar([g[0] for g in groups], shares, color=[g[2] for g in groups], width=0.55)
    for bar, share, n in zip(bars, shares, counts):
        b4.text(bar.get_x() + bar.get_width() / 2, share, f"{share:.1%}".replace(".", ",") + f"\n({n:,})".replace(",", "."),
                ha="center", va="bottom", color=INK_2, fontsize=8.5)
    b4.set_ylim(0, max(shares) * 1.35)
    b4.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    style(b4, "phot_variable_flag = VARIABLE", "", "fração do grupo")

    fig.suptitle(f"Plêiades (Melotte 22 / M45): {n_m} candidatos a membro e "
                 f"{n_f:,} estrelas de campo no mesmo cone".replace(",", "."),
                 color=INK, fontsize=13, x=0.01, ha="left", y=0.995)
    fig.legend(handles=[
        Line2D([], [], marker="o", linestyle="", color=MEMBER, markersize=7,
               label="candidatos a membro (movimento próprio e paralaxe do aglomerado)"),
        Line2D([], [], marker="o", linestyle="", color=FIELD, markersize=7,
               label="estrelas de campo no cone de 5°")],
        loc="upper left", bbox_to_anchor=(0.01, 0.965), ncol=2, frameon=False,
        fontsize=9, labelcolor=INK_2)
    fig.text(0.01, 0.005, "NOT_AVAILABLE em phot_variable_flag significa que o Gaia não "
             "classificou a estrela, não que ela seja constante.", color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 0.93), h_pad=2.2, w_pad=1.8)
    out = FIG / "pleiades_parametros.png"
    fig.savefig(out, dpi=170, facecolor=SURFACE)
    print(out)


def map3d(d: pd.DataFrame, max_pc: float = 300) -> None:
    d = d[(d.parallax > 1000 / max_pc)].copy()
    lr, br = np.radians(d.l), np.radians(d.b)
    d["x"] = d.dist_pc * np.cos(br) * np.cos(lr)  # para o centro galáctico
    d["y"] = d.dist_pc * np.cos(br) * np.sin(lr)  # sentido da rotação galáctica
    d["z"] = d.dist_pc * np.sin(br)               # para o polo norte galáctico
    fig = go.Figure()
    for name, mask, color, size in (("estrelas de campo", ~d.is_member, FIELD, 2),
                                    ("candidatos a membro", d.is_member, MEMBER, 3)):
        s = d[mask]
        fig.add_trace(go.Scatter3d(
            x=s.x, y=s.y, z=s.z, mode="markers", name=f"{name} ({len(s):,})".replace(",", "."),
            marker=dict(size=size, color=color, opacity=0.85 if size == 3 else 0.45),
            customdata=np.stack([s.source_id.astype(str), s.dist_pc, s.phot_g_mean_mag], axis=1),
            hovertemplate="source_id %{customdata[0]}<br>distância %{customdata[1]:.1f} pc"
                          "<br>G %{customdata[2]:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[0], mode="markers+text", name="Sol",
                               marker=dict(size=5, color=INK), text=["Sol"],
                               textposition="top center", hoverinfo="name"))
    axis = dict(backgroundcolor=SURFACE, gridcolor=GRID, zerolinecolor=AXIS, color=INK_2)
    fig.update_layout(
        title=dict(text=f"Plêiades em 3D (estrelas do cone até {max_pc:.0f} pc; distância = 1000/parallax)",
                   font=dict(color=INK, size=15)),
        paper_bgcolor=SURFACE, font=dict(color=INK_2),
        scene=dict(xaxis=dict(title="x (pc) → centro galáctico", **axis),
                   yaxis=dict(title="y (pc) → rotação galáctica", **axis),
                   zaxis=dict(title="z (pc) → polo norte galáctico", **axis),
                   aspectmode="data"),
        legend=dict(x=0.01, y=0.98), margin=dict(l=0, r=0, t=50, b=0))
    out = FIG / "pleiades_3d.html"
    fig.write_html(out, include_plotlyjs=True, full_html=True)
    print(out)


def main() -> None:
    d = pd.read_parquet(SRC, columns=COLS)
    FIG.mkdir(exist_ok=True)
    panels(d)
    map3d(d)


if __name__ == "__main__":
    main()
