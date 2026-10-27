"""Diagrama HR (cor-magnitude absoluta) e diagrama cor-magnitude aparente das Plêiades.

    python scripts/plot_pleiades_hr.py       # roda depois de scripts/plot_pleiades_photo.py

Amostra: todas as estrelas do Gaia DR3 com G < 17 no enquadramento da foto de referência
(4,57° x 3,03° centrado em Alcyone; ver scripts/plot_pleiades_vs_photo.py), não só as
brilhantes. Cache: data/raw/gaia_dr3_pleiades_cone_G17.parquet.

Painéis (HTML interativo, plotly):
- Diagrama HR: BP-RP x magnitude absoluta M_G = G + 5 log10(parallax / mas) - 10.
  Só estrelas com parallax_over_error >= 10 (distância confiável). Sem correção de
  extinção (nas Plêiades A_G ~ 0,1 mag; estrelas de campo distantes têm mais).
  Estrelas muito brilhantes sem paralaxe no DR3 (ex.: Alcyone) não aparecem aqui.
- Diagrama cor-magnitude aparente: BP-RP x G. Não precisa de paralaxe: entram todas
  as estrelas com BP-RP.

Candidato a membro: mesmo critério de scripts/pleiades_region.py (movimento próprio a
menos de 4 mas/ano de (20,0, -45,5) e 6,5 <= parallax <= 8,3 mas).

Saída: figures/pleiades_hr.html
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plot_pleiades_bright import NAMES
from plot_pleiades_photo import CONE_RAW, G_LIMIT, tangent_plane
from plot_pleiades_vs_photo import ALCYONE, PX_PER_DEG
from pleiades_region import PLX_MAX, PLX_MIN, PM_CENTER, PM_RADIUS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "pleiades_hr.html"
PHOTO_W, PHOTO_H = 800, 531  # px da foto de referência
MIN_PARALLAX_OVER_ERROR = 10

SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
FIELD, MEMBER, NAMED = "#b4b2a9", "#2a78d6", "#eb6834"


def load() -> pd.DataFrame:
    d = pd.read_parquet(CONE_RAW, dtype_backend="numpy_nullable")
    xi, eta = tangent_plane(d.ra, d.dec, ALCYONE)
    d = d[(np.abs(xi) < PHOTO_W / 2 / PX_PER_DEG) & (np.abs(eta) < PHOTO_H / 2 / PX_PER_DEG)].copy()
    for c in ("phot_g_mean_mag", "bp_rp", "parallax", "parallax_error", "pmra", "pmdec", "ruwe"):
        d[c] = d[c].astype(float)
    d["parallax_over_error"] = d.parallax / d.parallax_error
    good = d.parallax_over_error >= MIN_PARALLAX_OVER_ERROR
    d["abs_g"] = np.where(good, d.phot_g_mean_mag + 5 * np.log10(d.parallax.where(good)) - 10, np.nan)
    d["dist_pc"] = np.where(good, 1000 / d.parallax, np.nan)
    pm_sep = np.hypot(d.pmra - PM_CENTER[0], d.pmdec - PM_CENTER[1])
    d["is_member"] = ((pm_sep < PM_RADIUS) & d.parallax.between(PLX_MIN, PLX_MAX)).fillna(False)
    d["name"] = ""
    for name, (ra, dec) in NAMES.items():
        sep = np.hypot((d.ra.astype(float) - ra) * np.cos(np.radians(dec)), d.dec.astype(float) - dec)
        if sep.min() < 0.02:
            d.loc[sep.idxmin(), "name"] = name
    return d


def fmt(v, spec, unit=""):
    return "—" if pd.isna(v) else f"{v:{spec}}{unit}"


def hover_text(d: pd.DataFrame) -> list[str]:
    rows = []
    for r in d.itertuples():
        head = f"<b>{r.name}</b><br>" if r.name else ""
        rows.append(
            f"{head}source_id {r.source_id}<br>"
            f"G {fmt(r.phot_g_mean_mag, '.2f')} · BP−RP {fmt(r.bp_rp, '.2f')} · "
            f"M_G {fmt(r.abs_g, '.2f')}<br>"
            f"distância {fmt(r.dist_pc, '.1f', ' pc')} · paralaxe {fmt(r.parallax, '.3f')} ± "
            f"{fmt(r.parallax_error, '.3f', ' mas')}<br>"
            f"pmra {fmt(r.pmra, '.2f')} · pmdec {fmt(r.pmdec, '.2f', ' mas/ano')}<br>"
            f"RUWE {fmt(r.ruwe, '.2f')} · {r.phot_variable_flag}<br>"
            f"{'candidato a membro' if r.is_member else 'estrela de campo'}")
    return rows


def main() -> None:
    d = load()
    d = d[d.bp_rp.notna()]
    d["hover"] = hover_text(d)
    groups = [
        ("estrelas de campo", d[~d.is_member & (d.name == "")], FIELD, 3, 0.55, "circle"),
        ("candidatos a membro", d[d.is_member & (d.name == "")], MEMBER, 5, 0.9, "circle"),
        ("Plêiades com nome", d[d.name != ""], NAMED, 11, 1.0, "star"),
    ]
    n_hr = int(d.abs_g.notna().sum())
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.07, subplot_titles=(
        f"Diagrama HR: magnitude absoluta ({n_hr:,} estrelas com paralaxe confiável)".replace(",", "."),
        f"Diagrama cor-magnitude aparente ({len(d):,} estrelas)".replace(",", ".")))
    for name, s, color, size, alpha, symbol in groups:
        for col, y in ((1, "abs_g"), (2, "phot_g_mean_mag")):
            ss = s[s[y].notna()]
            mode = "markers+text" if symbol == "star" else "markers"
            fig.add_trace(go.Scattergl(
                x=ss.bp_rp, y=ss[y], mode=mode, name=f"{name} ({len(s):,})".replace(",", "."),
                legendgroup=name, showlegend=(col == 1),
                marker=dict(size=size, color=color, opacity=alpha, symbol=symbol,
                            line=dict(width=0.6 if symbol == "star" else 0, color=SURFACE)),
                text=ss.name if symbol == "star" else None, textposition="middle right",
                textfont=dict(color=INK_2, size=10),
                hovertext=ss.hover, hovertemplate="%{hovertext}<extra></extra>"), row=1, col=col)

    axis = dict(gridcolor=GRID, zeroline=False, linecolor=AXIS, tickfont=dict(color=MUTED),
                title_font=dict(color=INK_2))
    fig.update_xaxes(title_text="cor BP−RP (mag) — azul/quente ← → vermelho/fria", **axis)
    fig.update_yaxes(title_text="magnitude absoluta M_G", autorange="reversed", row=1, col=1, **axis)
    fig.update_yaxes(title_text="magnitude aparente G", autorange="reversed", row=1, col=2, **axis)
    fig.update_layout(
        title=dict(text=f"Plêiades (campo da foto, Gaia DR3, G < {G_LIMIT}): passe o mouse "
                        "sobre os pontos; clique na legenda para esconder um grupo",
                   font=dict(color=INK, size=16), x=0.01),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, font=dict(color=INK_2),
        legend=dict(orientation="h", x=0.01, y=-0.12), height=760,
        hoverlabel=dict(bgcolor="white", font=dict(color=INK, size=12)),
        margin=dict(l=60, r=20, t=90, b=90))
    fig.add_annotation(text="M_G = G + 5·log10(paralaxe/mas) − 10, só com paralaxe/erro ≥ 10; "
                            "sem correção de extinção. Estrelas sem paralaxe no DR3 (ex.: Alcyone) "
                            "só aparecem no painel da direita.",
                       xref="paper", yref="paper", x=0.0, y=-0.2, showarrow=False,
                       font=dict(color=MUTED, size=11), xanchor="left")
    OUT.parent.mkdir(exist_ok=True)
    fig.write_html(OUT, include_plotlyjs=True, full_html=True)
    print(OUT)
    print(f"{len(d):,} estrelas com BP-RP; {n_hr:,} no HR; "
          f"{int(d.is_member.sum())} candidatos a membro; nomes: {sorted(d.name[d.name != ''])}")
    print("nomeadas sem M_G:", list(d.loc[(d.name != '') & d.abs_g.isna(), "name"]))


if __name__ == "__main__":
    main()
