"""Aquecimento da Fase 01: diagrama HR observacional de 10 estrelas famosas.

Lê uma tabela digitada à mão (valores conferidos no SIMBAD), calcula a magnitude
absoluta M_V a partir da magnitude aparente V e da paralaxe, e salva um diagrama
HR observacional (índice de cor B−V × magnitude absoluta M_V).

Uso:
    uv run python -m cecilia.aquecimento

Observação: o vocabulário define o diagrama HR do projeto como M_G × BP−RP (Gaia).
Aqui usamos fotometria Johnson (V, B−V) porque estrelas muito brilhantes, como
Sirius e Betelgeuse, saturam no Gaia. A conta de magnitude absoluta é a mesma.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem janela: roda no CI e em terminais sem display

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_TABELA = RAIZ / "data" / "aquecimento" / "estrelas_famosas.csv"
CAMINHO_FIGURA = RAIZ / "outputs" / "fase01" / "hr_aquecimento.png"

COLUNAS_OBRIGATORIAS = ["nome", "id_simbad", "tipo_mk", "V", "B_V", "paralaxe_mas", "fonte"]


def carregar_estrelas(caminho: Path | str = CAMINHO_TABELA) -> pd.DataFrame:
    """Lê a tabela de estrelas e confere colunas obrigatórias e valores ausentes.

    Linhas iniciadas por '#' no CSV são comentários (cabeçalho com a origem dos dados).
    Levanta ValueError se faltar alguma coluna ou algum valor.
    """
    df = pd.read_csv(caminho, comment="#")
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas obrigatórias ausentes em {caminho}: {faltando}")
    ausentes = df[COLUNAS_OBRIGATORIAS].isna().sum()
    ausentes = ausentes[ausentes > 0]
    if not ausentes.empty:
        raise ValueError(f"Valores ausentes em {caminho}: {ausentes.to_dict()}")
    return df


def magnitude_absoluta(m, paralaxe_mas):
    """Magnitude absoluta a partir da magnitude aparente e da paralaxe (em mas).

    Fórmula do vocabulário: M = m + 5·log10(ϖ/1000) + 5.
    Ex.: ϖ = 100 mas → distância de 10 pc → M = m.

    Não corrige extinção. Para as estrelas próximas da tabela o efeito é pequeno;
    para as supergigantes distantes (Rigel, Betelgeuse) M_V fica um pouco subestimada
    em brilho.

    Aceita escalares ou arrays. Levanta ValueError se alguma paralaxe for ≤ 0,
    porque a distância 1000/ϖ fica indefinida.
    """
    m = np.asarray(m, dtype=float)
    paralaxe = np.asarray(paralaxe_mas, dtype=float)
    if np.any(paralaxe <= 0):
        raise ValueError("Paralaxe deve ser positiva (em mas) para calcular a distância.")
    resultado = m + 5 * np.log10(paralaxe / 1000) + 5
    return float(resultado) if resultado.ndim == 0 else resultado


def plotar_hr(df: pd.DataFrame, caminho_saida: Path | str):
    """Desenha o diagrama HR observacional (B−V × M_V) e salva em PNG.

    Espera as colunas 'B_V', 'M_V' e 'nome'. O eixo y é invertido (mais brilhante
    no alto); o eixo x cresce para a direita (estrelas quentes, de B−V menor, à
    esquerda). Retorna (fig, ax) para inspeção nos testes.
    """
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(df["B_V"], df["M_V"], c=df["B_V"], cmap="RdYlBu_r", edgecolors="black", s=60)
    for _, estrela in df.iterrows():
        ax.annotate(
            estrela["nome"],
            (estrela["B_V"], estrela["M_V"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=9,
        )
    ax.invert_yaxis()
    ax.set_xlabel("Índice de cor B−V (mag)")
    ax.set_ylabel("Magnitude absoluta M_V (mag)")
    ax.set_title("Diagrama HR observacional — aquecimento")
    ax.grid(alpha=0.3)

    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
    return fig, ax


def main() -> None:
    """Lê a tabela padrão, calcula M_V, salva a figura e imprime o resultado."""
    df = carregar_estrelas()
    df["M_V"] = magnitude_absoluta(df["V"], df["paralaxe_mas"])
    fig, _ = plotar_hr(df, CAMINHO_FIGURA)
    plt.close(fig)
    print(
        df[["nome", "tipo_mk", "V", "B_V", "paralaxe_mas", "M_V"]].round(2).to_string(index=False)
    )
    print(f"\nFigura salva em: {CAMINHO_FIGURA}")


if __name__ == "__main__":
    main()
