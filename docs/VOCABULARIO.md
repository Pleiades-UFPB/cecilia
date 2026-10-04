# Vocabulário congelado — CECILIA

Termos oficiais do projeto. Código, documentos, planos PAUL e discussões usam estes termos com estes significados. Alterações exigem decisão registrada no `STATE.md`.

## Astronomia

| Termo | Definição no projeto |
|---|---|
| **Teff** | Temperatura efetiva da fotosfera, em kelvin. |
| **log g** | Logaritmo (base 10) da gravidade superficial, em cgs (cm/s²). Distingue anãs (~4,0–4,6) de gigantes (~1–3,5). |
| **[M/H]** / **[Fe/H]** | Metalicidade relativa ao Sol, em dex. [M/H] = metais totais; [Fe/H] = ferro. Não são intercambiáveis. |
| **Classe espectral** | Letra da sequência de Harvard: O, B, A, F, G, K, M. É, essencialmente, uma escala de temperatura. Pode ter subclasse numérica (G2, K5). |
| **Classe de luminosidade** | Numeral romano do sistema MK: I (supergigante), III (gigante), V (anã/sequência principal), etc. Independente da classe espectral. |
| **Tipo MK** | Combinação classe espectral + subclasse + classe de luminosidade (ex.: Sol = G2V). |
| **Diagrama HR** | Magnitude absoluta (ou luminosidade) vs cor (ou Teff). No projeto, a versão observacional: M_G vs BP−RP. |
| **Diagrama Kiel** | log g vs Teff. |
| **Magnitude aparente / absoluta** | Brilho observado / brilho a 10 pc. M = m + 5·log10(ϖ/1000) + 5, com ϖ em mas, sem correção de extinção. |
| **Paralaxe (ϖ)** | Em mas. Distância ≈ 1000/ϖ pc, válido só para paralaxe precisa. |
| **Extinção** | Escurecimento e avermelhamento pela poeira interestelar. Afeta cores e magnitudes. |
| **RUWE** | Renormalised Unit Weight Error do Gaia. Indicador de qualidade astrométrica; valores altos sugerem binária ou problema de ajuste. |
| **νmax** | Frequência de máxima potência das oscilações, em μHz. |
| **Δν** | Grande separação entre modos de mesma ordem angular, em μHz. Relaciona-se com a densidade média. |
| **Relações de escala** | Fórmulas que estimam massa e raio a partir de νmax, Δν e Teff. |
| **RGB** | Red Giant Branch: gigante queimando H em camada, núcleo inerte de He. |
| **RC** | Red Clump: gigante queimando He no núcleo. Mesma região do HR que parte do RGB — por isso é um problema de classificação real. |
| **Estágio evolutivo** | No Trilho B, o rótulo RGB vs RC. |
| **X, Y, Z** | Frações de massa de hidrogênio, hélio e metais. X + Y + Z = 1. |

## Dados

| Termo | Definição no projeto |
|---|---|
| **Fonte** | Uma entrada de catálogo (um objeto). No Gaia, identificada por `source_id`. |
| **Catálogo** | Tabela publicada por um levantamento (Gaia DR3, LAMOST, APOKASC-3, 2MASS). |
| **Cross-match** | Associação de fontes entre catálogos (por ID ou posição). |
| **Corte de qualidade** | Filtro documentado que remove fontes com medidas pouco confiáveis. |
| **Cache** | Cópia local em Parquet de toda consulta remota, em `data/raw/`. |
| **Manifesto de dados** | Registro em `data/README.md` de cada arquivo: origem, consulta, data, número de linhas. |

## Aprendizado de máquina

| Termo | Definição no projeto |
|---|---|
| **Rótulo** | Valor-alvo que o modelo aprende a prever. |
| **Feature** | Variável de entrada do modelo. |
| **Fonte do rótulo** | Catálogo/método que produziu o rótulo. Deve ser independente das features. |
| **Vazamento de rótulo** | Feature que contém, direta ou indiretamente, a informação do rótulo. Proibido. |
| **Confundidor** | Feature que o modelo considera importante por viés de seleção, sem justificativa física. |
| **Baseline** | Método simples baseado em regra ou física, contra o qual o ML é comparado. |
| **Conjunto de teste** | Partição separada uma única vez, com semente fixa, nunca usada no desenvolvimento. |
| **Macro-F1** | Média do F1 por classe, sem ponderar pelo tamanho. Métrica principal com classes desbalanceadas. |
| **Curva PR** | Precisão vs revocação por classe. |
| **SHAP** | Método de atribuição de contribuição de cada feature a cada predição. |

## PAUL

| Termo | Definição no projeto |
|---|---|
| **Fase** | Bloco do roadmap (ex.: 03-limpeza-features). Tem um responsável. |
| **Plano** | Unidade de trabalho PAUL dentro de uma fase (PLAN.md → SUMMARY.md). |
| **Loop** | PLAN → APPLY → UNIFY. Só está completo com o SUMMARY. |
| **AC** | Critério de aceitação no formato Given/When/Then. |
| **Responsável** | Aluno que conduz os loops da fase. |
| **Revisor** | Aluno que revisa o PR da fase. |
