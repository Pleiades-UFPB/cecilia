---
phase: 03-limpeza-e-features
plan: 01
subsystem: limpeza
tags: [pandas, pyarrow, matplotlib, gaia-dr3, lamost, apokasc-3, 2mass]

requires:
  - phase: 02-aquisicao-de-dados (sem plano PAUL)
    provides: data/interim/trailA_lamost_gaia_2mass.parquet e trailB_apokasc_gaia_2mass.parquet (build_interim.py)
provides:
  - Perfil de valores por coluna dos Trilhos A e B (CSV/Markdown + 214 histogramas)
  - Catálogo de colunas com categoria e justificativa, aprovado pelo grupo
  - colunas_proibidas(trilho) para o teste anti-vazamento (AC-03.4)
affects: [03-02 Trilho A, 03-03 Trilho B, 04 classificação espectral, 05 asterossismologia, 02 aquisição (defeitos)]

tech-stack:
  added: []
  patterns:
    - "Leitura coluna a coluna (pd.read_parquet(columns=[c], dtype_backend='numpy_nullable')) para tabelas de GB"
    - "Catálogo de colunas como fonte única de verdade para categorias e lista de proibidas"

key-files:
  created:
    - src/cecilia/limpeza/perfil.py
    - src/cecilia/limpeza/catalogo_colunas.py
    - scripts/perfil_interim.py
    - docs/relatorios/fase-03-perfil-colunas.md
  modified: []

key-decisions:
  - "Triagem de colunas aprovada sem ajustes no checkpoint"
  - "GSP-Phot inteiro é so_baseline no Trilho A e irrelevante no Trilho B"
  - "classprob_dsc_combmod_star classificada como qualidade (não so_baseline)"

patterns-established:
  - "Coluna sem documentação conferida recebe verificar=True no catálogo"
  - "Teste de cobertura catálogo × esquema real, pulado no CI sem dados"

duration: ~1 sessão (APPLY com duas execuções completas do perfil, ~5 min cada)
started: 2026-11-05
completed: 2026-11-05
description: "Perfil de valores e triagem aprovada de todas as 124 (A) e 138 (B) colunas interim, com lista de colunas proibidas para o teste anti-vazamento"
type: Summary
about: "CECILIA"
---

# Fase 03 Plano 01: Perfil de valores e triagem de colunas — Summary

**Todas as colunas das tabelas interim foram perfiladas e classificadas: 124 no Trilho A (7.751.078 estrelas) e 138 no Trilho B (15.808 estrelas). A triagem foi aprovada pelo grupo, e `colunas_proibidas()` já está pronta para o teste anti-vazamento do 03-02 e do 03-03.**

**Status PAUL:** DONE_WITH_CONCERNS. Há colunas com `verificar=True`, e o perfil encontrou defeitos herdados da Fase 2.

## Performance

| Metric | Value |
|--------|-------|
| Duração | 1 sessão (2026-11-05) |
| Tarefas | 2 automáticas + 2 checkpoints, todos concluídos |
| Arquivos de código/doc criados | 7 (692 linhas) |
| Saídas geradas | 5 tabelas em `outputs/perfil/`, 214 PNG em `outputs/figures/perfil/` |

## Acceptance Criteria Results

| Critério | Status | Notas |
|-----------|--------|-------|
| AC-1: Pré-condição de dados | Pass | Os dois Parquet existem e o `data/interim/MANIFEST.jsonl` registra a origem (2026-10-27) |
| AC-2: Perfil por coluna | Pass | `perfil_serie`/`perfil_colunas` com todos os campos. Teste confirma que Int64 continua Int64 |
| AC-3: Toda coluna classificada, nenhuma inventada | Pass, com ressalva | O teste de cobertura rodou localmente contra o esquema real: 0 colunas sem categoria e 0 inventadas. Continuam com `verificar=True`: 7 colunas no A e 22 no B |
| AC-4: Colunas proibidas explícitas | Pass | A: as 30 `AP_COLS`, `lamost_z`/`lamost_e_z` e o rótulo (`lamost_Class`/`lamost_subClass`), 34 no total. B: `EvolSt`, relações de escala, idades e `AgeCat`, C/N e `InvRGaia`, 23 no total |
| AC-5: Figuras e tabelas reprodutíveis | Pass | Duas execuções do zero produziram 219 arquivos com md5 idêntico |
| AC-6: Triagem aprovada pelo grupo | Pass | Aprovada sem ajustes. Decisão registrada no relatório e no STATE |

