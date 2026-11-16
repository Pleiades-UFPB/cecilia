# Dados — CECILIA

Nenhum arquivo de dados é versionado. Este manifesto é a fonte de verdade sobre o que existe em `data/` e como foi obtido.

Tudo em `data/raw/` é gerado por `uv run python -m cecilia.data_assembly.fetch_raw <etapa>` (ver a docstring para as etapas), exceto os dois arquivos das Plêiades, indicados na tabela. Cada arquivo gravado também ganha uma linha em `data/raw/MANIFEST.jsonl`, com a consulta ADQL/URL completa.

## Estrutura

- `raw/` — cache exato das consultas remotas (Parquet). Nunca editar.
- `interim/` — após cross-match e cortes de qualidade.
- `processed/` — matrizes de features e partições treino/validação/teste.

## Fontes

| Fonte | Uso | Trilho | Acesso |
|---|---|---|---|
| Gaia DR3 `gaiadr3.gaia_source` | astrometria, fotometria G/BP/RP, RUWE | A, B | Gaia Archive TAP (`gea.esac.esa.int`), upload de `source_id` em lotes de 20k (`tap_upload.ids`), usuário anônimo |
| Gaia DR3 `gaiadr3.astrophysical_parameters` | Teff/log g/[M/H] GSP-Phot — **só para baseline e análise, nunca feature** | A, B | idem, LEFT JOIN na mesma consulta do `gaia_source` |
| 2MASS PSC (vizinho no Gaia) | fotometria J, H, Ks | A, B | `gaiadr3.tmass_psc_xsc_best_neighbour` → `gaiadr3.tmass_psc_xsc_join` → `gaiadr1.tmass_original_valid`, restrito a `designation = original_ext_source_id` |
| LAMOST DR11 v2.0 LRS | classe espectral (rótulo) | A | VizieR `V/162/dr11l`, arquivo `dr11l.dat.gz` do espelho CfA (`vizier.cfa.harvard.edu`); já traz `GaiaDR3` (= `source_id`), sem cross-match |
| APOKASC-3 | νmax, Δν, estágio evolutivo, massa, idade | B | VizieR `J/ApJS/276/69/table4`, espelho CfA; já traz `GaiaDR3` e `2MASS` |

### Observações

- **Espelho:** todo acesso ao VizieR usa o espelho CfA/Harvard. Os servidores chineses do LAMOST são lentos e não são usados para transferir dados.
- **LAMOST DR12:** o DR12 v2.0 (público desde 2026-09-11) só existe em lamost.org. O VizieR tem o DR11 v2.0, com cerca de 5% menos espectros (11.931.197 contra 12.602.862).
- **Sentinelas em `raw/`:** os valores sentinela ficam como vieram. No LAMOST: `-9999` em snr*, z, e_z, GaiaDR3 e Gmag; `-999` nas magnitudes PS1; `99` em offsetsv; PanSTARRS vazio vira nulo. No APOKASC-3: `-9999.99` em [C/Fe] e [N/Fe], `-999.99` nos erros. Em `interim/` (`cecilia.data_assembly.clean_sentinels`) todos esses viram nulo. Ficam como estão: snr* e FiberID iguais a 99 (valores reais) e `E_Age*` = 99 do APOKASC-3 (provável teto).
- **Ids grandes:** ler os Parquet com `pd.read_parquet(..., dtype_backend="numpy_nullable")`. Sem isso, uma coluna int64 com nulos (PanSTARRS) vira float64 e os ids de 18–19 dígitos são arredondados.
- **Tabelas cruzadas em `interim/`:** uma linha por estrela; colunas do Gaia e do 2MASS com os nomes originais, LAMOST e APOKASC-3 com prefixo `lamost_`/`apokasc_`. Colunas cujo nome só difere de outra por maiúsculas/minúsculas são renomeadas, porque o DuckDB não diferencia caixa: `Gmag` do LAMOST (G do Gaia) vira `lamost_Gmag_gaia` (o `lamost_gmag` é o g do Pan-STARRS) e `e_AgeRGB`/`e_AgeRC` do APOKASC-3 (incerteza inferior) viram `apokasc_e_AgeRGB_inf`/`apokasc_e_AgeRC_inf`. Até o plano 02-01 essas colunas saíam como `*_1` com o conteúdo da outra coluna do par. Ainda sem cortes de qualidade (RUWE, S/N, ph_qual). Os arquivos do Gaia/2MASS só existem em `raw/` (não têm sentinelas); a versão cruzada é a que fica em `interim/`.
- **LAMOST, vários espectros por estrela:** escolher o de maior S/N em `interim/`. Filtro de estrelas usado no trilho A: `Class == "STAR"`, `FiberType == "Obj"`, `GaiaDR3 != -9999`.
- **Erros de magnitude no Gaia:** não há colunas de erro de magnitude G/BP/RP; usar σ ≈ 1.0857 / `*_flux_over_error`.
- **2MASS sem `cc_flg`:** a cópia do 2MASS no Gaia Archive não tem `cc_flg`. Se precisar, ele está em VizieR `II/246/out`, coluna `Cflg`.
- **APOKASC-3, idades:** `AgeCat` `RGB_AGB` e `RC/RGB` são ambíguos. Os `e_Age*` são negativos (erro inferior) e `E_Age* = 99` parece teto.
- **Gaia Archive fora do ar:** de 25/11/2026 a 02/12/2026, para o lançamento do DR4. Limites e esquemas podem mudar depois.

