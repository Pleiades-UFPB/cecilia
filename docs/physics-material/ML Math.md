
Este arquivo cobre a ferramenta estatística do CECILIA: como transformar uma tabela de features (cores, magnitudes) em um classificador, como medir se ele funciona e como interrogá-lo sobre o que aprendeu. Aplica-se aos dois trilhos, mas os exemplos físicos vêm principalmente do Trilho A. 

---

## 1. O que significa "aprender" aqui

*Ligação com o projeto: Fases 04 e 05.*

**Intuição.** Um classificador é uma função que recebe os números de uma estrela e devolve uma classe. "Aprender" é escolher essa função, dentre muitas possíveis, olhando exemplos em que a resposta já é conhecida.

**Analogia.** Um sommelier em treinamento prova centenas de vinhos com o rótulo à vista. Depois, prova vinhos sem rótulo e tenta acertar. Não decorou garrafas: formou critérios (acidez, corpo, aroma) que generalizam para vinhos novos.

**Formalização.** Cada estrela é um vetor de **features** $\large \mathbf{x}\in\mathbb{R}^n$ (por exemplo, $\large n=6$: BP−RP, G−RP, J−H, H−Ks, G−Ks e $\large M_G$). Seu **rótulo** é $\large y\in\{1,\dots,K\}$ (a classe espectral). Procuramos $\large f$ tal que

$$
\huge \hat y = f(\mathbf{x}) = \arg\max_{k}\ P(y=k\,|\,\mathbf{x})
$$

Isto é, o modelo estima a probabilidade de cada classe dado as features e escolhe a mais provável. O ajuste minimiza uma **função de perda** média sobre os $\large N$ exemplos de treino:

$$
\huge \hat f = \arg\min_{f}\ \frac{1}{N}\sum_{i=1}^{N}\ \mathcal{L}\big(y_i,\ f(\mathbf{x}_i)\big)
$$

**Exemplo.** Com $\large K=5$ classes (por exemplo, A, F, G, K, M), o modelo devolve cinco probabilidades que somam 1, como $\large (0{,}02,\ 0{,}10,\ 0{,}55,\ 0{,}30,\ 0{,}03)$, e o rótulo previsto é G, mas com bastante incerteza entre G e K.

**Armadilha.** Minimizar a perda no treino não é o objetivo. O objetivo é errar pouco em estrelas **novas**. Um modelo flexível o bastante decora os exemplos de treino, inclusive o ruído, e isso se chama *overfitting*. Quase todo o resto deste arquivo é sobre como evitar ou detectar isso.

---

## 2. Preparar os dados: ausentes, partições e vazamento

*Ligação com o projeto: Fase 03 (valores ausentes, partição treino/validação/teste, verificação anti-vazamento).*

### 2.1 Valores ausentes

**Intuição.** Nem toda estrela tem todas as colunas preenchidas (uma estrela pode não ter fotometria 2MASS de boa qualidade, por exemplo). É preciso decidir entre remover a linha ou **imputar** um valor.

**Formalização.** Imputação pela média: $\large x_{ij}\leftarrow \bar x_j$, onde $\large \bar x_j$ é a média da coluna $\large j$. É simples e deixa as variáveis com variância artificialmente menor, porque muitos pontos viram exatamente o valor central.

**Exemplo.** Em 1000 estrelas, 100 sem $\large J-H$. Remover reduz a amostra em 10%, mas pode eliminar justamente as estrelas mais fracas, cuja fotometria é pior (viés de seleção). Imputar mantém a amostra, e o preço é preencher com um número que a estrela não tem. Uma técnica comum é adicionar uma coluna indicadora ("este valor foi imputado"), para que o modelo possa usar a própria ausência como informação.

**Armadilha.** A média (ou qualquer valor de imputação) deve ser calculada **só com os dados de treino**. Calcular com todos os dados já é vazamento (seção 2.3).

### 2.2 Partição treino / validação / teste

**Intuição.** Cada pedaço dos dados tem uma função diferente.

**Analogia.** O aluno estuda com a lista de exercícios (**treino**), faz um simulado para ajustar o método de estudo (**validação**) e só faz a prova final uma vez (**teste**). Se ajustar o método olhando a prova final, a nota deixa de medir aprendizado.

**Formalização.** Uma divisão típica é 70/15/15 por cento, **estratificada** (cada partição preserva a proporção de classes). A **semente fixa** garante que a mesma divisão possa ser reproduzida.

