# PROJECT BRIEF — CECILIA

Respostas preparadas para o walkthrough do `/paul:init`. Tipo de projeto: **aplicação / software de pesquisa** (Python, dados + ML).

## Identidade

- **Nome:** CECILIA
- **Homenagem:** Cecilia Payne-Gaposchkin (1900–1979), que mostrou que a sequência espectral é uma sequência de temperatura e que as estrelas são feitas majoritariamente de H e He.
- **Contexto:** grupo de estudo Pleiades, LAViD/CI/UFPB. Proposta original de Luis Eduardo.
- **Equipe:** João Pedro, Luis Eduardo, Maria Vitória, Luan Motta, Arthur. Orientador: Prof. Carlos Eduardo Batista.

## Problema

Classificar estrelas e inferir suas propriedades a partir de grandes catálogos públicos é hoje um problema de dados: milhões de fontes, rótulos escassos e heterogêneos, classes desbalanceadas. O grupo quer aprender o pipeline completo — da consulta ao catálogo até a interpretação do modelo — de forma cientificamente correta.

## Objetivo

Construir um pipeline reprodutível em Python que:

1. Adquire dados estelares de Gaia DR3, 2MASS, LAMOST e APOKASC-3, com cache local.
2. Limpa e transforma os dados com critérios de qualidade documentados.
3. **Trilho A:** classifica estrelas por classe espectral (O-B-A-F-G-K-M) a partir de fotometria, com rótulos espectroscópicos independentes, comparando com um baseline por faixas de Teff.
4. **Trilho B:** classifica o estágio evolutivo de gigantes vermelhas (RGB vs red clump) a partir de parâmetros asterossísmicos e espectroscópicos do APOKASC-3.
5. Analisa e visualiza os resultados (diagramas HR e Kiel, SHAP).
6. Visualiza a estrutura interna 1D de uma estrela, incluindo o perfil de H/He.

Objetivo secundário: ferramenta de comparação lado a lado de estrelas (estáticas, sem interação gravitacional).

## Usuários

Os próprios alunos (aprendizado) e o orientador (acompanhamento). Saídas: código, figuras, relatório por fase.

## Restrições

- Python 3.11+, `uv`, bibliotecas listadas em `pyproject.toml`.
- Dados apenas de fontes públicas; nada versionado no git além de código e manifestos.
- Rodar em máquina pessoal dos alunos (sem HPC). Subamostragem é aceitável e deve ser documentada.
- Regra anti-vazamento de rótulo (ver `CLAUDE.md`).
- Rodízio de responsáveis entre fases (ver `docs/EQUIPE-E-RODIZIO.md`).

## Escopo

**Dentro:** dados estelares; limpeza e features; classificação multiclasse; asterossismologia via catálogo; análise e visualização; modelo 1D de interior.

**Fora:** exoplanetas (coberto pelo ExoHunter); quasares, galáxias; sistemas multi-estelares; hidrodinâmica 3D; dinâmica gravitacional.

## Critério de sucesso do projeto

- Pipeline reproduz do zero (dados → figuras) com um comando por fase.
- Trilho A: modelo fotométrico avaliado com macro-F1 e PR por classe em conjunto de teste fixo, comparado ao baseline.
- Trilho B: classificador RGB vs RC avaliado, com interpretação física das features dominantes.
- Visualização de interior funcional para pelo menos uma estrela tipo solar e uma gigante.
- Todo aluno foi responsável por pelo menos uma fase de dados, uma de modelo e uma de análise/visualização.