## Manifesto

| Arquivo | Fonte | Consulta / URL | Data | Linhas | Responsável |
|---|---|---|---|---|---|
| `raw/apokasc3_table4.parquet` | APOKASC-3 (VizieR J/ApJS/276/69) | `Vizier(columns=['**'], row_limit=-1, vizier_server='vizier.cfa.harvard.edu').get_catalogs('J/ApJS/276/69/table4')` | 2026-10-22 | 15.808 | Arthur Stern |
| `raw/gaia_dr3_trailB_source.parquet` | Gaia DR3 | `gaia_source` ⟕ `astrophysical_parameters` para os 15.808 `GaiaDR3` do APOKASC-3 (consulta em `MANIFEST.jsonl`) | 2026-10-22 | 15.808 | Arthur Stern |
| `raw/gaia_dr3_trailB_tmass.parquet` | Gaia DR3 / 2MASS | cadeia best_neighbour → join → tmass_original_valid para os mesmos ids; 21 sem 2MASS | 2026-10-27 | 15.787 | Arthur Stern |
| `raw/lamost/dr11l.dat.gz`, `raw/lamost_dr11_lrs.parquet` | LAMOST DR11 v2.0 LRS (VizieR V/162) | `https://vizier.cfa.harvard.edu/ftp/cats/V/162/dr11l.dat.gz`, convertido sem filtros (36 campos do ReadMe) | 2026-10-27 | 11.931.197 | Arthur Stern |
| `raw/gaia_dr3_trailA_source.parquet` | Gaia DR3 | `gaia_source` ⟕ `astrophysical_parameters` para os 7.751.078 `GaiaDR3` únicos com `Class == "STAR"`, `FiberType == "Obj"`, `GaiaDR3 != -9999`; 388 lotes de 20k | 2026-10-27 | 7.751.078 | Arthur Stern |
| `raw/gaia_dr3_trailA_tmass.parquet` | Gaia DR3 / 2MASS | cadeia 2MASS para os mesmos ids; 119.718 sem 2MASS | 2026-10-27 | 7.631.360 | Arthur Stern |
| `interim/lamost_dr11_lrs.parquet` | `raw/lamost_dr11_lrs.parquet` | sentinelas → nulo (`cecilia.data_assembly.clean_sentinels`; contagens em `interim/MANIFEST.jsonl`) | 2026-10-27 | 11.931.197 | Arthur Stern |
| `interim/apokasc3_table4.parquet` | `raw/apokasc3_table4.parquet` | idem | 2026-10-27 | 15.808 | Arthur Stern |
| `interim/trailA_lamost_gaia_2mass.parquet` | `interim/lamost_dr11_lrs.parquet` + `raw/gaia_dr3_trailA_*` | LAMOST `STAR`/`Obj` com GaiaDR3, 1 espectro por estrela: maior `snri` se a estrela é tipo M (≥ metade dos espectros com subClass dM*/gM*/sdM*; 678.801 estrelas), senão maior `snrg`; empate → outra banda → MJD → ObsID. `lamost_snr_band` = banda usada, `lamost_n_spectra` = nº de espectros ⟕ Gaia ⟕ 2MASS em `source_id` (`cecilia.data_assembly.build_interim`); todas com Gaia, 7.631.360 com 2MASS | 2026-11-16 (regenerado no 02-01; 1ª versão 2026-10-27) | 7.751.078 | Arthur Stern |
| `interim/trailB_apokasc_gaia_2mass.parquet` | `interim/apokasc3_table4.parquet` + `raw/gaia_dr3_trailB_*` | APOKASC-3 ⟕ Gaia ⟕ 2MASS em `source_id`; todas com Gaia, 15.787 com 2MASS | 2026-11-16 (regenerado no 02-01; 1ª versão 2026-10-27) | 15.808 | Arthur Stern |
| `interim/trailA_lamost_gaia_2mass_200pc.parquet` | `interim/trailA_lamost_gaia_2mass.parquet` | só estrelas a menos de 200 pc: `parallax > 5` e `parallax_over_error >= 10`; coluna nova `dist_pc = 1000 / parallax` (`cecilia.visualization.filter_200pc`) | 2026-11-16 (regenerado no 02-01; 1ª versão 2026-10-27) | 207.030 | Arthur Stern |
| `interim/trailB_apokasc_gaia_2mass_200pc.parquet` | `interim/trailB_apokasc_gaia_2mass.parquet` | idem | 2026-11-16 (regenerado no 02-01; 1ª versão 2026-10-27) | 45 | Arthur Stern |
| `raw/gaia_dr3_pleiades_gflux.parquet` | Gaia DR3 | `phot_g_mean_flux`, `phot_g_mean_flux_error` para os 50.025 `source_id` do cone das Plêiades (`cecilia.visualization.pleiades_region`; consulta em `raw/MANIFEST.jsonl`) | 2026-10-27 | 50.025 | Arthur Stern |
| `raw/gaia_dr3_pleiades_cone_G17.parquet` | Gaia DR3 (VizieR I/355/gaiadr3, espelho CfA) | cone de 2,8° em (56,75°, +24,12°), G < 17; colunas Source, RA/Dec, Gmag, BP-RP, Plx, e_Plx, pmRA, pmDE, RUWE, VarFlag renomeadas para os nomes do `gaia_source` (`cecilia.visualization.plot_pleiades_photo`); usado nas imagens do céu e no diagrama HR — o mesmo cone no Gaia Archive estoura 60 s | 2026-10-27 | 37.727 | Arthur Stern |
| `interim/pleiades_region.parquet` | `interim/trailA_lamost_gaia_2mass.parquet` + `raw/gaia_dr3_pleiades_gflux.parquet` | cone de 5° em (56,75°, +24,12°); `is_member`: movimento próprio a < 4 mas/ano de (20,0, −45,5) e 6,5 ≤ parallax ≤ 8,3 mas (717 candidatos); `dist_pc = 1000 / parallax` | 2026-11-16 (regenerado no 02-01; 1ª versão 2026-10-27) | 50.025 | Arthur Stern |

