---
phase: 02-aquisicao-de-dados
plan: 01
subsystem: aquisicao
tags: [duckdb, pyarrow, gaia-dr3, lamost, apokasc-3, 2mass, ruff, uv]

requires:
  - phase: 03-limpeza-e-features (03-01)
    provides: diagnóstico dos defeitos do interim; catálogo de colunas e teste de cobertura
provides:
  - build_interim.py sem colisão de nomes (seleção por posição, renomeação explícita, checagem de unicidade)
  - data/interim/ regenerado do cache local (trailA, trailB, *_200pc, pleiades_region)
  - duckdb declarado no pyproject.toml/uv.lock
  - data_assembly/ e visualization/ importáveis pelo pacote, com ROOT na raiz do repositório
  - CI local verde (lint, formatação, testes)
  - manifesto de data/README.md preenchido
affects: [03-02 Trilho A, 03-03 Trilho B, 05 asterossismologia]

tech-stack:
  added: [duckdb 2.0.0]
  patterns:
    - "Colunas do Parquet selecionadas no DuckDB pelo nome que ele dá a cada posição (nomes_duckdb)"
    - "Pares que só diferem por maiúsculas recebem nome de saída explícito (RENOMEAR)"
    - "Módulos executáveis rodam com uv run python -m cecilia.<pacote>.<modulo>"

key-files:
  created:
    - tests/test_build_interim.py
  modified:
    - src/cecilia/data_assembly/build_interim.py
    - src/cecilia/limpeza/catalogo_colunas.py
    - data/README.md
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Nomes novos: lamost_Gmag_gaia, apokasc_e_AgeRGB_inf, apokasc_e_AgeRC_inf; lamost_gmag e apokasc_E_Age* mantêm o nome"
  - "Módulos ficam em src/cecilia/ (sem pasta scripts/); docstrings usam python -m"
  - "Branch empilhada sobre fase-03/plano-01-perfil-colunas (PR #5 ainda aberto)"

patterns-established:
  - "Todo SELECT montado a partir do esquema passa por checar_nomes_unicos"

duration: ~1 sessão (regeneração do interim ~6 min)
started: 2026-11-16T11:21:00-03:00
completed: 2026-11-16T11:45:00-03:00
description: "Colisão de nomes do DuckDB corrigida no build_interim, interim regenerado do cache local sem colunas *_1, duckdb declarado, CI local verde e manifesto preenchido"
type: Summary
about: "CECILIA"
---

# Fase 02 Plano 01: Regularizar a aquisição — Summary

**O `build_interim.py` agora seleciona as colunas pela posição no esquema e renomeia de forma explícita os pares que só diferem por maiúsculas. O interim foi regenerado a partir do cache local: `lamost_Gmag_gaia` contém o G do Gaia e `apokasc_e_Age*_inf` contém a incerteza inferior. O `duckdb` está declarado, o lint e a formatação passam e o manifesto de `data/README.md` está preenchido.**

**Status PAUL:** DONE. Todos os ACs passam. As pendências estão listadas abaixo.

## Performance

| Metric | Value |
|--------|-------|
| Duração | 1 sessão (2026-11-16) |
| Tarefas | 3 automáticas, todas concluídas |
| Arquivos alterados | 22 (1 criado) |
| Regeneração | build_interim 5 min 26 s; filter_200pc e pleiades_region < 30 s |

## Acceptance Criteria Results

| Critério | Status | Notas |
|-----------|--------|-------|
| AC-1: Colisão detectada e evitada | Pass | `tests/test_build_interim.py` (6 testes). Com a seleção antiga, por nome do Parquet, os testes dos Trilhos A e B falham exatamente como o defeito real: `Gmag` lê `gmag` e `e_AgeRGB` lê `E_AgeRGB` |
| AC-2: Interim regenerado, sem rede (AC-02.1) | Pass | Ver "Verificação". Nenhuma consulta remota: `fetch_raw` não rodou e `pleiades_region` usou o cache de gflux ("já existe, pulando consulta") |
| AC-3: CI verde localmente (AC-01.1) | Pass | `uv sync --locked`, `ruff check`, `ruff format --check` e `pytest` (33 passed) |
| AC-4: Manifesto preenchido (AC-02.2) | Pass | Partiu do texto não commitado do usuário no checkout principal. Ajustes: comandos `python -m`, datas das 5 tabelas regeneradas e nota sobre os nomes renomeados |
| AC-5: Catálogo coerente | Pass | `test_cobertura_contra_esquema_real` rodou contra os dados locais, sem skip, nos dois trilhos. As justificativas descrevem o conteúdo certo, e as categorias aprovadas no 03-01 não mudaram |

## Verificação (AC-2)

