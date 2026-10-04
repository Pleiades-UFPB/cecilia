"""Teste de fumaça: confirma que o ambiente instalado pelo `uv sync` está funcional.

Não testa lógica do projeto. Só garante que o pacote `cecilia` e as bibliotecas
científicas importam. Se algum teste aqui falhar, o problema é de ambiente
(dependência faltando ou quebrada), não de código.
"""

import importlib
import tomllib
from pathlib import Path

import pytest

import cecilia

RAIZ = Path(__file__).resolve().parents[1]

# Nome do módulo importável (nem sempre igual ao nome do pacote no PyPI:
# scikit-learn → sklearn, imbalanced-learn → imblearn).
MODULOS_CIENTIFICOS = [
    "numpy",
    "pandas",
    "pyarrow",
    "astropy",
    "astroquery",
    "sklearn",
    "xgboost",
    "imblearn",
    "shap",
    "matplotlib",
    "plotly",
]


def test_pacote_importa():
    """A versão declarada no pacote deve ser a mesma do pyproject.toml."""
    with open(RAIZ / "pyproject.toml", "rb") as f:
        versao_pyproject = tomllib.load(f)["project"]["version"]
    assert cecilia.__version__ == versao_pyproject


@pytest.mark.parametrize("nome", MODULOS_CIENTIFICOS, ids=MODULOS_CIENTIFICOS)
def test_dependencias_cientificas_importam(nome):
    """Cada biblioteca científica principal deve importar sem erro.

    Só importa — nenhuma consulta à rede é feita (astroquery inclusive).
    """
    if nome == "matplotlib":
        # Backend sem janela, para rodar no CI (sem display).
        importlib.import_module(nome).use("Agg")
    try:
        importlib.import_module(nome)
    except ImportError as erro:
        pytest.fail(f"Biblioteca '{nome}' não importou: {erro}")