**Exemplo.** Se a classe M é 3% dos dados, uma divisão aleatória simples pode deixar o teste com 1% ou 5% de M, o que torna as métricas instáveis. Estratificar corrige isso.

### 2.3 Vazamento de dados (*data leakage*)

**Intuição.** Vazamento é qualquer caminho pelo qual informação do teste (ou da resposta) entra no treino, inflando artificialmente o desempenho.

**Formas que importam neste projeto.**

- **Duplicatas entre partições:** a mesma estrela pode ter várias observações no LAMOST. Se uma cópia vai para o treino e outra para o teste, o modelo "reconhece" a estrela em vez de generalizar.
- **Pré-processamento global:** calcular médias, escalas ou imputações com todos os dados antes de dividir.
- **Feature que codifica o alvo:** usar uma coluna derivada, direta ou indiretamente, do mesmo processo que gerou o rótulo.
- **Vizinhança espacial:** estrelas muito próximas no céu e em distância compartilham propriedades (aglomerados). Dividir de forma aleatória espalha os parentes entre treino e teste.

**Armadilha.** O vazamento quase nunca dá erro: ele dá um resultado *bom demais*. Se o desempenho parece excelente na primeira tentativa, a primeira hipótese é vazamento, e não genialidade do modelo.

---

## 3. Baseline: o ponto de comparação

*Ligação com o projeto: Fases 04 e 05 (baseline antes dos modelos).*

**Intuição.** Um modelo só é bom em relação a alguma outra coisa. O *baseline* é a alternativa mais simples que alguém poderia usar.

**Exemplo numérico.** Se 60% das estrelas da amostra são K, um "modelo" que responde sempre "K" tem 60% de acurácia sem aprender nada. Um modelo de ML com 65% só ganhou 5 pontos sobre o trivial. Os baselines do ROADMAP são mais informativos: no Trilho A, a classe prevista por faixas de Teff; no Trilho B, um corte simples no plano νmax–Δν ou Teff–log g.

**Insight.** No Trilho A, como a classe é quase uma função monótona de Teff (arquivo 01, seção 8), o baseline é forte para anãs "bem comportadas". O ganho do ML deve aparecer onde a regra simples falha: estrelas avermelhadas, gigantes, estrelas perto das fronteiras entre classes.

**Armadilha.** Se o ML não supera o baseline com folga, essa também é uma conclusão científica legítima, e não um fracasso a esconder.

---

## 4. Árvores de decisão

*Ligação com o projeto: base do Random Forest e do XGBoost (Fases 04 e 05).*

**Intuição.** Uma árvore faz perguntas de sim/não sobre as features ("BP−RP < 1,0?") até chegar a um grupo de estrelas parecidas. Cada pergunta é escolhida para separar as classes da melhor forma possível.

**Analogia.** O jogo das vinte perguntas. A boa estratégia é fazer primeiro as perguntas que mais eliminam possibilidades.

**Formalização.** A "pureza" de um nó é medida pela **impureza de Gini** (ou pela entropia). Se $\large p_k$ é a fração de estrelas da classe $\large k$ no nó:

$$
\huge G = 1 - \sum_{k=1}^{K} p_k^2 \qquad\qquad H = -\sum_{k=1}^{K} p_k\log_2 p_k
$$

$\large G=0$ significa nó puro (todas da mesma classe). Para cada corte candidato, calcula-se o **ganho**: impureza do pai menos a média ponderada das impurezas dos filhos.

$$
\huge \Delta G = G_{\text{pai}} - \left(\frac{n_E}{n}\,G_E + \frac{n_D}{n}\,G_D\right)
$$

**Exemplo numérico.** Um nó com 100 estrelas, 50 G e 50 K: $\large G = 1-(0{,}5^2+0{,}5^2)=0{,}5$. Um corte em BP−RP gera:

- Esquerda: 50 estrelas, 40 G e 10 K, então $\large G_E = 1-(0{,}8^2+0{,}2^2)=0{,}32$.
- Direita: 50 estrelas, 10 G e 40 K, então $\large G_D = 0{,}32$.

O ganho é $\large 0{,}5-(0{,}5\cdot0{,}32+0{,}5\cdot0{,}32)=0{,}18$. A árvore testa todos os cortes em todas as features e escolhe o de maior ganho.

