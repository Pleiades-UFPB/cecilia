# CECILIA

Classificação estelar e asterossismologia com aprendizado de máquina sobre Gaia DR3, LAMOST e APOKASC-3.

Projeto do grupo **Pleiades** — LAViD / Centro de Informática / UFPB.

Repositório: <https://github.com/Pleiades-UFPB/cecilia>

## Por que "Cecilia"

Cecilia Payne-Gaposchkin (1900–1979) defendeu em 1925, em Radcliffe/Harvard, a tese *Stellar Atmospheres*. Aplicando a equação de ionização de Saha aos espectros estelares, ela mostrou duas coisas:

1. A sequência espectral O-B-A-F-G-K-M é, essencialmente, uma sequência de **temperatura** — não de composição química.
2. Uma vez corrigido o efeito da temperatura, as estrelas são compostas predominantemente por **hidrogênio e hélio**.

Henry Norris Russell desaconselhou a segunda conclusão na época; ele próprio a confirmou em 1929. Cecilia tornou-se depois a primeira mulher professora titular e chefe de departamento em Harvard.

O projeto carrega as duas ideias: o Trilho A trata da classificação espectral (a sequência de temperatura), e a visualização final (Fase 07) mostra o perfil interno de hidrogênio e hélio de uma estrela.

## O que o projeto faz

- **Trilho A — Classificação espectral.** Prever a classe espectral (e, como extensão, a classe de luminosidade) a partir de observáveis fotométricos do Gaia DR3 e 2MASS, usando rótulos de classificação espectroscópica independente (LAMOST). Um baseline baseado em regra (faixas de Teff) serve de referência.
- **Trilho B — Asterossismologia.** Classificar o estágio evolutivo de gigantes vermelhas (ramo das gigantes vs red clump) e explorar regressão de parâmetros a partir do catálogo APOKASC-3.
- **Análise.** Diagramas HR e Kiel, relações entre variáveis, interpretação dos modelos (SHAP).
- **Visualização de interior.** Modelo 1D da estrutura interna (núcleo, zona radiativa, zona convectiva) com perfil de H/He, parametrizado pelas propriedades inferidas.

Fora do escopo: detecção de exoplanetas (coberta pelo ExoHunter), objetos não estelares (quasares, galáxias), sistemas multi-estelares, simulação hidrodinâmica 3D.

## Equipe

Alunos: João Pedro, Luis Eduardo, Maria Vitória, Luan Motta e Arthur.
Orientação: Prof. Carlos Eduardo Batista (CI/UFPB, LAViD).

Proposta original: Luis Eduardo, a partir de reunião de alinhamento do grupo Pleiades.

## Como o projeto é desenvolvido

Desenvolvimento assistido por IA com **Claude Code** e o framework **PAUL** (Plan-Apply-Unify Loop). Todo trabalho segue o ciclo PLAN → APPLY → UNIFY, com critérios de aceitação definidos antes da execução. Detalhes em [`CLAUDE.md`](CLAUDE.md) e [`docs/EQUIPE-E-RODIZIO.md`](docs/EQUIPE-E-RODIZIO.md).

## Status

| Item | Valor |
|------|-------|
| Milestone | v0.1 — pipeline completo (em andamento, 0 de 7 fases) |
| Fase atual | Fase 01 — Fundação (pronta para planejar). Roadmap: [`.paul/ROADMAP.md`](.paul/ROADMAP.md) |
| Estado detalhado | [`.paul/STATE.md`](.paul/STATE.md) |

## Estrutura

```
cecilia/
├── CLAUDE.md              # regras do projeto para o Claude Code
├── .paul/                 # estado do PAUL (gerado por /paul:init — versionado)
├── docs/                  # brief, vocabulário, roadmap, aceitação, referências
├── data/                  # raw / interim / processed (dados NÃO versionados)
├── notebooks/             # exploração (nunca fonte de verdade)
├── src/cecilia/           # código do pacote
└── tests/
```

## Ambiente

```bash
git clone https://github.com/Pleiades-UFPB/cecilia.git
cd cecilia
uv sync
uv run pytest
uv run ruff check .    # lint
uv run ruff format .   # formata o código
```

O CI (GitHub Actions, `.github/workflows/ci.yml`) roda os mesmos comandos em cada PR para a `main`.

## Agradecimentos de dados

This work has made use of data from the European Space Agency (ESA) mission *Gaia* (https://www.cosmos.esa.int/gaia), processed by the *Gaia* Data Processing and Analysis Consortium (DPAC, https://www.cosmos.esa.int/web/gaia/dpac/consortium). Funding for the DPAC has been provided by national institutions, in particular the institutions participating in the *Gaia* Multilateral Agreement.

Os textos de agradecimento de LAMOST, 2MASS e APOKASC-3 serão adicionados na Fase 02, conforme as políticas de cada fonte (ver `data/README.md`).

## Licença

Código sob licença MIT (ver [`LICENSE`](LICENSE)). Dados seguem as licenças e políticas de citação de suas fontes.
