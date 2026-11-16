# Fase 03 — Perfil de valores e triagem de colunas (plano 03-01)

**Status:** triagem **aprovada** no checkpoint do 03-01 (2026-11-05), sem ajustes. As categorias abaixo valem como estão em `catalogo_colunas.py`.

Gerado a partir de `data/interim/` com:

```bash
uv run python scripts/perfil_interim.py
```

Tabelas completas (uma linha por coluna, com faixa, ausentes, valores mais frequentes e justificativa):

- Trilho A: [`outputs/perfil/trailA_perfil.md`](../../outputs/perfil/trailA_perfil.md) / `.csv` — 124 colunas, 7.751.078 estrelas
- Trilho B: [`outputs/perfil/trailB_perfil.md`](../../outputs/perfil/trailB_perfil.md) / `.csv` — 138 colunas, 15.808 estrelas
- Histogramas: `outputs/figures/perfil/{A,B}/{coluna}.png`, mostrando a faixa entre os percentis 1 e 99 com contagem em escala log
- Contagem por subclasse LAMOST: [`outputs/perfil/trailA_subclasse.csv`](../../outputs/perfil/trailA_subclasse.csv)

A categoria de cada coluna está em `src/cecilia/limpeza/catalogo_colunas.py`, que é a fonte de verdade. Este relatório só resume.

## Categorias

| Categoria | Significado | Trilho A | Trilho B |
|---|---|---:|---:|
| `feature_candidata` | Pode entrar como feature ou servir de base para uma feature derivada (cor, M_G) | 13 | 15 |
| `rotulo` | Fonte do rótulo | 2 | 1 |
| `so_baseline` | **Proibida como feature.** Vem do mesmo cálculo ou da mesma fonte do rótulo. Uso só em baseline ou análise | 32 | 22 |
| `qualidade` | Usada em corte de qualidade, não como feature | 40 | 44 |
| `identificador` | Id ou chave de junção | 12 | 7 |
| `confundidor_potencial` | Sem justificativa física para o rótulo. Pode refletir viés de seleção | 6 | 6 |
| `irrelevante` | Descartada | 19 | 43 |

`colunas_proibidas(trilho)` junta `rotulo` e `so_baseline`. É essa lista que o teste anti-vazamento do 03-02 e do 03-03 vai usar (AC-03.4).

## Achados que afetam as próximas etapas

### 1. Defeitos de dados herdados da Fase 2 (`build_interim.py`)

O DuckDB não diferencia maiúsculas de minúsculas em nomes de coluna. Quando dois nomes só diferem na caixa, o segundo é lido no lugar do primeiro:

| Coluna interim | Deveria conter | Contém de fato |
|---|---|---|
| `lamost_Gmag_1` | G do Gaia, copiado pelo LAMOST (`Gmag`) | g do Pan-STARRS (`gmag`), valor por valor |
| `apokasc_e_AgeRGB_1`, `apokasc_e_AgeRC_1` | Incerteza inferior da idade (negativa, mínimo −43,9 no raw) | Repete `E_AgeRGB` / `E_AgeRC` (positiva) |

**Impacto neste projeto:** nenhum direto. As três colunas já estavam fora: `phot_g_mean_mag` substitui a primeira, e as idades são proibidas no Trilho B. Mesmo assim, o arquivo interim está errado e precisa ser corrigido num plano da Fase 2. Fica registrado como concern no SUMMARY.

### 2. O rótulo do Trilho A precisa de mapeamento (03-02)

`lamost_subClass` tem 88 valores distintos. A grande maioria é do tipo MK (G5, K5, dM0, gM3…), mas há valores sem classe espectral:

- Fora da sequência O–M: `WD` (11.151), `DoubleStar` (3.761), `Carbon` (3.718), `EM` (423), `WDMagnetic` (367), `CV` (346), `CarbonWD` (123). Sistemas multi-estelares (`DoubleStar`, `CV`) estão fora do escopo.
- Sem subclasse: `O`, `B`, `OB`, `A`, `F`, `G`.
- Com classe de luminosidade: `A6IV`, `A5V`… (poucas dezenas).
- Desbalanceamento forte: G e K dominam (G5 sozinha tem 757 mil). O tem ~200 estrelas no total, e B, ~9,4 mil.

### 3. O rótulo do Trilho B tem mais que duas classes

`apokasc_EvolSt` tem RGB (9.632), RC (5.736), Dwarf (241), Unknown (170) e RC/RGB (29). Para o problema binário, só RGB e RC servem.

`apokasc_EvolSrc` diz de onde veio o rótulo: `Seis` (11.397) ou `Spec` (4.241). Quando o rótulo é `Spec`, ele foi derivado de dados espectroscópicos. Nesse caso, Teff, log g e [C/N] espectroscópicos podem vazar o rótulo. Proposta: o 03-03 usa só os rótulos `Seis`, ou testa as duas versões.

