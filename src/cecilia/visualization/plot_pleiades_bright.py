"""Só as estrelas mais brilhantes do campo das Plêiades: fluxo G > média + 1,5 desvio-padrão.

    python scripts/plot_pleiades_bright.py   # roda depois de scripts/plot_pleiades_photo.py

Amostra: as estrelas do Gaia DR3 com G < 17 no mesmo campo de 4,6° x 3,1° da imagem
figures/pleiades_ceu.png (cache data/raw/gaia_dr3_pleiades_cone_G17.parquet).
Fluxo relativo = 10^(-0,4 G). O corte média + 1,5 sigma não depende da unidade do fluxo,
então dá o mesmo resultado que usar phot_g_mean_flux em e-/s.

Os nomes das Plêiades só são escritos quando há uma estrela do Gaia a menos de 0,02° da
posição listada abaixo (J2000, aproximada).

Saída: figures/pleiades_brilhantes.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_pleiades_photo import (BP_RP_MAX, BP_RP_MIN, CONE_RAW, DEC0, G_LIMIT, HALF_H, HALF_W,
                                 RA0, STAR_COLORS, tangent_plane)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "pleiades_brilhantes.png"
N_SIGMA = 1.5

NAMES = {"Alcyone": (56.871, 24.105), "Atlas": (57.291, 24.053), "Electra": (56.219, 24.113),
         "Maia": (56.457, 24.368), "Merope": (56.582, 23.948), "Taygeta": (56.302, 24.467),
         "Pleione": (57.297, 24.137), "Celaeno": (56.201, 24.289), "Asterope": (56.477, 24.555)}


def main() -> None:
    d = pd.read_parquet(CONE_RAW, dtype_backend="numpy_nullable")
    d["xi"], d["eta"] = tangent_plane(d.ra, d.dec)
    d = d[(d.xi.abs() < HALF_W) & (d.eta.abs() < HALF_H)].copy()
    flux = 10 ** (-0.4 * d.phot_g_mean_mag.astype(float))
    cut = flux.mean() + N_SIGMA * flux.std()
    g_cut = -2.5 * np.log10(cut)
    b = d[flux > cut].sort_values("phot_g_mean_mag", ascending=False)
    print(f"{len(b)} de {len(d):,} estrelas com fluxo > média + {N_SIGMA} sigma (G < {g_cut:.2f})")

    fig, ax = plt.subplots(figsize=(12, 8.4), facecolor="black")
    ax.set_facecolor("black")
    g = b.phot_g_mean_mag.to_numpy(float)
    colors = STAR_COLORS(np.clip((np.nan_to_num(b.bp_rp.to_numpy(float), nan=0.8) - BP_RP_MIN)
                                 / (BP_RP_MAX - BP_RP_MIN), 0, 1))
    size = 0.4 * (10 ** (-0.4 * (g - G_LIMIT))) ** 0.45
    for scale, alpha in ((60, 0.025), (18, 0.06), (5, 0.18), (1, 1.0)):
        ax.scatter(b.xi, b.eta, s=size * scale, c=colors, alpha=alpha, linewidths=0)

    halo = [pe.withStroke(linewidth=3, foreground="black")]
    for name, (ra, dec) in NAMES.items():
        sep = np.hypot((b.ra.astype(float) - ra) * np.cos(np.radians(dec)), b.dec.astype(float) - dec)
        if len(sep) and sep.min() < 0.02:
            star = b.iloc[int(np.argmin(sep.to_numpy()))]
            ax.annotate(f"{name}  G {star.phot_g_mean_mag:.1f}".replace(".", ","),
                        (star.xi, star.eta), xytext=(9, 7), textcoords="offset points",
                        color="#e6e6e6", fontsize=9, path_effects=halo)

    ax.set_xlim(HALF_W, -HALF_W)  # leste à esquerda
    ax.set_ylim(-HALF_H, HALF_H)
    ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_color("#444444")
    ax.tick_params(colors="#9a9a9a", labelsize=8.5)
    ax.grid(color="#2a2a2a", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_xlabel(f"ΔRA (graus, leste à esquerda) a partir de RA {RA0}°", color="#bdbdbd", fontsize=9.5)
    ax.set_ylabel(f"ΔDec (graus) a partir de Dec +{DEC0}°", color="#bdbdbd", fontsize=9.5)
    ax.set_title(f"Plêiades: as {len(b)} estrelas com fluxo G acima de média + {N_SIGMA:g}σ "
                 f"(G < {g_cut:.2f}) entre {len(d):,} do campo".replace(",", ".").replace("1.5", "1,5")
                 .replace(f"{g_cut:.2f}", f"{g_cut:.2f}".replace(".", ",")),
                 color="#f0f0f0", fontsize=12, loc="left", pad=10)
    fig.tight_layout()
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=170, facecolor="black")
    print(OUT)


if __name__ == "__main__":
    main()