**Armadilha.** Uma árvore profunda separa perfeitamente o treino (cada folha com uma única estrela) e generaliza mal. Árvores individuais são **instáveis**: mudar poucos exemplos pode mudar a árvore inteira. Isso motiva as florestas.

---

## 5. Random Forest

*Ligação com o projeto: Fases 04 e 05.*

**Intuição.** Em vez de confiar numa árvore instável, treina-se centenas de árvores, cada uma vendo uma versão ligeiramente diferente dos dados, e elas **votam**. Os erros individuais tendem a se cancelar.

**Analogia.** A sabedoria das multidões: a média das estimativas de muitas pessoas independentes costuma ser melhor que a da maioria delas.

**Formalização.** Cada árvore é treinada numa amostra *bootstrap* (sorteio com reposição de $\large N$ exemplos) e, em cada corte, só considera um subconjunto aleatório das features. A classe final é o voto da maioria.

Por que funciona? Suponha $\large B$ árvores, cada uma com variância $\large \sigma^2$ e correlação média $\large \rho$ entre elas. A variância da média é

$$
\huge \operatorname{Var}\big(\bar f\big) = \rho\,\sigma^2 + \frac{1-\rho}{B}\,\sigma^2
$$

Com muitas árvores ($\large B\to\infty$) o segundo termo some, e o que sobra é $\large \rho\sigma^2$. Por isso o sorteio de features em cada corte importa: **reduz a correlação** $\large \rho$ entre árvores. Árvores diversas se cancelam mais.

**Exemplo numérico.** Se $\large \sigma^2=1$, $\large \rho=0{,}3$ e $\large B=100$: $\large \operatorname{Var}=0{,}3+0{,}007=0{,}307$. Se $\large \rho=0{,}9$ (árvores quase idênticas): $\large 0{,}9+0{,}001=0{,}901$. Mais árvores quase iguais quase não ajudam.

**Detalhe útil.** Em cada bootstrap, a fração de exemplos que *não* é sorteada tende a $\large (1-1/N)^N\to e^{-1}\approx 0{,}368$. Esses 37% ("fora da sacola", *out-of-bag*) servem como um conjunto de validação gratuito para cada árvore.

**Armadilha.** Floresta reduz **variância**, mas não corrige **viés**: se todas as árvores cometem o mesmo erro sistemático (por exemplo, por causa de um rótulo enviesado), a votação não conserta.

---

## 6. Gradient Boosting e XGBoost

*Ligação com o projeto: Fases 04 e 05.*

**Intuição.** A floresta treina árvores em paralelo e independentes. O *boosting* faz o oposto: treina árvores **em sequência**, e cada nova árvore tenta corrigir os erros das anteriores.

**Analogia.** Um jogador de golfe. A primeira tacada leva a bola perto do buraco, a segunda corrige o que faltou, a terceira ajusta o último pedaço. Cada tacada é pequena e focada no erro que sobrou.

**Formalização.** O modelo é uma soma de árvores $\large f_m$, cada uma escalada por uma taxa de aprendizado $\large \eta$ (pequena, para evitar saltos grandes):

$$
\huge F_m(\mathbf{x}) = F_{m-1}(\mathbf{x}) + \eta\, f_m(\mathbf{x})
$$

A nova árvore é ajustada ao **gradiente negativo da perda** em relação à predição atual. Para a perda quadrática, isso é exatamente o resíduo $\large y-F_{m-1}$ (daí o nome "gradient").

O XGBoost refina a ideia: otimiza uma função objetivo que inclui uma **penalização de complexidade** e usa aproximação de segunda ordem da perda:

$$
\huge \text{Obj} = \sum_i \mathcal{L}(y_i, \hat y_i) + \sum_t \Omega(f_t), \qquad \Omega(f) = \gamma\,T + \tfrac12\,\lambda\sum_{j=1}^{T} w_j^2
$$

Aqui $\large T$ é o número de folhas e $\large w_j$ o valor da folha $\large j$. Com $\large g_i$ e $\large h_i$ sendo a primeira e a segunda derivada da perda em cada estrela, e $\large G_j=\sum_{i\in j} g_i$, $\large H_j=\sum_{i\in j} h_i$, o valor ótimo de cada folha é

$$
\huge w_j^{*} = -\,\frac{G_j}{H_j+\lambda}
$$

E o ganho de um corte (comparado a não cortar) é

