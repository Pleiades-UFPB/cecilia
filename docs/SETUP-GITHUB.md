# Setup do repositório no GitHub

## Dados do repositório

- **Nome:** `cecilia`
- **Descrição:** CECILIA — Classificação estelar e asterossismologia com ML sobre Gaia DR3, LAMOST e APOKASC-3. Projeto Pleiades / LAViD-UFPB.
- **Visibilidade:** pública
- **Licença:** MIT
- **Topics:** astronomy, astrophysics, stellar-classification, asteroseismology, gaia, machine-learning, xgboost, python, paul-framework, claude-code

## Criação (GitHub CLI)

Substitua `<OWNER>` pela org do LAViD ou sua conta.

```bash
cd cecilia
git init -b main
git add .
git commit -m "Inicializa repositório CECILIA"

gh repo create <OWNER>/cecilia --public --source=. --push \
  --description "CECILIA — Classificação estelar e asterossismologia com ML sobre Gaia DR3, LAMOST e APOKASC-3. Projeto Pleiades / LAViD-UFPB."

gh repo edit <OWNER>/cecilia \
  --add-topic astronomy --add-topic astrophysics --add-topic stellar-classification \
  --add-topic asteroseismology --add-topic gaia --add-topic machine-learning \
  --add-topic xgboost --add-topic python --add-topic paul-framework --add-topic claude-code
```

Adicione o arquivo `LICENSE` (MIT) pela interface do GitHub ou com o texto padrão, com o titular que você definir.

## Colaboradores

```bash
for u in <user-joao> <user-luis> <user-maria> <user-luan> <user-arthur>; do
  gh api -X PUT repos/<OWNER>/cecilia/collaborators/$u -f permission=push
done
```

## Proteção da main

Settings → Branches → regra para `main`: exigir PR e 1 aprovação. Combina com a regra "revisor da fase aprova o PR".

## Inicializando o PAUL

```bash
npx paul-framework --local   # instala em ./.claude/
```

No Claude Code, dentro do repositório:

1. `/paul:init` — use as respostas de `docs/PROJECT-BRIEF.md`.
2. `/paul:milestone v0.1-pipeline-completo`
3. `/paul:add-phase` para cada fase de `docs/ROADMAP-PROPOSTO.md`.
4. `/paul:discuss-milestone` com o grupo.
5. `/paul:plan` da Fase 01.

Commite `.claude/` (comandos locais do PAUL) e `.paul/` para que todos usem a mesma versão.
