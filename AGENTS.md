# AGENTS.md — CECILIA

Fonte autoritativa de regras: `CLAUDE.md`. Este arquivo é só o resumo operacional para agentes. Em caso de conflito, vale `CLAUDE.md`.

## Comandos (via `uv`, nunca `pip`/`python` direto)

```bash
uv sync                  # instala ambiente (Python 3.11, ver `.python-version`)
uv run pytest            # testes
uv run pytest tests/test_fumaca.py -q   # verificação rápida de ambiente
uv run ruff check .      # lint
uv run ruff format .     # formata (CI cobra `--check`)
```

Ordem de verificação local = ordem do CI (`.github/workflows/ci.yml`): `ruff check` → `ruff format --check` → `pytest`. CI usa `uv sync --locked`; se mexer em `pyproject.toml`, regenere o `uv.lock`.

Ruff: line-length 100, target py311, regras `E,F,I,UP,B`; `.claude/` e `.paul/` excluídos da formatação.

## Estrutura e fronteiras

- `src/cecilia/` — único código de produção (hoje só `__init__.py`; subpacotes como `data/` ainda não existem — crie conforme o roadmap).
- `tests/` — `pytest`, `testpaths = ["tests"]`. Só há `test_fumaca.py` (checa imports, sem rede).
- `notebooks/` — exploração; nada ali é fonte de verdade até migrar para `src/`.
- `data/{raw,interim,processed}/` — **nunca versionado** (ver `.gitignore`: `*.parquet, *.fits, *.csv.gz`). Manifesto versionado: `data/README.md`. `raw/` é cache exato e imutável.
- `.paul/`, `.claude/` — gerenciados pelo PAUL/framework; não edite `STATE.md`, `paul.toml`, `ledger.toml` à mão.
- `docs/` — `VOCABULARIO.md` (termos oficiais, uso exato), `ACCEPTANCE.md` (critérios Given/When/Then), `ROADMAP-PROPOSTO.md` (decisões abertas).

## Regras científicas (resumo — detalhe em `CLAUDE.md`)

1. **Sem vazamento de rótulo:** Trilho A — Teff, log g, [M/H] e qualquer tipo espectral (Gaia/LAMOST) nunca são features. Trilho B — massa via relações de escala reaprende a fórmula; documente.
2. **Baseline físico sempre** (tabela Teff / relações de escala) antes do ML.
3. **Split treino/val/teste fixo, com semente**, salvo em disco; teste intocado no dev.
4. Métricas: **macro-F1 + matriz de confusão + P/R por classe**; acurácia sozinha não vale.
5. Desconfie de features "importantes" sem física (paralaxe, mag. aparente = viés de seleção).
6. **Nada inventado:** nome de coluna/tabela de catálogo só após checar doc oficial ou consulta real; senão marque `# VERIFICAR` no código.

## Código e dados

- Python 3.11+, deps só via `pyproject.toml` (grupo `dev`: pytest, ruff, jupyterlab).
- Funções puras e testáveis para limpeza/features; figuras salvas por script, nunca à mão.
- Catalog queries (astroquery) em `src/cecilia/data/`, **sempre com cache em `data/raw/` (Parquet)**; nunca consulte o remoto 2× pelo mesmo dado.
- Comentários, docstrings e commits **em português** (imperativo: "Adiciona consulta ao gaia_source com cache").
- matplotlib em CI/sem display: `matplotlib.use("Agg")` (ver `test_fumaca.py`).

## Git / PR

- **Código** (`src/`, `tests/`, `notebooks/`, scripts, `pyproject.toml`, `uv.lock`, `.github/`): branch `fase-NN/plano-NN-descricao-curta` + PR após `/paul:unify`, com SUMMARY no PR.
- **Só docs/estado** (`docs/`, `README.md`, `CLAUDE.md`, `data/README.md`, `.paul/`): direto na `main` após `git pull`, sem PR. Commit misto segue regra do código.

## Fluxo PAUL

Todo trabalho: `/paul:plan` → `/paul:apply` → `/paul:unify`; plano referencia ACs de `docs/ACCEPTANCE.md`; nunca deixe PLAN sem SUMMARY. Escopo fora (exoplanetas, quasares/galáxias, multi-estelares, hidro 3D, N corpos) → pare e marque `NEEDS_CONTEXT`.
