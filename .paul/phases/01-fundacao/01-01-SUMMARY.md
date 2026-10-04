---
phase: 01-fundacao
plan: 01
subsystem: infra
tags: [uv, pytest, ruff, github-actions, python-3.11]

requires: []
provides:
  - ambiente reprodutível travado em uv.lock (Python 3.11)
  - teste de fumaça do ambiente
  - CI no GitHub Actions (uv sync --locked, ruff, pytest)
affects: [01-fundacao, todas as fases seguintes]

tech-stack:
  added: [GitHub Actions (actions/checkout@v7, astral-sh/setup-uv@v10.2.0)]
  patterns: [uv sync --locked no CI, ruff check + ruff format --check obrigatórios]

key-files:
  created: [.python-version, uv.lock, tests/test_fumaca.py, .github/workflows/ci.yml]
  modified: [pyproject.toml, README.md]

key-decisions:
  - "Python 3.11 (mínimo suportado) em .python-version"
  - "Regras do ruff: E, F, I, UP, B (sem regras de docstring)"
  - ".claude e .paul excluídos do ruff (ruff 0.16 formata Markdown)"

patterns-established:
  - "Todo PR passa por CI: uv sync --locked, ruff check, ruff format --check, pytest"
  - "Testes não acessam rede"

duration: ~3min
started: 2026-10-04T11:07:00-03:00
completed: 2026-10-04T11:10:00-03:00
description: "Ambiente travado em uv.lock com Python 3.11, teste de fumaça de 12 casos e CI no GitHub Actions"
type: Summary
about: "CECILIA"
---

# Fase 01 Plano 01: Ambiente reprodutível — Summary

**Ambiente travado em `uv.lock` (152 pacotes, Python 3.11.15), teste de fumaça com 12 casos, ruff configurado e CI no GitHub Actions rodando os mesmos comandos em cada PR.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~3 min |
| Started | 2026-10-04T11:07-03:00 |
| Completed | 2026-10-04T11:10-03:00 |
| Tasks | 3 of 3 completed |
| Files modified | 6 (+ PLAN/SUMMARY) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Ambiente sobe do zero (AC-01.1) | Pass | Clone limpo da branch → `uv sync --locked` + `uv run pytest`: 12 passed, Python 3.11.15 |
| AC-2: Teste de fumaça detecta ambiente quebrado | Pass | 1 teste de versão + 11 parametrizados (id = nome do módulo); falha nomeia a biblioteca |
| AC-3: Lint e formatação padronizados | Pass | `ruff check .` → All checks passed; `ruff format --check .` → sem pendências |
| AC-4: CI verifica cada PR | Pass (local) — confirmar no PR | Workflow válido (YAML carregado, 6 passos). Só dispara em PR/push na main; check verde é confirmado no PR deste plano |
| AC-T.1: Reprodutibilidade | Pass | Mesmo resultado em clone limpo |

## Accomplishments

- Versões exatas de todas as dependências fixadas em `uv.lock`; CI usa `--locked` e quebra se o lock ficar desatualizado.
- Teste de fumaça separa "problema de ambiente" de "problema de código" logo no primeiro teste que alguém roda.
- Seção "Ambiente" do README com os comandos de lint/formatação.

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Tasks 1–3 | `8a81d88` | feat | uv.lock, pytest/ruff, teste de fumaça, CI, README |
| Auto-fix (ruff × Markdown) | `80f96f3` | fix | Exclui .claude e .paul do ruff |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `.python-version` | Created | Fixa Python 3.11 |
| `pyproject.toml` | Modified | pytest (`testpaths`, `-ra`), ruff (`py311`, regras E/F/I/UP/B, `extend-exclude`) |
| `uv.lock` | Created | Versões exatas (152 pacotes) |
| `tests/test_fumaca.py` | Created | 54 linhas; versão do pacote + import de 11 bibliotecas |
| `.github/workflows/ci.yml` | Created | 39 linhas; CI em PR/push para main |
| `README.md` | Modified | Comandos de ruff e menção ao CI |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Python 3.11 em `.python-version` | Desenvolver na versão mínima evita sintaxe que quebra em 3.11 | Todos usam 3.11 (uv baixa automaticamente) |
| Ruff sem regras de docstring (D) | Ruído excessivo para iniciantes; docstrings em PT são regra do CLAUDE.md | Revisão de docstrings fica humana |
| `.claude` e `.paul` fora do ruff | Ruff 0.16 formata blocos de código em Markdown; framework e estado PAUL não devem ser reescritos | `docs/*.md` e README continuam verificados |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Essencial — protege arquivos gerenciados pelo PAUL |
| Version updates | 1 | Nenhum — versões mais novas das actions |
| Deferred | 1 | Baixo |

**Total impact:** Correções essenciais, sem aumento de escopo.

### Auto-fixed Issues

**1. Tooling — ruff formatava Markdown de diretórios protegidos**
- **Found during:** Task 2 (verificação do `ruff format`)
- **Issue:** ruff 0.16.10 processava 111 arquivos `.md`, incluindo `.claude/` (framework) e `.paul/` (estado gerenciado). Nada foi alterado, mas um `ruff format .` futuro poderia reescrevê-los.
- **Fix:** `extend-exclude = [".claude", ".paul"]` em `[tool.ruff]`
- **Files:** `pyproject.toml`
- **Verification:** `ruff format --check .` passa a verificar 12 arquivos; testes e lint verdes
- **Commit:** `80f96f3`

**2. Versões das actions**
- Plano citava `actions/checkout@v4`; usado `@v7` (release estável atual).
- `astral-sh/setup-uv` não publica tag móvel `v10`; fixado `@v10.2.0` (verificado na API do GitHub).

### Deferred Items

- `PendingDeprecationWarning` do shap (`set_bad/set_over/set_under` do matplotlib) ao importar. Não falha testes; reavaliar ao atualizar shap/matplotlib.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| CI só dispara em PR/push na main; não dá para ver verde antes do PR | AC-4 confirmado no PR deste plano (aberto após o UNIFY, conforme CLAUDE.md) |

## Next Phase Readiness

**Ready:**
- Ambiente estável para o plano 01-02 (script de HR usa matplotlib/pandas já travados)
- CI pronto para validar todo PR seguinte

**Concerns:**
- Proteção da `main` não exige o check "CI" como obrigatório — pode ser adicionado em Settings → Branches depois do primeiro run

**Blockers:**
- None

---
*Built with PAUL Framework v1.4 · https://chrisai.cv/skool · https://youtube.com/@chris-ai-systems*
*Phase: 01-fundacao, Plan: 01*
*Completed: 2026-10-04*