### 4. Ausentes relevantes

| Coluna | Trilho | % ausentes | Observação |
|---|---|---:|---|
| GSP-Phot (todas) | A | 14,0 | Não afeta features (são proibidas). Afeta o baseline, que fica sem Teff em 14% das estrelas |
| GSP-Phot (todas) | B | 51,7 | Irrelevante no B |
| `radial_velocity` | A | 57,7 | Irrelevante |
| Pan-STARRS `lamost_{g,r,i,z,y}mag` | A | 47–70 | Problema se viraram features. Têm valores negativos (mínimo −7,1) que parecem sentinelas não documentados |
| 2MASS J/H/Ks | A | 1,5 | Sem contrapartida 2MASS |
| `ext_key` | A, B | 99,9 / 100 | Nulo significa "não associado a fonte estendida". Não é dado faltante |
| `apokasc_Numax` / `DNu` | B | 8,1 / 14,2 | Sem detecção sísmica (`CatTab` = NoDet*) |

### 5. Faixas fisicamente estranhas

- **`parallax`:** valores negativos (p01 = −0,004 mas, mínimo −17). No Trilho A, `parallax_over_error` tem mediana 23 e p01 negativo. Isso pede um corte antes de calcular M_G.
- **`ruwe`:** p99 = 10 e máximo 95. O corte usual é RUWE < 1,4.
- **`phot_bp_rp_excess_factor`:** máximo 651, indicando contaminação de BP/RP.
- **`lamost_e_z`:** máximo 1×10⁷.
- **`lamost_FiberMask`:** valores negativos (mínimo −5002), embora seja uma máscara de bits.
- **`apokasc_vsini`:** 18 estrelas com valor negativo (mínimo −5), possivelmente uma flag.
- **`apokasc_e_[Fe/H]`:** constante (0,058).
- **`ph_qual`:** no Trilho A, 84% é `AAA`. No Trilho B há 24 `EEE`.

## Triagem aprovada

### Colunas irrelevantes (descartar)

**Trilho A**
- Metadados de data e arquivo: `lamost_ObsDate`, `lamost_LMJD`, `lamost_MJD`, `j_date`, `lamost_fNFlux`, `lamost_n_spectra`.
- Posições duplicadas: `tmass_ra`, `tmass_dec`, `lamost_RAdeg`, `lamost_DEdeg`, `lamost_RAOdeg`, `lamost_DEOdeg`.
- Constante: `lamost_FiberType`.
- Coluna com defeito: `lamost_Gmag_1`.
- Velocidade radial: `radial_velocity`, `radial_velocity_error`.
- Flags de disponibilidade: `has_xp_continuous`, `has_xp_sampled`, `has_rvs`.

**Trilho B**
- Todas as colunas GSP-Phot (o APOKASC-3 traz Teff e [Fe/H] do APOGEE).
- `radial_velocity` e `radial_velocity_error`.
- As mesmas flags `has_*`.
- Posições duplicadas: `tmass_ra`, `tmass_dec`, `apokasc__RA`, `apokasc__DE`.
- `j_date`, `apokasc_Simbad`, `apokasc_KCat`.
- `apokasc_alphaCat` (redundante com `[a/Fe]`).

### Confundidores potenciais (fora das features até prova em contrário)

`ra`, `dec`, `l`, `b`, `pmra`, `pmdec`. No Trilho B todas as estrelas estão no campo do Kepler (l entre 68° e 84°), então as posições não carregam informação nenhuma lá.

`parallax` e `phot_g_mean_mag` ficam como `feature_candidata`, porque são a base de M_G. Mesmo assim, devem ser investigadas com SHAP na Fase 4 (regra 5).

### Colunas com `verificar=True` (7 no A, 22 no B)

- **Não conferidas na documentação:** o CDS estava inacessível durante o APPLY, então as notas numeradas (1)–(9) do ReadMe do APOKASC-3 não foram lidas. Faltam: significado exato de `EvolSt`, `EvolSrc`, `CatTab`, `SeisSrc`, `InvRGaia`, `alphaCat` e dos fatores `fDNu`/`fNumax`.
- **Classificação provisória:**
  - `classprob_dsc_combmod_star`: tratada como qualidade, não como baseline (ver desvio no SUMMARY).
  - Pan-STARRS: decisão aberta, como o WISE.
  - `xm_flag`: provisória.

## Decisões pendentes (fora deste plano)

- Incluir ou não a fotometria Pan-STARRS como feature.
- Incluir ou não o WISE (ainda não foi baixado).
- Tratamento de extinção. Não pode usar a extinção do GSP-Phot nas features; ver regra 1.
