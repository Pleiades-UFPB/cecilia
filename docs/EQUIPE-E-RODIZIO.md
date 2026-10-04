# Equipe e rodízio — CECILIA

## Equipe

- João Pedro
- Luis Eduardo (proponente)
- Maria Vitória
- Luan Motta
- Arthur

Orientador: Prof. Carlos Eduardo Batista. Cronograma e prazos: definidos pelo orientador.

## Papéis por fase

- **Responsável:** conduz os loops PAUL da fase (`/paul:plan`, `/paul:apply`, `/paul:unify`) e abre os PRs de código (documentação e estado do PAUL vão direto para a `main`, ver `CLAUDE.md`).
- **Revisor:** revisa cada PR da fase contra os ACs antes do merge.
- **Demais:** acompanham, testam, discutem no `/paul:discuss`.

## Regras do rodízio

1. Ninguém é responsável por duas fases consecutivas.
2. Ao fim do v0.1, cada aluno foi responsável por pelo menos uma fase de **dados** (02/03), uma de **modelo** (04/05) e uma de **análise/visualização** (06/07). Como são 7 fases e 5 alunos, isso se completa com co-responsáveis nas fases mais pesadas.
3. O revisor de uma fase é o responsável da fase seguinte — assim quem pega o bastão já conhece o que recebe.
4. **Passagem de bastão:** loop fechado (SUMMARY.md), `STATE.md` atualizado, `/paul:handoff` gerado e commitado.

## Tabela de rodízio (proposta — orientador confirma)

| Fase | Responsável | Co-responsável | Revisor |
|---|---|---|---|
| 01 Fundação | | | |
| 02 Aquisição | | | |
| 03 Limpeza e features | | | |
| 04 Classificação espectral | | | |
| 05 Asterossismologia | | | |
| 06 Análise | | | |
| 07 Interior 1D | | | |

## PAUL com várias pessoas

O PAUL foi desenhado para uma sessão por vez. Com cinco pessoas:

- `.paul/` é versionado no git. Ninguém edita `STATE.md` à mão.
- **Um loop ativo por trilho.** Fases 04 e 05 podem correr em paralelo, mas cada uma em sua branch, e os PRs entram em `main` em sequência; quem integra o segundo faz `/paul:resume` após o merge para reconciliar o estado.
- Antes de começar qualquer sessão: `git pull` e `/paul:progress`.
- Conflito em `.paul/`: não resolver manualmente; chamar o orientador.