## Accomplishments

- Primeira descrição quantitativa completa do dataset: faixa (p01–p99), ausentes e valores mais frequentes de cada coluna, com histogramas gerados por script.
- Catálogo de colunas com categoria e justificativa física, de onde sai a lista de colunas proibidas. Isso aplica as regras 1 (vazamento) e 5 (confundidores) do `CLAUDE.md` antes de qualquer modelagem.
- O perfil revelou problemas que mudam os próximos planos:
  - o rótulo do Trilho A tem 88 subclasses, incluindo WD, DoubleStar, Carbon e CV;
  - o rótulo do Trilho B tem 5 valores, e 4.241 rótulos vêm de espectroscopia (`EvolSrc=Spec`);
  - a fotometria Pan-STARRS tem 47–70% de ausentes e magnitudes negativas.

## Task Commits

Ainda sem commits. O código do plano vai num único commit na branch `fase-03/plano-01-perfil-colunas`, e o PR leva este SUMMARY (regra Git do `CLAUDE.md`).

## Files Created/Modified

| Arquivo | Mudança | Propósito |
|------|--------|---------|
| `src/cecilia/limpeza/__init__.py` | Criado | Pacote de limpeza |
| `src/cecilia/limpeza/perfil.py` | Criado | Funções puras de perfil por coluna |
| `src/cecilia/limpeza/catalogo_colunas.py` | Criado | Categoria, justificativa e `verificar` de cada coluna. Funções `colunas_proibidas` e `colunas_por_categoria` |
| `scripts/perfil_interim.py` | Criado | Gera CSV e Markdown de perfil, contagem de subclasses e histogramas |
| `tests/test_perfil.py` | Criado | 6 testes com dados sintéticos |
| `tests/test_catalogo_colunas.py` | Criado | 9 testes, incluindo a cobertura contra o esquema real (pulada sem dados) |
| `docs/relatorios/fase-03-perfil-colunas.md` | Criado | Relatório com achados e triagem aprovada |
| `outputs/perfil/*`, `outputs/figures/perfil/{A,B}/*.png` | Gerado | Saídas do script; não são editadas à mão |

## Decisions Made

| Decisão | Motivo | Impacto |
|----------|-----------|--------|
| Triagem aprovada sem ajustes | Checkpoint do grupo | O catálogo vale como está para o 03-02 e o 03-03 |
| GSP-Phot inteiro (`AP_COLS`) é `so_baseline` no A | Mesmo ajuste de Teff/log g/[M/H]; as colunas reconstroem Teff entre si | Só `teff_gspphot` alimenta o baseline. A M_G entra calculada a partir de G e da paralaxe, não por `mg_gspphot` |
| GSP-Phot é `irrelevante` no B | O APOKASC-3 já traz Teff e [Fe/H] do APOGEE; 51,7% ausente | 30 colunas descartadas |
| `fDNu`/`fNumax`, idades, `AgeCat`, [C/Fe] e [N/Fe] proibidos no B | Dependem do estágio evolutivo ou são usados para classificá-lo | Features do B ficam em νmax, Δν, Teff, log g espectroscópico, [Fe/H], [α/Fe], vsini e fotometria |
| Posições e movimento próprio são `confundidor_potencial` | Refletem a área observada pelo levantamento e a cinemática, não física | Ficam fora das features |

## Deviations from Plan

### Summary

| Tipo | Quantidade | Impacto |
|------|-------|--------|
| Desvios de classificação | 1 | Baixo |
| Correções durante a execução | 2 | Nenhum no resultado final |
| Pendências | 3 | Registradas no STATE |

**Impacto total:** o escopo foi o planejado, sem nada a mais. Os achados novos são diagnósticos e não alteram os dados.

### Desvios

