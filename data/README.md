# Dados — CECILIA

Nenhum arquivo de dados é versionado. Este manifesto é a fonte de verdade sobre o que existe em `data/` e como foi obtido.

## Estrutura

- `raw/` — cache exato das consultas remotas (Parquet). Nunca editar.
- `interim/` — após cross-match e cortes de qualidade.
- `processed/` — matrizes de features e partições treino/validação/teste.

## Fontes previstas

| Fonte | Uso | Trilho | Acesso |
|---|---|---|---|
| Gaia DR3 `gaia_source` | astrometria, fotometria G/BP/RP, RUWE | A | Gaia Archive (ADQL via astroquery) |
| Gaia DR3 `astrophysical_parameters` | Teff/log g/[M/H] GSP-Phot — **só para baseline e análise, nunca feature** | A | idem |
| 2MASS (vizinho no Gaia) | fotometria J, H, Ks | A | tabela de cross-match do Gaia — VERIFICAR nome |
| LAMOST LRS | classe espectral (rótulo) | A | release e forma de cross-match — VERIFICAR na Fase 02 |
| APOKASC-3 | νmax, Δν, estágio evolutivo, massa, idade | B | tabela do artigo — VERIFICAR colunas |

## Manifesto

| Arquivo | Fonte | Consulta / URL | Data | Linhas | Responsável |
|---|---|---|---|---|---|
| `aquecimento/estrelas_famosas.csv` | SIMBAD (CDS) | Digitado à mão a partir do SIMBAD (V, B, paralaxe, tipo espectral); bibcodes por linha | 2026-10-04 | 10 | Plano 01-02 |

**Exceção versionada:** `aquecimento/estrelas_famosas.csv` é o único arquivo de dados no git. É pequeno, digitado à mão e didático (aquecimento da Fase 01), não um cache de consulta. Todo o resto de `data/` segue a regra: não versionado.

## Agradecimentos obrigatórios

Registrar aqui o texto exigido por cada fonte e replicá-lo no README principal.
