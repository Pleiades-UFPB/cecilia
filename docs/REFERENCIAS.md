# Referências — CECILIA

## Artigos-base

### Li, Lu, Wang & Wang (2025). *Machine Learning in Stellar Astronomy: Progress up to 2024.* arXiv:2502.15300.
**Papel:** referência de domínio. Panorama de ML aplicado a classificação estelar e inferência de parâmetros.
**Seções mais úteis:** III (fundamentos: RF, SVM, KNN, redes), IV (fontes de dados), V (classificação — ex.: Maravelias et al. 2022 com curvas PR por classe), VI (inferência de parâmetros), VII.E (estrelas variáveis), VII.I/Giants (Hon et al. 2018, oscilações em gigantes).
**Alerta citado pelos próprios autores:** qualidade dos dados de treino e natureza "caixa-preta" dos modelos.

### Sahlmann & Gómez (2025). *Machine learning-based identification of Gaia astrometric exoplanet orbits.* MNRAS. arXiv:2404.09350.
**Papel:** referência **metodológica**, não de domínio (exoplanetas estão fora do escopo).
**O que aproveitar:**
- Consulta e junção de tabelas do Gaia DR3 por `source_id`.
- Imputação documentada de campos ausentes (tabela de valores de preenchimento).
- XGBoost + Balanced Random Forest para classes muito desbalanceadas.
- Validação cruzada k-fold.
- Uso de SHAP para identificar e **descartar confundidores** (paralaxe e magnitude aparente pareciam importantes por viés de seleção, não por física).
- Discussão honesta de limitações: o modelo tende a encontrar candidatos parecidos com o conjunto de treino.

## Fontes de dados

- **Gaia DR3** — Gaia Collaboration et al. (2023), A&A 674, A1. Arquivo: https://gea.esac.esa.int/archive/
- **LAMOST** — Cui et al. (2012), RAA 12, 1197. Release a definir na Fase 02.
- **2MASS** — Skrutskie et al. (2006), AJ 131, 1163.
- **APOKASC-3** — Pinsonneault et al. (verificar ano e referência final na Fase 02).

## Contexto histórico

- Payne, C. H. (1925). *Stellar Atmospheres.* Harvard Observatory Monographs No. 1 — tese que dá nome ao projeto.

## Leituras de apoio sugeridas

- Hon, Stello & Zinn (2018), ApJ 859, 64 — redes neurais para oscilações em gigantes (Trilho B).
- Maravelias et al. (2022), A&A 666, 26 — classificador fotométrico com curvas PR por classe (Trilho A).
