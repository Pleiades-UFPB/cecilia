---
description: "CECILIA — milestone and phase structure"
type: Roadmap
about: "CECILIA"
---

# Roadmap: CECILIA

## Overview

Do repositório vazio ao pipeline completo: fundação → aquisição de dados → limpeza e features → Trilho A (classe espectral) e Trilho B (asterossismologia) → análise → visualização de interior 1D. Proposta detalhada em `docs/ROADMAP-PROPOSTO.md`.

## Current Milestone
**v0.1 Pipeline completo** (v0.1.0)
Status: 🚧 In Progress
Phases: 0 of 7 complete

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with [INSERTED])

Os dois trilhos compartilham as fases 01, 03 e 06. Fases 04 e 05 podem correr em paralelo **apenas** com um loop por trilho e PRs integrados em sequência (ver `docs/EQUIPE-E-RODIZIO.md`).

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Fundação | 1/3 | Planning | - |
| 2 | Aquisição de dados | TBD | Not started | - |
| 3 | Limpeza e features | TBD | Not started | - |
| 4 | Classificação espectral (Trilho A) | TBD | Not started | - |
| 5 | Asterossismologia (Trilho B) | TBD | Not started | - |
| 6 | Análise | TBD | Not started | - |
| 7 | Visualização de interior 1D | TBD | Not started | - |

## Phase Details

### Phase 1: Fundação

**Goal:** Repositório pronto, ambiente reprodutível, convenções em vigor.
**Depends on:** Nothing (first phase)
**Research:** Unlikely (convenções internas)

**Scope:**
- Estrutura de pastas, `pyproject.toml`, `uv sync` funcionando
- `pytest` e `ruff` rodando; teste de fumaça
- Revisão coletiva do `docs/VOCABULARIO.md`
- Aquecimento: script que lê tabela de 10 estrelas famosas (digitadas à mão) e plota um HR

**Plans:**
- [x] 01-01: Ambiente reprodutível (uv.lock, pytest, ruff, teste de fumaça, CI)
- [ ] 01-02: Aquecimento — tabela de 10 estrelas e diagrama HR
- [ ] 01-03: Revisão coletiva do VOCABULARIO (checkpoint humano)

### Phase 2: Aquisição de dados

**Goal:** Consultas reprodutíveis com cache em `data/raw/`.
**Depends on:** Phase 1 (ambiente e convenções)
**Research:** Likely (catálogos externos, colunas a verificar)
**Research topics:** volume/região da amostra do Trilho A; cross-match LAMOST↔Gaia (ID publicado vs posição); tamanho máximo de amostra viável

**Scope:**
- Trilho A: `gaiadr3.gaia_source` + `gaiadr3.astrophysical_parameters` + vizinho 2MASS; LAMOST LRS com classes espectrais; cross-match
- Trilho B: catálogo APOKASC-3
- Manifesto em `data/README.md`; agradecimentos de cada fonte no README

**Plans:** TBD (defined during /paul:plan)

### Phase 3: Limpeza e features

**Goal:** Tabelas prontas para modelagem, com cortes documentados.
**Depends on:** Phase 2 (dados brutos em cache)
**Research:** Likely (tratamento de extinção; incluir ou não WISE)

**Scope:**
- Cortes de qualidade (candidatos: `parallax_over_error`, `ruwe`, qualidade 2MASS) justificados no plano
- Features: cores (BP−RP, G−RP, J−H, H−Ks, G−Ks), magnitude absoluta
- Tratamento de ausentes documentado, com contagem
- Partição treino/validação/teste com semente fixa, salva em disco
- Verificação automatizada anti-vazamento

**Plans:** TBD (defined during /paul:plan)

### Phase 4: Classificação espectral (Trilho A)

**Goal:** Classificador fotométrico avaliado contra baseline.
**Depends on:** Phase 3 (features e partição fixa)
**Research:** Unlikely

**Scope:**
- Baseline: classe por faixas de Teff (`teff_gspphot`) vs rótulo LAMOST
- Random Forest, XGBoost, Balanced Random Forest
- Macro-F1, matriz de confusão, PR por classe
- SHAP e investigação de confundidores
- Opcional: classe de luminosidade (anã vs gigante)

**Plans:** TBD (defined during /paul:plan)

### Phase 5: Asterossismologia (Trilho B)

**Goal:** Classificador RGB vs red clump com interpretação física.
**Depends on:** Phase 3 (dados APOKASC-3 limpos e partição fixa)
**Research:** Likely (verificar colunas do APOKASC-3)

**Scope:**
- Features candidatas: νmax, Δν, Teff, [M/H]
- Baseline: corte em νmax–Δν ou Teff–log g
- Modelos e métricas como na Fase 4
- Opcional didático: regressão de massa vs relação de escala (documentar que não é resultado novo)

**Plans:** TBD (defined during /paul:plan)

### Phase 6: Análise

**Goal:** Figuras e análises que contam a história dos dados e dos modelos.
**Depends on:** Phases 4 e 5 (predições dos dois trilhos)
**Research:** Unlikely

**Scope:**
- HR observacional colorido por classe (rótulo e predição)
- Kiel do Trilho B colorido por estágio evolutivo
- Onde o modelo erra no HR
- Relatório da fase em Markdown com figuras

**Plans:** TBD (defined during /paul:plan)

### Phase 7: Visualização de interior 1D

**Goal:** Visualizar estrutura interna de uma estrela e perfil de H/He.
**Depends on:** Phase 6 (propriedades inferidas/escolhidas)
**Research:** Likely (fonte dos perfis: Lane-Emden, modelo solar padrão tabelado, MESA)

**Scope:**
- Entrada: massa/Teff/estágio
- Perfis radiais (T, ρ, X, Y) e diagrama de camadas (núcleo, radiativa, convectiva)
- Visualização interativa em Plotly

**Plans:** TBD (defined during /paul:plan)

---

## 📋 Planned Milestone: v0.2 Comparador

**Goal:** Fase 8 — comparador de 2–4 estrelas lado a lado (tamanho, cor, HR, camadas). Estático, sem gravitação.
**Prerequisite:** v0.1 complete

---
*Roadmap created: 2026-10-04*
*Last updated: 2026-10-04*
