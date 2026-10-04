# Roadmap proposto — CECILIA

Fases para criar com `/paul:add-phase` após o `/paul:init`. Milestone inicial: **v0.1 — pipeline completo**.

Os dois trilhos compartilham as fases 01, 03 e 06. Fases 04 e 05 podem correr em paralelo **apenas** se cada trilho tiver um loop por vez e os PRs forem integrados em sequência (ver `docs/EQUIPE-E-RODIZIO.md`).

---

## Fase 01 — Fundação

**Objetivo:** repositório pronto, ambiente reprodutível, convenções em vigor.

- Estrutura de pastas, `pyproject.toml`, `uv sync` funcionando.
- `pytest` e `ruff` rodando; teste de fumaça.
- Revisão coletiva do `VOCABULARIO.md` (é o primeiro ato do projeto).
- Exercício de aquecimento: script que lê uma tabela pequena (10 estrelas famosas digitadas à mão) e plota um HR.

## Fase 02 — Aquisição de dados

**Objetivo:** consultas reprodutíveis com cache.

- Trilho A: `gaiadr3.gaia_source` + `gaiadr3.astrophysical_parameters` + vizinho 2MASS; catálogo LAMOST LRS com classes espectrais; cross-match.
- Trilho B: download do catálogo APOKASC-3.
- Manifesto de dados em `data/README.md`.
- Textos de agradecimento de cada fonte no README.

**Decisões abertas (usar `/paul:discover`):**
- Região do céu/volume da amostra do Trilho A (ex.: até 200 pc para minimizar extinção, ou amostra maior com correção).
- Forma de cross-match LAMOST↔Gaia (ID publicado pelo LAMOST vs posição).
- Tamanho máximo de amostra viável nas máquinas dos alunos.

## Fase 03 — Limpeza e features

**Objetivo:** tabelas prontas para modelagem, com cortes documentados.

- Cortes de qualidade (candidatos: `parallax_over_error`, `ruwe`, qualidade fotométrica 2MASS) — valores finais decididos e justificados no plano.
- Features derivadas: cores (BP−RP, G−RP, J−H, H−Ks, G−Ks), magnitude absoluta.
- Tratamento de valores ausentes documentado (imputação ou remoção, com contagem).
- Partição treino/validação/teste com semente fixa, salva em disco.
- Verificação automatizada anti-vazamento.

**Decisões abertas:** tratamento de extinção; incluir ou não WISE.

## Fase 04 — Classificação espectral (Trilho A)

**Objetivo:** classificador fotométrico avaliado contra baseline.

- Baseline: classe prevista pelas faixas de Teff (usando `teff_gspphot`) vs rótulo LAMOST.
- Modelos: Random Forest, XGBoost; Balanced Random Forest para desbalanceamento.
- Métricas: macro-F1, matriz de confusão, curva PR por classe.
- Interpretação com SHAP; investigação de confundidores.
- Extensão opcional: classe de luminosidade (anã vs gigante).

## Fase 05 — Asterossismologia (Trilho B)

**Objetivo:** classificador RGB vs RC com interpretação física.

- Features candidatas: νmax, Δν, Teff, [M/H] (verificar colunas no catálogo).
- Baseline: corte simples em espaço νmax–Δν ou Teff–log g.
- Modelos e métricas como na Fase 04.
- Exercício didático opcional: regressão de massa e comparação com a relação de escala — o modelo deve "redescobrir" a fórmula. Documentar que isso não é resultado novo.

## Fase 06 — Análise

**Objetivo:** figuras e análises que contam a história dos dados e dos modelos.

- Diagrama HR observacional colorido por classe (rótulo e predição).
- Diagrama Kiel do Trilho B colorido por estágio evolutivo.
- Onde o modelo erra no HR (erros concentrados nas fronteiras de classe?).
- Relatório da fase em Markdown com as figuras.

## Fase 07 — Visualização de interior 1D

**Objetivo:** visualizar a estrutura interna de uma estrela e o perfil de H/He.

- Entrada: massa/Teff/estágio inferidos ou escolhidos.
- Saída: perfis radiais (T, ρ, X, Y) e diagrama de camadas (núcleo, zona radiativa, zona convectiva).
- Visualização interativa em Plotly.

**Decisão aberta (`/paul:discover`):** fonte dos perfis —
(a) politropo de Lane-Emden (didático, só ρ e T, sem composição);
(b) modelo solar padrão tabelado publicamente (tem X e Y por raio, mas só para o Sol);
(c) perfis gerados com MESA (mais completo, exige instalação pesada).
Uma combinação (a)+(b) cobre o objetivo sem HPC.

---

## Objetivo secundário (milestone v0.2)

**Fase 08 — Comparador de estrelas:** visualização lado a lado de 2–4 estrelas (tamanho relativo, cor, posição no HR, camadas). Estático, sem gravitação.

## Fora do roadmap

Exoplanetas, objetos extragalácticos, sistemas múltiplos, hidrodinâmica 3D.