$$
\huge \text{Ganho} = \frac12\left[\frac{G_E^2}{H_E+\lambda}+\frac{G_D^2}{H_D+\lambda}-\frac{(G_E+G_D)^2}{H_E+H_D+\lambda}\right]-\gamma
$$

**Exemplo numérico.** Perda quadrática: $\large g_i=\hat y_i-y_i$ e $\large h_i=1$. Uma folha com três estrelas cujos resíduos ($\large y-\hat y$) são $\large +2,\,+1,\,+3$ tem $\large G=-6$ e $\large H=3$. Com $\large \lambda=1$:

$$
\huge w^{*} = -\frac{-6}{3+1} = 1{,}5
$$

O resíduo médio seria 2, mas a folha prediz 1,5: o termo $\large \lambda$ **encolhe** a correção. Isso é regularização, e protege contra seguir ruído. Se $\large \gamma$ for maior que o ganho de um corte, ele nem é feito (poda).

**Contraste com a floresta.** Floresta: muitas árvores profundas e diversas, reduz variância. Boosting: muitas árvores rasas e sequenciais, reduz viés. Costuma render mais acurácia, mas exige mais cuidado (taxa de aprendizado, número de árvores, regularização) e é mais propenso a overfitting se mal ajustado.

**Armadilha.** Classificação multiclasse no XGBoost usa a função softmax e treina uma árvore por classe a cada rodada. As probabilidades de saída tendem a ser mal calibradas: um "0,9" não é automaticamente 90% de acerto.

---

## 7. Desbalanceamento de classes

*Ligação com o projeto: Fase 04 (Balanced Random Forest) e `REFERENCIAS.md` (Sahlmann & Gómez).*

**Intuição.** Quando uma classe é muito mais rara que as outras, o modelo pode "ignorá-la" sem pagar quase nada na perda.

**Exemplo numérico (o paradoxo da acurácia).** Se 99% das estrelas são da classe A e 1% da classe B, um modelo que responde sempre A tem **99% de acurácia** e zero capacidade de achar B. No catálogo LAMOST, classes como O e B são raras em comparação com F, G e K, então esse risco é real.

**Formalização (Balanced Random Forest).** Em cada árvore, em vez de um bootstrap da amostra inteira, sorteia-se o mesmo número de exemplos de cada classe, por exemplo $\large n_{\min}$ da classe rara e $\large n_{\min}$ da classe comum (com subamostragem da maioria). Assim, cada árvore vê um problema balanceado, e a floresta ainda vê a maioria dos dados da classe comum ao longo das árvores. A alternativa é aplicar **pesos de classe** na perda, por exemplo $\large w_k\propto 1/N_k$.

**Armadilha.** Balancear muda as **probabilidades**: o modelo passa a super-representar a classe rara, e as probabilidades de saída já não refletem as frequências reais do céu. Para decidir "o quão provável é que esta estrela seja B", é preciso corrigir pelas proporções originais. Para apenas ranquear candidatos, geralmente não importa.

---

## 8. Métricas

*Ligação com o projeto: Fases 04 e 05 (macro-F1, matriz de confusão, curva PR por classe).*

### 8.1 Matriz de confusão

**Intuição.** Uma tabela $\large K\times K$ em que a linha é a classe verdadeira e a coluna a prevista. A diagonal são os acertos. Os erros fora da diagonal contam *como* o modelo erra, e não só *quanto*.

**Uso físico.** Esperamos que os erros se concentrem nas casas vizinhas (G confundida com K, e não com O). Se aparecerem erros "distantes", algo está errado com a física ou com os dados.

### 8.2 Precisão, recall e F1

**Para uma classe específica**, com $\large TP$ (verdadeiros positivos), $\large FP$ (falsos positivos) e $\large FN$ (falsos negativos):

$$
\huge P = \frac{TP}{TP+FP} \qquad\quad R = \frac{TP}{TP+FN} \qquad\quad F_1 = \frac{2PR}{P+R}
$$

**Precisão:** das que o modelo disse ser da classe, quantas realmente são. **Recall:** das que realmente são da classe, quantas o modelo achou. Em geral há um compromisso entre os dois.

**Analogia.** Um detector de metais na praia. Se for muito sensível, acha todas as moedas (recall alto), mas também apita para tampinhas (precisão baixa). Se for pouco sensível, só apita para moedas de verdade (precisão alta), mas deixa passar muitas (recall baixo).

**Exemplo numérico.** Uma classe tem 50 estrelas reais. O modelo prevê 40 como dessa classe, e 30 estão certas. $\large P=30/40=0{,}75$, $\large R=30/50=0{,}60$, e

