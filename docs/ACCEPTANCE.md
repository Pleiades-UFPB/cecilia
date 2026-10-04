# Critérios de aceitação — CECILIA

Formato BDD (Given / When / Then), referenciável pelos planos PAUL como `AC-<fase>.<n>`. Planos podem detalhar ou acrescentar ACs, mas não afrouxar os transversais.

## Transversais (valem para todas as fases)

**AC-T.1 — Reprodutibilidade**
Given um clone limpo do repositório e `uv sync` executado
When o comando documentado da fase é executado
Then os mesmos artefatos (tabelas, métricas, figuras) são produzidos, com diferenças numéricas apenas dentro de tolerância documentada

**AC-T.2 — Sem vazamento de rótulo**
Given a lista de features de qualquer modelo
When comparada à fonte do rótulo
Then nenhuma feature é derivada do rótulo ou do mesmo cálculo que o gera (no Trilho A: Teff, log g, [M/H] e tipos espectrais nunca são features)

**AC-T.3 — Teste intocado**
Given a partição de teste salva na Fase 03
When qualquer modelo é desenvolvido ou ajustado
Then o conjunto de teste só é usado na avaliação final registrada no SUMMARY

**AC-T.4 — Nada inventado**
Given qualquer nome de tabela, coluna ou campo de catálogo usado no código
When o plano é unificado
Then o nome foi verificado em documentação oficial ou consulta real, ou está marcado `# VERIFICAR` e reportado como DONE_WITH_CONCERNS

**AC-T.5 — Loop fechado**
Given um plano em andamento
When o responsável da fase muda
Then o plano anterior tem SUMMARY.md e o STATE.md está atualizado

## Fase 01 — Fundação

**AC-01.1** Given o repositório clonado, When `uv sync && uv run pytest` é executado, Then termina sem erros.
**AC-01.2** Given o `VOCABULARIO.md`, When revisado pelos cinco alunos, Then cada termo tem aprovação ou alteração registrada.
**AC-01.3** Given a tabela de estrelas de aquecimento, When o script é executado, Then gera um diagrama HR em arquivo com eixo de cor invertido corretamente (estrelas quentes à esquerda).

## Fase 02 — Aquisição

**AC-02.1** Given uma consulta já executada, When executada novamente, Then lê do cache em `data/raw/` sem acessar a rede.
**AC-02.2** Given cada arquivo em `data/raw/`, When o manifesto é consultado, Then registra origem, consulta/URL, data e número de linhas.
**AC-02.3** Given o cross-match do Trilho A, When concluído, Then a taxa de associação e o número de fontes por classe espectral são reportados.

## Fase 03 — Limpeza e features

**AC-03.1** Given os cortes de qualidade, When aplicados, Then cada corte reporta quantas fontes removeu e por quê.
**AC-03.2** Given valores ausentes, When tratados, Then a estratégia e a contagem por coluna estão documentadas.
**AC-03.3** Given a partição, When gerada, Then usa semente fixa, é estratificada pelo rótulo e é salva em disco.
**AC-03.4** Given a matriz de features, When o teste anti-vazamento roda, Then falha se qualquer coluna proibida estiver presente.

## Fase 04 — Classificação espectral

**AC-04.1** Given o baseline por faixas de Teff, When avaliado no teste, Then macro-F1 e matriz de confusão são registrados.
**AC-04.2** Given os modelos de ML, When avaliados no teste, Then macro-F1, matriz de confusão e curva PR por classe são registrados e comparados ao baseline.
**AC-04.3** Given a análise SHAP, When concluída, Then as 5 features mais importantes são listadas com justificativa física ou marcadas como possíveis confundidores.

## Fase 05 — Asterossismologia

**AC-05.1** Given o classificador RGB vs RC, When avaliado no teste, Then métricas e comparação com baseline são registradas.
**AC-05.2** Given a interpretação SHAP, When concluída, Then o papel de νmax e Δν é discutido à luz do vocabulário.
**AC-05.3** Given o exercício opcional de regressão de massa, When realizado, Then o SUMMARY declara explicitamente que o alvo deriva das relações de escala.

## Fase 06 — Análise

**AC-06.1** Given o diagrama HR, When gerado, Then mostra rótulo e predição lado a lado, com legenda e unidades.
**AC-06.2** Given os erros do modelo, When analisados, Then sua distribuição no HR é discutida no relatório da fase.

## Fase 07 — Interior 1D

**AC-07.1** Given uma estrela tipo solar, When visualizada, Then mostra perfis radiais de T e ρ e identifica as camadas.
**AC-07.2** Given a fonte de perfis com composição, When disponível, Then mostra X e Y em função do raio, com o núcleo depletado em H.
**AC-07.3** Given a visualização, When aberta, Then informa ao usuário a origem do modelo (politropo, modelo tabelado ou MESA).
