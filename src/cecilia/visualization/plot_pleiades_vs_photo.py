"""Gaia DR3 ao lado da foto de referência das Plêiades, no mesmo enquadramento.

    python scripts/plot_pleiades_vs_photo.py # roda depois de scripts/plot_pleiades_photo.py

Foto de referência: figures/referencia/pleiades_foto.webp (800 x 531 px), enviada pelo
usuário, sem créditos/metadados de origem.

Enquadramento medido na foto: Alcyone está no centro e a distância Atlas-Electra
(0,98°) ocupa ~170 px, ou seja ~175 px por grau. O painel do Gaia usa o mesmo centro
(Alcyone) e o mesmo campo: 800/175 x 531/175 = 4,57° x 3,03°. A medida é feita à mão,
então o alinhamento é aproximado (alguns pixels).

Saída: figures/pleiades_gaia_vs_foto.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from plot_pleiades_photo import CONE_RAW, G_LIMIT, draw, tangent_plane

ROOT = Path(__file__).resolve().parents[1]
PHOTO = ROOT / "figures" / "referencia" / "pleiades_foto.webp"
OUT = ROOT / "figures" / "pleiades_gaia_vs_foto.png"

ALCYONE = (56.871, 24.105)
PX_PER_DEG = 175


def main() -> None:
    photo = Image.open(PHOTO).convert("RGB")
    w, h = photo.size
    half = (w / 2 / PX_PER_DEG, h / 2 / PX_PER_DEG)

    d = pd.read_parquet(CONE_RAW, dtype_backend="numpy_nullable")
    xi, eta = tangent_plane(d.ra, d.dec, ALCYONE)
    d = d[(np.abs(xi) < half[0] + 0.05) & (np.abs(eta) < half[1] + 0.05)]

    fig, (a, b) = plt.subplots(1, 2, figsize=(16, 16 / 2 * h / w + 0.9), facecolor="black")
    draw(a, d, "", center=ALCYONE, half=half)
    b.imshow(np.asarray(photo), extent=(half[0], -half[0], -half[1], half[1]))
    b.set_xlim(half[0], -half[0]); b.set_ylim(-half[1], half[1])
    b.set_xticks([]); b.set_yticks([])
    for s in b.spines.values():
        s.set_visible(False)

    label = dict(color="#e6e6e6", fontsize=11, va="top", ha="left")
    a.text(0.015, 0.975, f"Gaia DR3: {len(d):,} estrelas com G < {G_LIMIT}".replace(",", "."),
           transform=a.transAxes, **label)
    b.text(0.015, 0.975, "Foto de referência", transform=b.transAxes, **label)
    fig.text(0.5, 0.02, f"Mesmo enquadramento: {2 * half[0]:.2f}° × {2 * half[1]:.2f}° centrado em "
             f"Alcyone; norte para cima, leste à esquerda. A nebulosa da foto é poeira "
             "iluminada e não está no catálogo.".replace(".", ",", 2),
             color="#9a9a9a", fontsize=9, ha="center")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.06, wspace=0.01)
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=160, facecolor="black")
    print(OUT)


if __name__ == "__main__":
    main()
