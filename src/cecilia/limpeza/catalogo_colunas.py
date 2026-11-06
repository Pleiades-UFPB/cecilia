"""Catálogo de colunas: categoria e justificativa de cada coluna das tabelas interim.

Fonte de verdade para:
- quais colunas são proibidas como feature (`colunas_proibidas`), usada pelo teste
  anti-vazamento (AC-03.4, AC-T.2);
- quais colunas servem a cortes de qualidade, quais são candidatas a feature e quais
  são descartadas como irrelevantes.

Cada entrada é `coluna: Coluna(categoria, justificativa, verificar)`. `verificar=True`
quer dizer que o significado exato da coluna não foi conferido na documentação oficial
(regra 6 do CLAUDE.md) e a categoria é provisória.

Referências usadas na conferência:
- Gaia DR3: datamodel de `gaia_source` e `astrophysical_parameters` (nomes de colunas
  conferidos no esquema real do Parquet, consulta em fetch_raw.py);
- 2MASS: `gaiadr1.tmass_original_valid` e `gaiadr3.tmass_psc_xsc_best_neighbour`;
- LAMOST DR11 v2.0 LRS: ReadMe do VizieR V/162 (cópia em data/raw/lamost/ReadMe);
- APOKASC-3: descrições de coluna do VizieR J/ApJS/276/69/table4 (via astroquery). As
  notas numeradas (1)-(9) do ReadMe não foram lidas: colunas que dependem delas têm
  verificar=True.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Categoria(StrEnum):
    FEATURE_CANDIDATA = "feature_candidata"
    ROTULO = "rotulo"
    SO_BASELINE = "so_baseline"  # proibida como feature; uso em baseline ou análise
    QUALIDADE = "qualidade"  # usada em corte de qualidade, não como feature
    IDENTIFICADOR = "identificador"
    CONFUNDIDOR_POTENCIAL = "confundidor_potencial"
    IRRELEVANTE = "irrelevante"


@dataclass(frozen=True)
class Coluna:
    categoria: Categoria
    justificativa: str
    verificar: bool = False


F, R, B, Q, ID, C, X = (
    Categoria.FEATURE_CANDIDATA, Categoria.ROTULO, Categoria.SO_BASELINE,
    Categoria.QUALIDADE, Categoria.IDENTIFICADOR, Categoria.CONFUNDIDOR_POTENCIAL,
    Categoria.IRRELEVANTE,
)


def _mesma(cols, categoria, justificativa, verificar=False) -> dict[str, Coluna]:
    return {c: Coluna(categoria, justificativa, verificar) for c in cols}


# --------------------------------------------------------------------- Gaia DR3 source
GAIA = {
    "source_id": Coluna(ID, "Identificador Gaia DR3; chave de junção."),
    "ra": Coluna(C, "Posição reflete a pegada do levantamento, não física da estrela."),
    "dec": Coluna(C, "Posição reflete a pegada do levantamento, não física da estrela."),
    "l": Coluna(C, "Latitude/longitude galáctica: correlaciona com extinção e população, "
                   "mas também com a seleção do levantamento."),
    "b": Coluna(C, "Latitude/longitude galáctica: correlaciona com extinção e população, "
                   "mas também com a seleção do levantamento."),
    "parallax": Coluna(F, "Base da magnitude absoluta M_G. Sozinha é confundidor potencial "
                          "(viés de seleção, Sahlmann & Gómez 2025)."),
    "pmra": Coluna(C, "Movimento próprio depende da distância e da cinemática; sem relação "
                      "direta com classe espectral ou estágio evolutivo."),
    "pmdec": Coluna(C, "Movimento próprio depende da distância e da cinemática; sem relação "
                       "direta com classe espectral ou estágio evolutivo."),
    "phot_g_mean_mag": Coluna(F, "Base de M_G e de G−RP, G−Ks. Magnitude aparente sozinha é "
                                 "confundidor potencial (viés de seleção)."),
    "phot_bp_mean_mag": Coluna(F, "Base das cores BP−RP."),
    "phot_rp_mean_mag": Coluna(F, "Base das cores BP−RP, G−RP."),
    "bp_rp": Coluna(F, "Cor BP−RP: indicador fotométrico de temperatura, sem correção de "
                       "extinção."),
    "radial_velocity": Coluna(X, "Velocidade radial (RVS): cinemática, sem relação física "
                                 "direta com os rótulos; disponível só para estrelas brilhantes."),
    "has_xp_continuous": Coluna(X, "Flag de disponibilidade de produto, não mede a estrela."),
    "has_xp_sampled": Coluna(X, "Flag de disponibilidade de produto, não mede a estrela."),
    "has_rvs": Coluna(X, "Flag de disponibilidade de produto, não mede a estrela."),
    "classprob_dsc_combmod_star": Coluna(
        Q, "Probabilidade de ser estrela (DSC), não classe espectral: serve para remover "
           "não-estrelas. Se usada como feature, investigar vazamento (vem dos espectros BP/RP).",
        verificar=True),
    **_mesma(
        ["parallax_error", "parallax_over_error", "pmra_error", "pmdec_error", "ruwe",
         "astrometric_excess_noise", "astrometric_params_solved", "visibility_periods_used",
         "ipd_frac_multi_peak", "ipd_gof_harmonic_amplitude", "duplicated_source"],
        Q, "Qualidade astrométrica (RUWE, erros, multiplicidade de imagem): candidata a corte."),
    **_mesma(
        ["phot_g_mean_flux_over_error", "phot_bp_mean_flux_over_error",
         "phot_rp_mean_flux_over_error", "phot_bp_n_obs", "phot_rp_n_obs",
         "phot_bp_rp_excess_factor", "phot_bp_n_blended_transits",
         "phot_rp_n_blended_transits"],
        Q, "Qualidade fotométrica Gaia (S/N, excesso BP/RP, contaminação): candidata a corte."),
    "phot_variable_flag": Coluna(Q, "Variabilidade: fotometria média de variáveis é menos "
                                    "confiável; candidata a corte ou análise."),
    "radial_velocity_error": Coluna(X, "Erro de coluna irrelevante (radial_velocity)."),
    "non_single_star": Coluna(Q, "Binária detectada pelo Gaia: sistemas multi-estelares "
                                 "estão fora do escopo; candidata a corte."),
}

# ------------------------------------------------------- Gaia DR3 GSP-Phot (AP_COLS)
# Todas saem do mesmo ajuste GSP-Phot (BP/RP + G + paralaxe) que produz Teff, log g e
# [M/H]: são estimadas juntas e uma reconstrói a outra (ex.: cor intrínseca =
# bp_rp − ebpminrp_gspphot; L e R fixam Teff).
_GSPPHOT_BASE = ["teff_gspphot", "logg_gspphot", "mh_gspphot", "distance_gspphot",
                 "azero_gspphot", "ag_gspphot", "ebpminrp_gspphot", "radius_gspphot",
                 "mg_gspphot"]
GSPPHOT_COLS = [f"{p}{s}" for p in _GSPPHOT_BASE for s in ("", "_lower", "_upper")] + [
    "libname_gspphot", "logposterior_gspphot", "mcmcaccept_gspphot"]

GSPPHOT_A = _mesma(
    GSPPHOT_COLS, B,
    "Saída do ajuste GSP-Phot, o mesmo cálculo de Teff/log g/[M/H] (regra 1 do CLAUDE.md). "
    "teff_gspphot define o baseline do Trilho A; as demais só em análise.")
GSPPHOT_B = _mesma(
    GSPPHOT_COLS, X,
    "No Trilho B o APOKASC-3 já traz Teff e [Fe/H] espectroscópicos (APOGEE), mais "
    "precisos que o GSP-Phot; não é usada.")

# -------------------------------------------------------------------------- 2MASS
TMASS = {
    "original_ext_source_id": Coluna(ID, "Designação 2MASS do vizinho no cross-match Gaia."),
    "designation": Coluna(ID, "Designação 2MASS PSC."),
    "tmass_ra": Coluna(X, "Posição 2MASS: duplica ra/dec do Gaia."),
    "tmass_dec": Coluna(X, "Posição 2MASS: duplica ra/dec do Gaia."),
    "j_m": Coluna(F, "Magnitude J: base de J−H e de cores Gaia−2MASS."),
    "h_m": Coluna(F, "Magnitude H: base de J−H e H−Ks."),
    "ks_m": Coluna(F, "Magnitude Ks: base de H−Ks e G−Ks."),
    "j_msigcom": Coluna(Q, "Incerteza total em J: candidata a corte."),
    "h_msigcom": Coluna(Q, "Incerteza total em H: candidata a corte."),
    "ks_msigcom": Coluna(Q, "Incerteza total em Ks: candidata a corte."),
    "ph_qual": Coluna(Q, "Qualidade fotométrica 2MASS por banda (A–X): candidata a corte."),
    "ext_key": Coluna(Q, "Associação com fonte estendida do 2MASS XSC: candidata a corte."),
    "j_date": Coluna(X, "Data da observação 2MASS: metadado."),
    "angular_distance": Coluna(Q, "Distância do cross-match Gaia↔2MASS: candidata a corte."),
    "number_of_neighbours": Coluna(Q, "Ambiguidade do cross-match: candidata a corte."),
    "number_of_mates": Coluna(Q, "Ambiguidade do cross-match: candidata a corte."),
    "xm_flag": Coluna(Q, "Flag do cross-match Gaia↔2MASS: candidata a corte.", verificar=True),
}

# ------------------------------------------------------------------------- LAMOST
LAMOST = {
    **_mesma(["lamost_ObsID", "lamost_uID", "lamost_gpID", "lamost_Target",
              "lamost_PlanID", "lamost_spID", "lamost_FiberID", "lamost_GaiaDR3",
              "lamost_PanSTARRS"],
             ID, "Identificador do espectro, da placa, da fibra ou de outro catálogo."),
    **_mesma(["lamost_ObsDate", "lamost_LMJD", "lamost_MJD"],
             X, "Data da observação: metadado."),
    **_mesma(["lamost_RAdeg", "lamost_DEdeg", "lamost_RAOdeg", "lamost_DEOdeg"],
             X, "Posição da fibra/catálogo de entrada: duplica ra/dec do Gaia."),
    **_mesma(["lamost_snru", "lamost_snrg", "lamost_snrr", "lamost_snri", "lamost_snrz"],
             Q, "S/N do espectro por banda: corte de qualidade do rótulo."),
    "lamost_snr_band": Coluna(Q, "Banda de S/N usada para escolher o espectro (build_interim)."),
    "lamost_n_spectra": Coluna(X, "Número de espectros da estrela: reflete estratégia de "
                                  "observação, não a estrela."),
    "lamost_Class": Coluna(R, "Classe do LASP (STAR/GALAXY/QSO); no Trilho A é sempre STAR "
                              "(filtro do build_interim). Fonte do rótulo."),
    "lamost_subClass": Coluna(R, "Subclasse espectral LASP: rótulo do Trilho A."),
    "lamost_z": Coluna(B, "Redshift medido no mesmo espectro do rótulo: mesma fonte (regra 1)."),
    "lamost_e_z": Coluna(B, "Incerteza de lamost_z: mesma fonte do rótulo."),
    **_mesma(["lamost_gmag", "lamost_rmag", "lamost_imag", "lamost_zmag", "lamost_ymag"],
             F, "Fotometria Pan-STARRS: independente do espectro, mas incluir ou não é "
                "decisão aberta (como WISE). ~50–70% ausentes no LAMOST bruto.",
             verificar=True),
    "lamost_Gmag_1": Coluna(X, "DEFEITO do build_interim: deveria ser o G do Gaia copiado "
                               "pelo LAMOST, mas contém o g do Pan-STARRS (colisão gmag/Gmag no "
                               "DuckDB, que não diferencia maiúsculas). Usar phot_g_mean_mag."),
    "lamost_FiberType": Coluna(X, "Constante 'Obj' no Trilho A (filtro do build_interim)."),
    "lamost_offsets": Coluna(Q, "Fibra deslocada (estrelas muito brilhantes, r<11): "
                                "espectro pode ser menos confiável."),
    "lamost_offsetsv": Coluna(Q, "Tamanho do deslocamento da fibra, em arcsec."),
    "lamost_FiberMask": Coluna(Q, "Máscara de bits de problemas na fibra (ReadMe nota 2)."),
    "lamost_fNFlux": Coluna(X, "Se o FITS tem fluxo normalizado: metadado de arquivo."),
}

# ------------------------------------------------------------------------ APOKASC-3
_EVOL = ("Depende do estágio evolutivo ou é calculada separadamente para RGB e RC: "
         "vazamento do rótulo do Trilho B.")
_ESCALA = ("Derivada de νmax, Δν e Teff por relações de escala: um modelo que a use só "
           "reaprende a fórmula (regra 1 do CLAUDE.md).")
_SPEC = ("Espectroscópica (APOGEE). Para estrelas com EvolSrc='Spec' o rótulo veio de "
         "classificação espectroscópica — usar como feature só na subamostra sísmica.")
APOKASC = {
    "apokasc_recno": Coluna(ID, "Número de registro do VizieR; não identifica a estrela."),
    "apokasc_KIC": Coluna(ID, "Kepler Input Catalog."),
    "apokasc_GaiaDR3": Coluna(ID, "Gaia DR3 source_id publicado pelo APOKASC-3 (= source_id)."),
    "apokasc_2MASS": Coluna(ID, "Designação 2MASS publicada pelo APOKASC-3."),
    "apokasc_Simbad": Coluna(X, "Coluna de link adicionada pelo CDS."),
    "apokasc_KCat": Coluna(X, "Coluna de link para o catálogo Kepler Q1-17 (CDS)."),
    "apokasc__RA": Coluna(X, "Posição derivada do nome 2MASS: duplica ra/dec."),
    "apokasc__DE": Coluna(X, "Posição derivada do nome 2MASS: duplica ra/dec."),
    "apokasc_EvolSt": Coluna(R, "Estágio evolutivo (RGB, RC, Dwarf, Unknown, RC/RGB): rótulo "
                                "do Trilho B. Significado dos valores na nota (1) do ReadMe.",
                             verificar=True),
    "apokasc_EvolSrc": Coluna(Q, "Origem do estágio evolutivo (Seis/Spec/None): define se o "
                                 "rótulo é sísmico; candidata a filtro.", verificar=True),
    "apokasc_CatTab": Coluna(Q, "Categoria da amostra (Gold, Silver, NoDet...): candidata a "
                                "corte.", verificar=True),
    "apokasc_SeisSrc": Coluna(Q, "Esquema de ponderação sísmica (nota 4).", verificar=True),
    "apokasc_SpecSrc": Coluna(Q, "Release APOGEE do dado espectroscópico (DR16/DR17).",
                              verificar=True),
    "apokasc_NNumax": Coluna(Q, "Número de valores de νmax filtrados (métodos concordantes)."),
    "apokasc_NDNu": Coluna(Q, "Número de valores de Δν filtrados (métodos concordantes)."),
    "apokasc_Quar": Coluna(Q, "Número de trimestres Kepler: duração da série temporal."),
    "apokasc_Numax": Coluna(F, "νmax: frequência de máxima potência (feature do roadmap)."),
    "apokasc_DNu": Coluna(F, "Δν: grande separação (feature do roadmap)."),
    "apokasc_e_Numax": Coluna(Q, "Incerteza de νmax."),
    "apokasc_e_DNu": Coluna(Q, "Incerteza de Δν."),
    **_mesma(["apokasc_fDNu", "apokasc_e_fDNu", "apokasc_fNumax"], B,
             "Fator de correção de Mosser para as relações de escala; " + _EVOL,
             verificar=True),
    **_mesma(["apokasc_Mass", "apokasc_e_Mass", "apokasc_Radius", "apokasc_e_Radius",
              "apokasc_loggSeis", "apokasc_e_loggSeis"], B, _ESCALA),
    "apokasc_Teff": Coluna(F, "Teff APOGEE (feature do roadmap). " + _SPEC, verificar=True),
    "apokasc_e_Teff": Coluna(Q, "Incerteza de Teff."),
    "apokasc_loggSpec": Coluna(F, "log g espectroscópico. " + _SPEC, verificar=True),
    "apokasc_e_loggSpec": Coluna(Q, "Incerteza de loggSpec."),
    "apokasc_[Fe/H]": Coluna(F, "[Fe/H] APOGEE (feature do roadmap). " + _SPEC,
                             verificar=True),
    "apokasc_e_[Fe/H]": Coluna(Q, "Incerteza de [Fe/H]."),
    "apokasc_[a/Fe]": Coluna(F, "[α/Fe] APOGEE: separa populações. " + _SPEC, verificar=True),
    "apokasc_e_[a/Fe]": Coluna(Q, "Incerteza de [α/Fe]."),
    **_mesma(["apokasc_[C/Fe]", "apokasc_e_[C/Fe]", "apokasc_[N/Fe]", "apokasc_e_[N/Fe]"], B,
             "Razão C/N muda com a mistura na subida do RGB e é usada na classificação "
             "espectroscópica do estágio evolutivo: risco de vazamento.", verificar=True),
    **_mesma(["apokasc_InvRGaia", "apokasc_e_InvRGaia"], B,
             "Raio inverso a partir de modelo MIST + Gaia (nota 7): grandeza derivada de "
             "modelo; proibida até conferir a nota.", verificar=True),
    "apokasc_AgeCat": Coluna(B, "Classe de idade recomendada (RC/RGB/RGB_AGB/NONE): "
                                "praticamente o próprio rótulo. " + _EVOL),
    **_mesma(["apokasc_AgeRGB", "apokasc_E_AgeRGB", "apokasc_AgeRC", "apokasc_E_AgeRC"], B,
             "Idade Garstec calculada para RGB ou para RC. " + _EVOL),
    **_mesma(["apokasc_e_AgeRGB_1", "apokasc_e_AgeRC_1"], B,
             "DEFEITO do build_interim: deveria ser a incerteza inferior (negativa) da idade, "
             "mas repete E_Age* (colisão e_/E_ no DuckDB, que não diferencia maiúsculas). "
             + _EVOL),
    "apokasc_vsini": Coluna(F, "Rotação projetada (APOGEE); faixa inclui valores negativos.",
                            verificar=True),
    "apokasc_alphaCat": Coluna(X, "Categoria derivada de [α/Fe] (nota 9): redundante.",
                               verificar=True),
}

CATALOGO = {
    "A": {**GAIA, **GSPPHOT_A, **TMASS, **LAMOST},
    "B": {**GAIA, **GSPPHOT_B, **TMASS, **APOKASC},
}


def catalogo(trilho: str) -> dict[str, Coluna]:
    if trilho not in CATALOGO:
        raise ValueError(f"trilho deve ser 'A' ou 'B', não {trilho!r}")
    return CATALOGO[trilho]


def colunas_por_categoria(trilho: str, categoria: Categoria) -> list[str]:
    return [c for c, info in catalogo(trilho).items() if info.categoria == categoria]


def colunas_proibidas(trilho: str) -> set[str]:
    """Colunas que nunca podem ser feature: rótulo e tudo do mesmo cálculo/fonte."""
    return {c for c, info in catalogo(trilho).items()
            if info.categoria in (Categoria.ROTULO, Categoria.SO_BASELINE)}