| Checagem | Resultado |
|---|---|
| Linhas trailA / trailB | 7.751.078 / 15.808 (iguais às de antes); com 2MASS 7.631.360 / 15.787 |
| 200 pc A / B; Plêiades | 207.030 / 45; 50.025 no cone, 717 candidatos (iguais às de antes) |
| Colunas terminadas em `_1` | nenhuma nas 5 tabelas; número de colunas igual (124, 138, 125, 139, 129) |
| `|lamost_Gmag_gaia − phot_g_mean_mag|` | mediana 2,6×10⁻⁷ mag, p99 8,1×10⁻⁷ mag (antes: era o g do PS1, mediana 0,84 mag de diferença do G) |
| `apokasc_e_AgeRGB_inf` | de −43,88 a −0,0098 (sempre negativa, como no raw) |
| `apokasc_e_AgeRC_inf` | de −43,88 a −0,001 |
| Trilho B, colunas comuns ao arquivo antigo | 0 linhas diferentes (`EXCEPT ALL`) |
| Trilho A, espectro escolhido e valores | hash de source_id, ObsID, gmag, snr_band, n_spectra, G, J e subClass idêntico ao do arquivo antigo |

## Files Created/Modified

| Arquivo | Mudança | Propósito |
|------|--------|---------|
| `src/cecilia/data_assembly/build_interim.py` | Modificado | `nomes_duckdb`, `RENOMEAR`, `checar_nomes_unicos`; SQL separado em `sql_trilho_a`/`sql_trilho_b` para teste; `ROOT` corrigido |
| `tests/test_build_interim.py` | Criado | Parquet sintéticos com gmag/Gmag e E_/e_ |
| `src/cecilia/data_assembly/{fetch_raw,clean_sentinels}.py` | Modificado | `ROOT`, docstrings `python -m`, lint e formatação |
| `src/cecilia/visualization/*.py` (10) | Modificado | `ROOT`, imports pelo pacote (`cecilia.data_assembly...`), docstrings, lint e formatação |
| `src/cecilia/limpeza/catalogo_colunas.py` | Modificado | Chaves e justificativas de `lamost_Gmag_gaia` e `apokasc_e_Age*_inf` |
| `docs/relatorios/fase-03-perfil-colunas.md` | Modificado | Nota de que o defeito foi corrigido; o histórico foi mantido |
| `data/README.md` | Modificado | Manifesto, fontes e agradecimentos (texto do usuário), comandos e datas atualizados |
| `pyproject.toml`, `uv.lock` | Modificado | `duckdb>=2.0.0` |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Renomear só a coluna “de baixo” de cada par: `Gmag` → `Gmag_gaia`, `e_Age*` → `e_Age*_inf` | Mudança mínima. `lamost_gmag` fica junto das outras magnitudes PS1, e `E_Age*` mantém o nome do VizieR | Código que use os nomes antigos (`*_1`) precisa trocar |
| Corrigir `ROOT` e imports em vez de mover arquivos para `scripts/` | O `CLAUDE.md` põe código de produção em `src/cecilia/`. Mover arquivos ficou fora do escopo do plano | Os comandos documentados passam a ser `uv run python -m cecilia.<pacote>.<modulo>` |
| Empilhar a branch sobre `fase-03/plano-01-perfil-colunas` | O PR #5 ainda não entrou em `feat/dataset_cleanup`, e o catálogo (passo 6) só existe lá | O PR mostra os commits do #5 até o #5 ser integrado |

## Deviations from Plan

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Imports dos módulos de `visualization/` quebrados fora de `scripts/` (`from build_interim import`), corrigidos para imports pelo pacote. Sem isso, `filter_200pc` e `pleiades_region` não rodavam |
| Scope additions | 1 | `filter_200pc` e `pleiades_region` também foram regenerados. Eles derivam do trailA e carregavam `lamost_Gmag_1` |
| Not done | 1 | `__init__.py` em `data_assembly/`/`visualization/` listados em `files_modified` não foram criados: os pacotes de namespace já funcionam (testes e `python -m`) |

**Lock do uv:** o `uv add` com uv 0.13.7 reescreveu o `uv.lock` na revisão 5 e simplificou marcadores. O CI instala o uv mais recente (`setup-uv` sem versão fixa), então lê o arquivo.

### Deferred Items
- `outputs/perfil/*` e `outputs/figures/perfil/` (gerados pelo 03-01) ainda usam os nomes antigos (`lamost_Gmag_1`, `apokasc_e_Age*_1`) e os valores errados. Basta rodar de novo `uv run python scripts/perfil_interim.py`, o que pertence à linha da Fase 3.
- AC-02.3 (taxa de associação do cross-match e fontes por classe espectral): plano 02-02.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Os dados existem só no checkout principal, não no worktree | Symlinks por arquivo em `data/raw/` e `data/interim/` do worktree (ignorados pelo git). Saídas geradas no worktree, conferidas e então movidas para `data/interim/` do checkout principal. O `MANIFEST.jsonl` recebeu as 5 entradas novas |

## Next Phase Readiness

**Ready:**
- Interim correto para o 03-02 e o 03-03; o catálogo bate com o esquema.
- O CI pode rodar em qualquer PR da linha `feat/dataset_cleanup`, desde que o workflow seja disparado para essa base (hoje só roda para PRs contra a `main`).

**Concerns:**
- O workflow de CI não roda para PRs contra `feat/dataset_cleanup`; a verificação foi local.
- O perfil do 03-01 em `outputs/` está desatualizado (ver Deferred).

**Blockers:** nenhum.

---
*Built with PAUL Framework v1.4 · https://chrisai.cv/skool · https://youtube.com/@chris-ai-systems*
*Phase: 02-aquisicao-de-dados, Plan: 01*
*Completed: 2026-11-16*