**1. `classprob_dsc_combmod_star` virou `qualidade`, não `so_baseline`**
- **Encontrado em:** Task 1.
- **Motivo:** é a probabilidade do DSC de o objeto ser estrela, e não uma classe espectral. Serve para remover não-estrelas.
- **Proteção:** continua com `verificar=True`, e a justificativa pede investigar vazamento caso alguém queira usá-la como feature.

**2. As colunas do APOKASC-3 foram conferidas pelas descrições do VizieR, sem o ReadMe completo**
- **Motivo:** o ReadMe não estava disponível no espelho CfA (404), e o CDS estava inacessível (timeout).
- **Como foi feito:** as descrições de coluna vieram via astroquery (só metadados, consulta de 1 linha).
- **Pendência:** as notas numeradas (1)–(9) não foram lidas, por isso 22 colunas do B ficaram com `verificar=True`.

### Correções durante a execução

1. **Lint:** `Categoria` passou a usar `StrEnum`, e o alias `I` virou `ID` (regras UP042 e E741 do ruff).
2. **Script:** `tabela_markdown` quebrava com `top` nulo (NaN). Corrigido antes das execuções de verificação.

### Pendências

- **Defeito no `build_interim.py` (Fase 2).** O DuckDB não diferencia maiúsculas de minúsculas nos nomes de coluna. Por isso:
  - `lamost_Gmag_1` contém o g do Pan-STARRS, e não o G do Gaia;
  - `apokasc_e_AgeRGB_1` e `apokasc_e_AgeRC_1` repetem `E_Age*` em vez da incerteza inferior.
  - Confirmado comparando com `data/raw` (lá existem `Gmag` e `e_AgeRGB` distintos, com mínimo −43,9). Nenhuma das três colunas é usada como feature, mas o interim precisa ser regenerado num plano da Fase 2.
- **Notas (1)–(9) do ReadMe do APOKASC-3:** conferir e atualizar `verificar` no catálogo.
- **Fotometria Pan-STARRS:** decidir se entra como feature e, se entrar, limpar as magnitudes negativas.

## Issues Encountered

| Problema | Resolução |
|-------|------------|
| O branch `fase-03/plano-01-perfil-colunas` já existia (no mesmo commit 31c335e) | Usado como está; não havia commits próprios nele |
| Durante a 2ª execução o `.venv` foi removido e recriado por fora, provavelmente pela IDE, e o matplotlib falhou ao carregar fontes | Ambiente reinstalado com `uv`; as duas execuções de verificação foram refeitas do zero |
| `ruff check .` falha em `data_assembly/` e `visualization/` (código da Fase 2, fora do escopo) | Não corrigido (boundary). Os arquivos novos passam no ruff |
| `.idea/cecilia.iml` apareceu no índice do git sem ter sido adicionado nesta sessão | Fica fora do commit do plano |

## Next Phase Readiness

**Pronto:**
- `colunas_proibidas("A")` e `colunas_proibidas("B")` para o teste anti-vazamento.
- Lista de colunas de qualidade para os cortes do 03-02 e do 03-03: RUWE, `parallax_over_error`, `ph_qual`, S/N do LAMOST, `CatTab`, entre outras.
- Faixas e ausentes documentados para justificar cortes e tratamento de ausentes (AC-03.1, AC-03.2).

**Pendências que afetam os próximos planos:**
- O 03-02 precisa mapear as 88 subclasses do LAMOST para O–M e decidir o que fazer com WD, Carbon, DoubleStar, CV e EM.
- O 03-03 precisa decidir entre usar só os rótulos `EvolSrc=Seis` ou testar as duas versões.
- Decisões ainda abertas: extinção, WISE e Pan-STARRS. Recomenda-se `/paul:discover` antes do 03-02.
- Fase 2 sem plano PAUL e com defeitos conhecidos.

**Bloqueios:**
- Nenhum para planejar o 03-02.

---
*Built with PAUL Framework v1.4 · https://chrisai.cv/skool · https://youtube.com/@chris-ai-systems*
*Phase: 03-limpeza-e-features, Plan: 01*
*Completed: 2026-11-05*
