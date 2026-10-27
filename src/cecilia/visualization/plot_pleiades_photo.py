"""Imagem das Plêiades em fundo preto, para comparar com uma foto real.

    python scripts/plot_pleiades_photo.py    # roda depois de scripts/pleiades_region.py

Dois painéis no mesmo campo (4,6° x 3,1°, norte para cima, leste à esquerda):
- esquerda: todas as estrelas do Gaia DR3 com G < 17 no campo — o que uma câmera
  registraria. Cone de 2,8° no Gaia DR3 do VizieR (I/355/gaiadr3, espelho CfA), com
  cache em data/raw/gaia_dr3_pleiades_cone_G17.parquet. (O mesmo cone no Gaia Archive
  estoura o limite de 60 s do usuário anônimo.)
- direita: só as estrelas da nossa amostra LAMOST (data/interim/pleiades_region.parquet).
  O LAMOST não observa estrelas muito brilhantes (a mais brilhante aqui tem G ~ 8,9),
  então as Sete Irmãs (G ~ 3-6) não aparecem.

Cada estrela é um ponto com halo: tamanho e brilho crescem com o fluxo (10^(-0,4 G)),
cor vem de bp_rp (azul-branco para estrelas quentes, laranja-vermelho para frias).
A nebulosa de reflexão da foto é poeira iluminada, não está em nenhum catálogo de
estrelas e por isso não aparece.

Saída: figures/pleiades_ceu.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

import fetch_raw

ROOT = Path(__file__).resolve().parents[1]
REGION = ROOT / "data" / "interim" / "pleiades_region.parquet"
CONE_RAW = fetch_raw.RAW / "gaia_dr3_pleiades_cone_G17.parquet"
OUT = ROOT / "figures" / "pleiades_ceu.png"

RA0, DEC0 = 56.75, 24.12
HALF_W, HALF_H = 2.3, 1.53  # graus; ~ campo da foto de referência (4,6° x 3,1°)
G_LIMIT, CONE_RADIUS = 17, 2.8  # o cone cobre os cantos do campo
VIZIER_CAT = "I/355/gaiadr3"
# nomes do VizieR -> nomes do gaia_source (RA/Dec ICRS na época 2016.0, como no Gaia)
VIZIER_COLS = {"Source": "source_id", "RA_ICRS": "ra", "DE_ICRS": "dec", "Gmag": "phot_g_mean_mag",
               "BP-RP": "bp_rp", "Plx": "parallax", "e_Plx": "parallax_error", "pmRA": "pmra",
               "pmDE": "pmdec", "RUWE": "ruwe", "VarFlag": "phot_variable_flag"}

# bp_rp -> cor aproximada da estrela (tipos O/B ... M)
STAR_COLORS = LinearSegmentedColormap.from_list("estrelas", [
    (0.0, "#9bb0ff"), (0.25, "#cad7ff"), (0.4, "#f8f7ff"), (0.6, "#fff4e8"),
    (0.75, "#ffd2a1"), (0.9, "#ffb56c"), (1.0, "#ff8b4d")])
BP_RP_MIN, BP_RP_MAX = -0.3, 3.0


def fetch_cone() -> pd.DataFrame:
    if not CONE_RAW.exists():
        import astropy.units as u
        from astropy.coordinates import SkyCoord
        from astroquery.vizier import Vizier

        v = Vizier(columns=list(VIZIER_COLS), column_filters={"Gmag": f"<{G_LIMIT}"},
                   row_limit=-1, vizier_server=fetch_raw.VIZIER_CFA)
        t = v.query_region(SkyCoord(RA0, DEC0, unit="deg"), radius=CONE_RADIUS * u.deg,
                           catalog=VIZIER_CAT)[0]
        df = t.to_pandas().rename(columns=VIZIER_COLS)[list(VIZIER_COLS.values())]
        if not df.source_id.is_unique:
            raise SystemExit("source_id repetido no resultado do VizieR")
        df.to_parquet(CONE_RAW, index=False)
        fetch_raw.record(CONE_RAW, f"Gaia DR3 (VizieR {VIZIER_CAT}, {fetch_raw.VIZIER_CFA})",
                         f"Vizier(columns={list(VIZIER_COLS)}, column_filters={{'Gmag': '<{G_LIMIT}'}}, "
                         f"row_limit=-1).query_region(({RA0}, {DEC0}), radius={CONE_RADIUS} deg, "
                         f"catalog='{VIZIER_CAT}')", len(df))
    return pd.read_parquet(CONE_RAW, dtype_backend="numpy_nullable")


def tangent_plane(ra, dec, center=(RA0, DEC0)):
    """Projeção gnômica em torno de center; xi cresce para leste (vai para a esquerda)."""
    ra, dec = np.radians(np.asarray(ra, float)), np.radians(np.asarray(dec, float))
    ra0, dec0 = np.radians(center[0]), np.radians(center[1])
    cosc = np.sin(dec0) * np.sin(dec) + np.cos(dec0) * np.cos(dec) * np.cos(ra - ra0)
    xi = np.cos(dec) * np.sin(ra - ra0) / cosc
    eta = (np.cos(dec0) * np.sin(dec) - np.sin(dec0) * np.cos(dec) * np.cos(ra - ra0)) / cosc
    return np.degrees(xi), np.degrees(eta)


def draw(ax, d: pd.DataFrame, title: str, center=(RA0, DEC0), half=(HALF_W, HALF_H)) -> None:
    ax.set_facecolor("black")
    xi, eta = tangent_plane(d.ra, d.dec, center)
    g = d.phot_g_mean_mag.to_numpy(float)
    color_val = np.clip((np.nan_to_num(d.bp_rp.to_numpy(float), nan=0.8) - BP_RP_MIN)
                        / (BP_RP_MAX - BP_RP_MIN), 0, 1)
    colors = STAR_COLORS(color_val)
    # estrelas fracas mais escuras (como numa foto com exposição curta): escala de 15% a 100%
    dim = np.clip(0.15 + 0.85 * np.clip((G_LIMIT - g) / (G_LIMIT - 8), 0, 1) ** 1.5, 0.15, 1)
    colors[:, :3] *= dim[:, None]
    rel = 10 ** (-0.4 * (g - G_LIMIT))           # fluxo relativo à estrela mais fraca
    order = np.argsort(-g)                         # fracas primeiro, brilhantes por cima
    xi, eta, colors, size = xi[order], eta[order], colors[order], 0.4 * rel[order] ** 0.45
    # núcleo para todas; halos largos e transparentes só para as brilhantes (G < 9),
    # imitando o espalhamento de luz das estrelas fortes numa foto
    bright = g[order] < 9
    for scale, alpha in ((60, 0.025), (18, 0.06), (5, 0.18)):
        ax.scatter(xi[bright], eta[bright], s=size[bright] * scale, c=colors[bright],
                   alpha=alpha, linewidths=0)
    ax.scatter(xi, eta, s=size, c=colors, alpha=1.0, linewidths=0)
    ax.set_xlim(half[0], -half[0])                 # leste à esquerda
    ax.set_ylim(-half[1], half[1])
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    if title:
        ax.text(0.015, 0.975, title, transform=ax.transAxes, color="#d9d9d9", fontsize=10.5,
                va="top")


def main() -> None:
    gaia = fetch_cone()
    lamost = pd.read_parquet(REGION, columns=["ra", "dec", "phot_g_mean_mag", "bp_rp"],
                             dtype_backend="numpy_nullable")
    in_field = lambda d: d[(lambda x, e: (abs(x) < HALF_W + 0.05) & (abs(e) < HALF_H + 0.05))(
        *tangent_plane(d.ra, d.dec))]
    gaia, lamost = in_field(gaia), in_field(lamost)

    fig, (a, b) = plt.subplots(1, 2, figsize=(18, 6.4), facecolor="black")
    draw(a, gaia, f"Gaia DR3, todas as estrelas com G < {G_LIMIT} ({len(gaia):,})".replace(",", "."))
    draw(b, lamost, f"Nossa amostra LAMOST ({len(lamost):,}); sem as estrelas brilhantes"
         .replace(",", "."))
    fig.text(0.5, 0.015, f"Campo de 4,6° × 3,1° centrado em RA {RA0}°, Dec +{DEC0}°; "
             "norte para cima, leste à esquerda. Tamanho/brilho pela magnitude G, cor por bp_rp.",
             color="#9a9a9a", fontsize=9, ha="center")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.05, wspace=0.01)
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=160, facecolor="black")
    print(OUT)


if __name__ == "__main__":
    main()