$$
\huge F_1 = \frac{2\cdot0{,}75\cdot0{,}60}{0{,}75+0{,}60}\approx 0{,}667
$$

**Por que média harmônica?** Com $\large P=1{,}0$ e $\large R=0{,}1$, a média aritmética é 0,55, que soa razoável. O F1 é $\large 0{,}18$. A média harmônica é dominada pelo valor menor, então não permite compensar um desastre num lado com excelência no outro.

### 8.3 Macro-F1

$$
\huge \text{macro-}F_1 = \frac{1}{K}\sum_{k=1}^{K} F_{1,k}
$$

É a média simples dos F1 de cada classe, dando o **mesmo peso a classes raras e comuns**. A alternativa (média ponderada pelo tamanho das classes) deixa a classe dominante ditar o resultado e esconde falhas nas raras. Por isso o ROADMAP escolhe macro-F1.

### 8.4 Curva Precisão–Recall

**Intuição.** O modelo dá uma probabilidade para cada estrela. Variando o limiar de decisão (de "só aceito se for 0,99" até "aceito qualquer 0,01"), obtém-se um par (recall, precisão) para cada limiar. A curva resultante mostra todo o compromisso de uma vez.

**Por que PR e não ROC.** Para classes raras, a curva ROC pode parecer ótima mesmo com muitos falsos positivos, porque o número enorme de negativos verdadeiros "dilui" a taxa de falsos positivos. A curva PR olha só para o que o modelo chamou de positivo, e por isso é mais honesta. Uma referência útil: a precisão de um classificador aleatório numa curva PR é igual à **prevalência** da classe (se a classe é 1%, o chute vale 0,01).

### 8.5 Regressão (Trilho B, exercício opcional)

Para prever massa, a classificação dá lugar a métricas de erro numérico, como a raiz do erro quadrático médio e o coeficiente de determinação:

$$
\huge \text{RMSE}=\sqrt{\frac1N\sum_i (y_i-\hat y_i)^2} \qquad\quad R^2 = 1-\frac{\sum_i (y_i-\hat y_i)^2}{\sum_i (y_i-\bar y)^2}
$$

**Armadilha geral das métricas.** Um número só (macro-F1, por exemplo) esconde estrutura. Sempre olhe também a matriz de confusão e as curvas por classe.

---

## 9. Validação cruzada k-fold

*Ligação com o projeto: Fases 04 e 05, `REFERENCIAS.md`.*

**Intuição.** Uma única divisão treino/teste depende da sorte da divisão. A validação cruzada repete o processo $\large k$ vezes, cada vez deixando um pedaço diferente para teste, e faz a média.

**Formalização.** Divide-se o conjunto em $\large k$ partes (*folds*). Para $\large i=1,\dots,k$: treina-se com as outras $\large k-1$ partes e avalia-se na parte $\large i$.

$$
\huge \text{CV}_k = \frac1k\sum_{i=1}^{k} \text{Métrica}_i
$$

A variação entre as $\large k$ avaliações dá uma noção da estabilidade do modelo.

**Exemplo.** Com $\large k=5$ e macro-F1 de 0,71; 0,73; 0,70; 0,72; 0,74, a média é 0,72 e a dispersão é pequena (cerca de 0,015), indicando um resultado estável.

**Variantes que importam aqui.**

- **Estratificada:** preserva a proporção de classes em cada *fold*.
- **Agrupada:** garante que todas as observações da mesma estrela fiquem juntas no mesmo *fold* (evita o vazamento por duplicatas da seção 2.3).
- **Aninhada:** se hiperparâmetros são escolhidos pela validação cruzada, a avaliação final deve usar um laço externo separado, para não "sobrescrever" a prova.

**Armadilha.** A validação cruzada estima o desempenho para dados **da mesma distribuição** que a amostra. Não diz nada sobre como o modelo se comporta em outro levantamento, com outra seleção de estrelas. E a dispersão entre *folds* subestima a incerteza real, porque os *folds* compartilham dados de treino.

---

## 10. Interpretação com SHAP e confundidores

*Ligação com o projeto: Fase 04 (interpretação, investigação de confundidores) e `REFERENCIAS.md` (Sahlmann & Gómez).*

**Intuição.** Depois de treinar, queremos saber **por que** o modelo previu o que previu, e quais features pesam mais. O SHAP responde atribuindo a cada feature uma contribuição para cada previsão individual.

