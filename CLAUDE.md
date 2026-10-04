# CLAUDE.md — Regras do projeto CECILIA

Este arquivo é lido pelo Claude Code em toda sessão. Ele define como trabalhar neste repositório.

## Contexto

Projeto de grupo de estudo (5 alunos de graduação + orientador) em astronomia estelar com ML. Prioridade: **aprendizado correto e reprodutível**, não velocidade. Quando houver escolha entre uma solução mais simples que o aluno entenda e uma mais sofisticada que ele não entenda, escolha a primeira e explique.

Vocabulário oficial: `docs/VOCABULARIO.md`. Use os termos exatamente como definidos lá.

## Fluxo PAUL (obrigatório)

- Todo trabalho passa por `/paul:plan` → `/paul:apply` → `/paul:unify`. Sem exceção.
- **Nunca deixe um PLAN sem SUMMARY.** Antes de troca de responsável (rodízio), o loop corrente precisa estar fechado.
- Critérios de aceitação vêm de `docs/ACCEPTANCE.md`. Todo plano referencia ACs de lá ou cria novos no mesmo formato Given/When/Then.
- Use `/paul:discover` antes de planejar quando houver decisão técnica em aberto (ver "Decisões abertas" em `docs/ROADMAP-PROPOSTO.md`).
- `.paul/STATE.md`, `.paul/paul.toml` e `.paul/ledger.toml` são gerenciados pelo PAUL. Não edite à mão.

## Regras científicas (invioláveis)

1. **Sem vazamento de rótulo.** Nenhuma feature pode ser derivada da mesma fonte ou do mesmo cálculo que gera o rótulo. No Trilho A: Teff, log g, [M/H] e qualquer tipo espectral (Gaia ou LAMOST) **não** entram como features do modelo de ML. No Trilho B: se o alvo é massa e a massa do catálogo vem das relações de escala, o modelo só está reaprendendo a fórmula — documente isso explicitamente.
2. **Baseline sempre.** Todo modelo de ML é comparado com um baseline baseado em regra ou física (tabela de Teff, relações de escala). Se o ML não supera o baseline, isso é um resultado, não um fracasso — registre.
3. **Divisão treino/validação/teste fixa e com semente.** O conjunto de teste é separado uma vez, salvo em disco, e não é tocado durante o desenvolvimento.
4. **Classes desbalanceadas são o caso normal.** Reporte macro-F1, matriz de confusão e precisão-revocação por classe. Acurácia global sozinha não é métrica aceita.
5. **Confundidores.** Ao interpretar com SHAP, investigue features "importantes" sem justificativa física (ex.: paralaxe, magnitude aparente, que refletem viés de seleção). Ver Sahlmann & Gómez (2025) em `docs/REFERENCIAS.md`.
6. **Nada inventado.** Nomes de colunas, tabelas e campos de catálogos devem ser verificados na documentação oficial ou em consulta real antes de uso. Se não verificado, marque como `# VERIFICAR` no código e como DONE_WITH_CONCERNS no PAUL.

## Regras de código

- Python 3.11+, ambiente gerenciado com `uv`. Dependências só via `pyproject.toml`.
- Código de produção em `src/cecilia/`. Notebooks em `notebooks/` são exploração; nada que um notebook calcula é fonte de verdade até migrar para `src/`.
- Funções puras e testáveis para limpeza e features. Testes em `tests/` com `pytest`.
- Consultas a catálogos (astroquery) ficam em `src/cecilia/data/` e **sempre** gravam cache em `data/raw/` (Parquet). Nunca consultar o arquivo remoto duas vezes para o mesmo dado.
- Dados não são versionados no git. O que é versionado: o código que gera os dados e o manifesto em `data/README.md`.
- Toda figura gerada para análise é salva por script, não manualmente.
- Comentários e docstrings em português.

## Git

- Branch por plano: `fase-NN/plano-NN-descricao-curta`.
- PR só é aberto depois do `/paul:unify`; o `SUMMARY.md` do plano vai no PR.
- Commits em português, no imperativo: "Adiciona consulta ao gaia_source com cache".

## Escopo

Dentro: dados estelares, limpeza, features, classificação, asterossismologia (APOKASC-3), análise, visualização 1D de interior.
Fora: exoplanetas, quasares/galáxias, sistemas multi-estelares, hidrodinâmica 3D, simulação gravitacional de N corpos.
Se uma tarefa tocar o "fora", pare e marque como NEEDS_CONTEXT.
