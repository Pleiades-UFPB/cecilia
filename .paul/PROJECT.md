---
description: "Pipeline reprodutível que leva o grupo da consulta a catálogos estelares públicos até a interpretação correta de modelos de ML"
type: Project
about: "CECILIA"
---

# CECILIA

## What This Is

Pipeline reprodutível em Python para classificação estelar e asterossismologia com aprendizado de máquina sobre Gaia DR3, 2MASS, LAMOST e APOKASC-3. Dois trilhos: (A) classe espectral O-B-A-F-G-K-M a partir de fotometria, com rótulos espectroscópicos independentes do LAMOST; (B) estágio evolutivo de gigantes vermelhas (RGB vs red clump) a partir do APOKASC-3. Fecha com análise (HR, Kiel, SHAP) e visualização 1D do interior estelar com perfil de H/He. Projeto do grupo de estudo Pleiades (LAViD/CI/UFPB), em homenagem a Cecilia Payne-Gaposchkin.

## Core Value

O grupo aprende o pipeline completo — da consulta ao catálogo até a interpretação do modelo — de forma cientificamente correta e reprodutível (sem vazamento de rótulo, com baseline e teste fixo).

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Application (software de pesquisa — Python, dados + ML) |
| Version | 0.0.0 |
| Status | Initializing |
| Last Updated | 2026-10-04 |

## Requirements

### Core Features

- Aquisição de dados de Gaia DR3, 2MASS, LAMOST e APOKASC-3 com cache local em Parquet (`data/raw/`)
- Limpeza e features com cortes de qualidade documentados e partição treino/validação/teste fixa com semente
- Trilho A: classificador fotométrico de classe espectral vs baseline por faixas de Teff
- Trilho B: classificador RGB vs red clump com interpretação física das features
- Análise e visualização: diagramas HR e Kiel, SHAP, modelo 1D de interior com perfil de H/He

### Validated (Shipped)
None yet.

### Active (In Progress)
None yet.

### Planned (Next)
Fases propostas em `docs/ROADMAP-PROPOSTO.md` (milestone v0.1 — pipeline completo):
- [ ] Fase 01 — Fundação
- [ ] Fase 02 — Aquisição de dados
- [ ] Fase 03 — Limpeza e features
- [ ] Fase 04 — Classificação espectral (Trilho A)
- [ ] Fase 05 — Asterossismologia (Trilho B)
- [ ] Fase 06 — Análise
- [ ] Fase 07 — Visualização de interior 1D
- [ ] (v0.2) Fase 08 — Comparador de estrelas (estático)

### Out of Scope

- Exoplanetas — coberto pelo ExoHunter
- Quasares, galáxias e demais objetos não estelares
- Sistemas multi-estelares
- Hidrodinâmica 3D e simulação gravitacional de N corpos

## Target Users

**Primary:** os 5 alunos de graduação (João Pedro, Luis Eduardo, Maria Vitória, Luan Motta, Arthur)
- Aprendizado correto > velocidade
- Rodízio de responsáveis entre fases (`docs/EQUIPE-E-RODIZIO.md`)

**Secondary:** orientador (Prof. Carlos Eduardo Batista) — acompanhamento via código, figuras e relatório por fase

## Constraints

### Technical Constraints
- Python 3.11+, ambiente `uv`, dependências só via `pyproject.toml`
- Roda em máquinas pessoais (sem HPC); subamostragem aceitável se documentada
- Dados só de fontes públicas; dados não versionados (só código + manifesto `data/README.md`)
- Consultas a catálogos sempre com cache; nunca consultar o arquivo remoto duas vezes para o mesmo dado
- Nomes de colunas/tabelas verificados na documentação oficial; senão `# VERIFICAR`

### Business Constraints
- Regras científicas invioláveis de `CLAUDE.md` (anti-vazamento, baseline, teste fixo, macro-F1, confundidores)
- Fluxo PAUL obrigatório; loop fechado antes de troca de responsável
- Critérios de aceitação em `docs/ACCEPTANCE.md`; vocabulário em `docs/VOCABULARIO.md`

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| Rótulos do Trilho A vêm do LAMOST; Teff/log g/[M/H]/tipo espectral não entram como features | Evitar vazamento de rótulo | 2026-10-04 | Active |
| Stack Python + uv + scikit-learn/XGBoost/imbalanced-learn/SHAP | Bibliotecas padrão, fáceis de aprender | 2026-10-04 | Active |
| Repositório público em github.com/Pleiades-UFPB/cecilia, licença MIT | Reprodutibilidade e abertura | 2026-10-04 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Reprodutibilidade | Dados → figuras do zero com um comando por fase | - | Not started |
| Trilho A | Macro-F1 e PR por classe em teste fixo, comparado ao baseline | - | Not started |
| Trilho B | Classificador RGB vs RC avaliado, features dominantes interpretadas fisicamente | - | Not started |
| Interior 1D | Visualização funcional para ≥1 estrela tipo solar e ≥1 gigante | - | Not started |
| Rodízio | Todo aluno responsável por ≥1 fase de dados, 1 de modelo, 1 de análise/visualização | - | Not started |

## Tech Stack / Tools

| Layer | Technology | Notes |
|-------|------------|-------|
| Linguagem/ambiente | Python 3.11+, uv | Reprodutível |
| Dados | astroquery, astropy, pandas, pyarrow | Cache Parquet em `data/raw/` |
| ML | scikit-learn, XGBoost, imbalanced-learn | Classes desbalanceadas |
| Interpretação | SHAP | Investigar confundidores |
| Visualização | matplotlib, plotly | Figuras sempre por script |
| Qualidade | pytest, ruff | Funções puras testáveis |
| Processo | Claude Code + PAUL | PLAN → APPLY → UNIFY |

## Links

| Resource | URL |
|----------|-----|
| Repository | https://github.com/Pleiades-UFPB/cecilia |
| Documentation | `docs/` |

---
*Created: 2026-10-04*
*Last updated: 2026-10-04*