**Analogia.** Três sócios geram um lucro juntos. Como dividir o prêmio de forma justa? A ideia de Shapley: para cada sócio, calcule o quanto ele acrescenta ao lucro quando entra em cada ordem possível de chegada, e tire a média.

**Formalização (valores de Shapley).** Para uma feature $\large i$ num conjunto $\large N$ de $\large n$ features, com $\large v(S)$ sendo a previsão do modelo usando apenas o subconjunto $\large S$:

$$
\huge \phi_i = \sum_{S\subseteq N\setminus\{i\}} \frac{|S|!\,(n-|S|-1)!}{n!}\,\Big[v(S\cup\{i\}) - v(S)\Big]
$$

Propriedade central (**eficiência**): as contribuições somam a diferença entre a previsão e a média:

$$
\huge \sum_{i}\phi_i = f(\mathbf{x}) - E\big[f(\mathbf{X})\big]
$$

**Exemplo numérico (duas features).** Seja $\large v(\varnothing)=0$, $\large v(\{A\})=10$, $\large v(\{B\})=20$, $\large v(\{A,B\})=40$. Existem duas ordens de chegada, e cada uma pesa 1/2:

$$
\huge \phi_A=\tfrac12(10-0)+\tfrac12(40-20)=15 \qquad \phi_B=\tfrac12(20-0)+\tfrac12(40-10)=25
$$

$\large 15+25=40$, que é exatamente $\large v(\{A,B\})-v(\varnothing)$. ✓ O cálculo exato é exponencial no número de features; para árvores existe um algoritmo eficiente (*TreeSHAP*).

**O que a lição de Sahlmann & Gómez ensina.** No artigo, a paralaxe e a magnitude aparente apareciam como features importantes, mas por **viés de seleção** e não por física: as estrelas do conjunto de treino foram escolhidas por critérios que correlacionam com essas grandezas. O SHAP foi o que expôs o problema, e as features foram descartadas. Uma versão do mesmo risco neste projeto: se o LAMOST observa de preferência estrelas de certa faixa de brilho, a magnitude aparente $\large G$ pode "prever" a classe sem ter relação física com ela.

**Teste de bom senso.** Para o Trilho A, esperamos que as features mais importantes sejam as de cor (que codificam temperatura). Se $\large G$ ou $\large \varpi$ aparecerem no topo, isso é um alerta.

**Armadilha.** O SHAP explica **o modelo**, e não o mundo. Se duas features são muito correlacionadas (BP−RP e G−RP, por exemplo), o crédito é dividido entre elas de forma arbitrária, e nenhuma parece muito importante mesmo que juntas sejam essenciais. E uma feature "importante" para o modelo pode ser importante justamente por ser um atalho enviesado.

---

## 11. Limitações honestas

*Ligação com o projeto: Fase 04 (investigação de confundidores) e Fase 06.*

**Intuição.** Um modelo de ML é, no fundo, um interpolador sofisticado sobre os exemplos que viu. Isso traz consequências que o projeto deve declarar.

- **Só encontra "mais do mesmo":** estrelas diferentes do conjunto de treino (tipos raros, binárias, estrelas em regiões muito avermelhadas) estão fora do que o modelo conhece e tendem a ser classificadas mal. É a limitação discutida por Sahlmann & Gómez.
- **Rótulo ruidoso:** o limite de desempenho é imposto em parte pela qualidade do rótulo LAMOST (arquivo 01, seção 8). Dois classificadores excelentes podem discordar do rótulo no mesmo lugar, porque é o rótulo que erra.
- **Mudança de distribuição:** a amostra de treino (estrelas com espectro LAMOST e cortes de qualidade) não representa todas as estrelas do Gaia. Aplicar o modelo ao catálogo inteiro é extrapolar.
- **Circularidade possível:** o baseline com `teff_gspphot` e as features fotométricas compartilham a mesma fonte de informação (arquivo 01, seção 9).
- **Correlação não é causalidade:** que o modelo use uma feature não prova que ela é a causa física da classe.

**Armadilha final.** A pergunta correta ao ver um bom resultado não é "o modelo é bom?", e sim "**bom em quê, para quais estrelas, e comparado a quê?**". Um resultado de ML é uma afirmação sobre a amostra e a métrica escolhidas, e só vira afirmação sobre o céu com justificativa física.

---