## Agradecimentos obrigatórios

Replicar no README principal e nos artigos.

**Gaia DR3.** Citar Gaia Collaboration, Prusti et al. 2016, A&A 595, A1, e Gaia Collaboration, Vallenari et al. 2023, A&A 674, A1. O texto abaixo vem de uma cópia do Wayback de 2026-02; a página da ESA estava fora do ar (503) na verificação.

> This work has made use of data from the European Space Agency (ESA) mission Gaia (https://www.cosmos.esa.int/gaia), processed by the Gaia Data Processing and Analysis Consortium (DPAC, https://www.cosmos.esa.int/web/gaia/dpac/consortium). Funding for the DPAC has been provided by national institutions, in particular the institutions participating in the Gaia Multilateral Agreement.

**2MASS.** Citar Skrutskie et al. 2006, AJ 131, 1163.

> This publication makes use of data products from the Two Micron All Sky Survey, which is a joint project of the University of Massachusetts and the Infrared Processing and Analysis Center/California Institute of Technology, funded by the National Aeronautics and Space Administration and the National Science Foundation.

**LAMOST.** Citar Luo et al. 2026, VizieR V/162.

> Guoshoujing Telescope (the Large Sky Area Multi-Object Fiber Spectroscopic Telescope LAMOST) is a National Major Scientific Project built by the Chinese Academy of Sciences. Funding for the project has been provided by the National Development and Reform Commission. LAMOST is operated and managed by the National Astronomical Observatories, Chinese Academy of Sciences.

**APOKASC-3.** Citar Pinsonneault et al. 2025, ApJS 276, 69 (doi:10.3847/1538-4365/ad9fef). Ele combina dados Kepler e SDSS-IV/APOGEE.

> This paper includes data collected by the Kepler mission and obtained from the MAST data archive at the Space Telescope Science Institute (STScI). Funding to US Institutions for the Kepler mission was provided by the NASA Science Mission Directorate. STScI is operated by the Association of Universities for Research in Astronomy, Inc., under NASA contract NAS5–26555.

> Funding for the Sloan Digital Sky Survey IV has been provided by the Alfred P. Sloan Foundation, the U.S. Department of Energy Office of Science, and the Participating Institutions. SDSS-IV acknowledges support and resources from the Center for High Performance Computing at the University of Utah. The SDSS website is www.sdss4.org. SDSS-IV is managed by the Astrophysical Research Consortium for the Participating Institutions of the SDSS Collaboration including […] — texto completo, com a lista de instituições, em https://www.sdss4.org/collaboration/citing-sdss/ (usar o texto SDSS-IV, não o SDSS-V de sdss.org).

**VizieR.** Citar Ochsenbein, Bauer & Marcout 2000, A&AS 143, 23.

> This research has made use of the VizieR catalogue access tool, CDS, Strasbourg, France (DOI : 10.26093/cds/vizier). The original description of the VizieR service was published in 2000, A&AS 143, 23
