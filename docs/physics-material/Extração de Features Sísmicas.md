Este arquivo cobre o passo que os outros materiais assumem como feito: **como medir** $\large \nu_{\max}$, $\large \Delta\nu$ e $\large \Delta\Pi_1$ a partir do que o satélite entrega, uma série de brilho no tempo. O que essas grandezas *significam* (relações de escala, modos p e g, RGB vs RC) está em [[Asterossismologia___Interior_Estelar]]. Aqui o foco é a medição, o que pode dar errado nela e como o resultado entra na tabela de features do Trilho B.

Para evitar repetição, este arquivo **não rederiva**: $\large \Delta\nu\propto\sqrt{\bar\rho}$, as relações de escala para $\large M$ e $\large R$, o padrão assintótico $\large \nu_{n,\ell}\approx\Delta\nu(n+\ell/2+\varepsilon)$, a fórmula de $\large \Delta\Pi_\ell$, o diagrama Kiel e a lista de armadilhas do RGB vs RC. Quando precisar delas, ele aponta para lá. Métricas, validação e SHAP estão em [[ML_Math]]; a lógica de catálogos, cross-match e cortes de qualidade está em [[Física_Observacional]].

Constantes solares usadas nos exemplos (as mesmas do arquivo de asterossismologia): $\large \nu_{\max,\odot}\approx3090\ \mu\text{Hz}$, $\large \Delta\nu_\odot\approx135{,}1\ \mu\text{Hz}$.

---
## A cadeia de medição

**Intuição.** O satélite não mede frequências. Mede quantos fótons chegaram a cada intervalo de tempo. Todo o resto é processamento: transformar essa série em um espectro, separar o "ruído de fundo" físico dos modos, e só então ler os números que importam.

**Formalização.**

$$
\huge \underbrace{F(t_i)}_{\text{curva de luz}} \;\longrightarrow\; \underbrace{P(\nu)}_{\text{espectro}} \;\longrightarrow\; \underbrace{B(\nu)}_{\text{fundo}} \;\longrightarrow\; \underbrace{\nu_{\max}}_{\text{envelope}} \;\longrightarrow\; \underbrace{\Delta\nu,\ \varepsilon,\ \delta\nu_{02}}_{\text{modos p}} \;\longrightarrow\; \underbrace{\Delta\Pi_1}_{\text{modos mistos}}
$$

Cada seta tem custo: a ordem importa porque cada etapa usa a anterior como ponto de partida (o $\large \Delta\nu$ só é medido bem em torno do $\large \nu_{\max}$, por exemplo). E cada etapa exige mais da qualidade e da duração dos dados do que a anterior.

**Armadilha.** Erros nas primeiras etapas se propagam em silêncio. Um filtro agressivo demais na curva de luz não dá erro: ele só faz o $\large \nu_{\max}$ sair errado.

---
## A curva de luz como dado

**Intuição.** Cada missão tem uma cadência (de quanto em quanto tempo mede) e uma duração (por quanto tempo olha). Esses dois números decidem **quais estrelas podem ser estudadas**, antes de qualquer análise.

| Missão | Cadência típica | Duração por alvo | Estrelas onde funciona bem |
|---|---|---|---|
| CoRoT | 32 s e 512 s | 20 a 150 dias | Gigantes e algumas tipo solar |
| Kepler | 58,85 s (curta) e 29,4 min (longa) | até ~4 anos, campo fixo | Gigantes (longa); tipo solar (curta) |
| K2 | 29,4 min e 1 min | ~80 dias por campanha | Gigantes; poucos modos resolvidos |
| TESS | 20 s, 2 min e imagens completas (10 a 30 min, variou entre fases da missão) | 27 dias por setor, até ~1 ano nas regiões de visão contínua | Gigantes brilhantes |

**Formalização.** Duas fórmulas decidem tudo. A **frequência de Nyquist** é a maior frequência recuperável:

$$
\huge \nu_{\text{Nyq}}=\frac{1}{2\,\Delta t} \qquad\quad \delta\nu\sim\frac{1}{T}
$$

e a **resolução** $\large \delta\nu$ é o menor espaçamento que se distingue (já usada no arquivo de asterossismologia).

**Exemplo numérico.** Kepler em cadência longa, $\large \Delta t=1765{,}5$ s:

$$
\huge \nu_{\text{Nyq}}=\frac{1}{2\times1765{,}5\ \text{s}}\approx 283\ \mu\text{Hz}
$$

Uma gigante com $\large \nu_{\max}=35\ \mu\text{Hz}$ cabe com folga. O Sol, com $\large \nu_{\max}=3090\ \mu\text{Hz}$, não: exige cadência curta ($\large \Delta t=58{,}85$ s dá $\large \nu_{\text{Nyq}}\approx8500\ \mu\text{Hz}$). TESS em 2 min dá $\large \nu_{\text{Nyq}}\approx4170\ \mu\text{Hz}$.

Para a resolução: um setor do TESS ($\large T=27$ d) dá $\large \delta\nu\approx0{,}43\ \mu\text{Hz}$; quatro anos de Kepler dão $\large 0{,}008\ \mu\text{Hz}$, mais de 50 vezes melhor. A seção sobre modos mistos mostra por que isso pesa.

**Armadilha.** Estrelas observadas em cadência longa **com modos acima de Nyquist** produzem picos "refletidos" para dentro da faixa observada (*aliasing*). Um pico em $\large \nu$ pode ser real ou ser o reflexo de um pico em $\large 2\nu_{\text{Nyq}}-\nu$. Para gigantes isso raramente importa; para estrelas mais compactas, é um erro clássico.

---
## Do arquivo do satélite à série limpa

**Intuição.** O arquivo bruto mistura sinal estelar com a vida do satélite: o telescópio se desloca, a temperatura muda, o detector tem um "tranco" a cada reorientação. Limpar é remover o que é do instrumento sem tocar no que é da estrela.

**O que existe nos arquivos (MAST).**

- **Arquivos de pixels** (*target pixel files*): a imagem pequena em torno do alvo. Permitem refazer a fotometria, útil quando há vizinhas contaminando.
- **Curvas de luz prontas:** duas colunas de fluxo importam. `SAP_FLUX` é a soma simples dos pixels; `PDCSAP_FLUX` é a mesma série após correção de sistemáticos do instrumento. Para sismologia, normalmente se parte da `PDCSAP`.
- **Coluna `QUALITY`:** marca pontos ruins (manobras, raios cósmicos, saturação). Pontos marcados saem.

**Passos de limpeza e o porquê de cada um.**

1. **Normalizar por segmento** (cada *quarter* no Kepler, cada setor no TESS): dividir pela mediana do segmento e subtrair 1. Segmentos diferentes têm níveis de fluxo diferentes por razões instrumentais.
2. **Remover valores aberrantes** (por exemplo, *sigma clipping* a partir de ~4σ): um ponto absurdamente alto espalha potência em todas as frequências.
3. **Filtrar tendências lentas** (filtro passa-alta): remove derivas do instrumento. A janela do filtro deve ser **muito maior que o período dos modos**: para $\large \nu_{\max}=35\ \mu\text{Hz}$, o período é $\large 1/\nu\approx8$ h, então uma janela de vários dias preserva os modos. Uma janela de poucas horas apagaria o sinal.
4. **Lacunas:** manter os buracos como buracos, e evitar interpolar sobre eles sem cuidado. Usar o periodograma de **Lomb-Scargle**, que aceita amostragem irregular.
5. **Converter para ppm:** $\large F_{\text{ppm}}=(F/\tilde F-1)\times10^6$.

**Exemplo.** Se o filtro tem janela de 1 dia, ele suprime potência abaixo de frequências da ordem de $\large 1/(86400\ \text{s})\approx11{,}6\ \mu\text{Hz}$. Para $\large \nu_{\max}=35$ ainda funciona, mas para uma gigante com $\large \nu_{\max}=5\ \mu\text{Hz}$ o mesmo filtro **destruiria** o envelope.

**Armadilha.** As lacunas criam uma **função janela** espectral: um sinal perfeitamente periódico, observado com buracos regulares, aparece com "satélites" ao redor do pico verdadeiro. Em TESS, o buraco a cada órbita (~13,7 dias) é fonte clássica disso. Sempre olhar o espectro da janela (o periodograma de uma senoide artificial amostrada nos mesmos tempos) antes de acreditar num pico estreito.

---
## O espectro de potência e a PSD

**Intuição.** Decompor a curva de luz em "notas" e medir o volume de cada uma. A decisão técnica é *como normalizar o volume*, porque duas estrelas só são comparáveis se a escala for a mesma.

**Formalização.** O espectro de potência bruto foi definido no arquivo de asterossismologia. Para comparar estrelas e missões, usa-se a **densidade espectral de potência** (PSD), com unidade ppm²/μHz, normalizada de modo que a área sob a curva seja a variância da série (**teorema de Parseval**):

$$
\huge \int_0^{\nu_{\text{Nyq}}} \text{PSD}(\nu)\,d\nu=\sigma^2_{\text{série}}
$$

Para uma série uniforme de $\large N$ pontos com $\large \Delta t$ em segundos, a estimativa via transformada de Fourier discreta é $\large \text{PSD}_k=2\,\Delta t\,|X_k|^2/N$ (em ppm²/Hz; multiplicar por $\large 10^{-6}$ para ppm²/μHz).

**Por que a normalização importa.** Com PSD, a altura de um pico **não depende** da duração da observação nem da cadência: é uma propriedade da estrela. Num espectro não normalizado, observar por o dobro do tempo dobra a altura de picos de ruído e muda as comparações.

**Exemplo numérico (verificado em dados sintéticos).** Numa curva de luz sintética de $\large N=65536$ pontos (cadência longa do Kepler, ~3,7 anos), a variância da série foi 5838,7 ppm². A integral da PSD calculada pelas fórmulas acima deu 5838,7 ppm². O acordo exato confirma que a normalização e as unidades estão corretas.

**O ruído do espectro é enorme por natureza.** Se a série for puro ruído, a potência em cada frequência segue uma distribuição exponencial em torno do valor médio. Nessa distribuição o desvio padrão **é igual** à média. No experimento sintético, a razão desvio/média da potência normalizada, medida numa região só com ruído, foi 0,999.

Consequência prática: um ponto qualquer do espectro varia 100% em torno do valor "verdadeiro". Um pico aparentemente alto pode ser pura flutuação. A probabilidade de um ponto ultrapassar $\large s$ vezes a média é $\large e^{-s}$. Para exigir probabilidade de falso alarme de 1% entre $\large N_{\text{ind}}=1000$ pontos independentes:

$$
\huge s=\ln\!\left(\frac{N_{\text{ind}}}{0{,}01}\right)=\ln(10^{5})\approx11{,}5
$$

ou seja, um pico só é "significativo" se for ~11,5 vezes acima do fundo, e não 3 ou 4 vezes.

**Armadilha.** Confundir PSD com "potência por ponto" (como o `periodogram` padrão pode devolver, dependendo da normalização escolhida). Se um resultado depende da duração da série, a normalização está errada.

---
## O fundo: granulação e ruído

**Intuição.** Antes de encontrar os modos, é preciso saber o que **não** é modo. A superfície de uma estrela com envelope convectivo (arquivo de asterossismologia, seção de transporte de energia) ferve em células que surgem e desaparecem, a **granulação**, e isso produz uma variação de brilho de **banda larga**: potência que sobe para baixas frequências. Soma-se a isso o ruído fotônico do detector, que é plano (ruído branco).

**Analogia.** Medir o som de uma flauta numa sala com chiado de ar-condicionado e murmúrio de fundo. Antes de falar da nota da flauta, é preciso modelar o ruído da sala.

**Formalização.** O modelo padrão usa uma **componente de Harvey** para a granulação, um ruído branco $\large W$, a atenuação por amostragem finita $\large \eta^2$, e o envelope dos modos como uma gaussiana:

$$
\huge B(\nu)=\eta^2(\nu)\left[\frac{2\sqrt2}{\pi}\frac{a^2}{b}\frac{1}{1+(\nu/b)^4}+H_{\text{env}}\,e^{-(\nu-\nu_{\max})^2/(2\sigma_{\text{env}}^2)}\right]+W
$$

$$
\huge \eta^2(\nu)=\operatorname{sinc}^2\!\left(\frac{\pi\,\nu}{2\,\nu_{\text{Nyq}}}\right)
$$

Aqui $\large a$ (em ppm) é a amplitude da granulação e $\large b$ (em μHz) a frequência característica. Com essa normalização, a integral da componente de Harvey de 0 a infinito é exatamente $\large a^2$, a contribuição da granulação para a variância, o que dá um significado direto ao parâmetro. Em dados reais costuma-se somar duas ou três componentes de Harvey (granulação e atividade em escalas diferentes); usamos uma para ilustrar.

O fator $\large \eta^2$ existe porque cada ponto da curva de luz é uma **média** sobre o tempo de exposição, o que atenua as altas frequências. Na frequência de Nyquist, $\large \eta^2=(2/\pi)^2\approx0{,}405$: perde-se quase 60% da potência.

**Como ajustar.** A estatística do ruído (exponencial, acima) dá a **verossimilhança correta** em cada ponto do espectro. O ajuste por máxima verossimilhança minimiza

$$
\huge -\ln\mathcal L=\sum_i\left[\ln B(\nu_i)+\frac{P_i}{B(\nu_i)}\right]
$$

**Não** se deve ajustar por mínimos quadrados comuns: o ruído é multiplicativo (proporcional ao modelo) e o ajuste ficaria enviesado.

**Exemplo numérico (experimento sintético).** Parâmetros verdadeiros: $\large a=60$ ppm, $\large b=45\ \mu\text{Hz}$, $\large W=5\ \text{ppm}^2/\mu\text{Hz}$. Recuperados: $\large a=59{,}9$, $\large b=44{,}9$, $\large W=5{,}04$.

**Armadilha.** Esse modelo é uma **parametrização**, e não a física completa: componentes de Harvey adicionais, a forma do envelope e o expoente de 4 no denominador são escolhas que mudam levemente o $\large \nu_{\max}$. Dois métodos bons podem dar valores diferentes por alguns por cento (ver o experimento).

---
## Extraindo $\large \nu_{\max}$

**Intuição.** Depois de subtrair o fundo, o que sobra acima dele é uma corcunda de potência dos modos. $\large \nu_{\max}$ é o centro dessa corcunda.

**Dois métodos comuns.**

1. **Ajuste gaussiano durante o ajuste do fundo:** o parâmetro $\large \nu_{\max}$ do modelo acima é o próprio resultado. Ajusta tudo junto, o que acopla fundo e envelope de forma consistente.
2. **Suavização do espectro dividido pelo fundo:** divide-se $\large P(\nu)$ pelo fundo (sem o envelope), convolui-se com uma gaussiana larga, e toma-se o máximo. A largura da gaussiana deve ser da ordem de $\large 2\Delta\nu$: estreita demais e a suavização segue o ruído; larga demais e apaga a corcunda.

**Quanto vale a largura do envelope.** Empiricamente, a largura a meia altura do envelope cresce com $\large \nu_{\max}$ aproximadamente como $\large 0{,}66\,\nu_{\max}^{0{,}88}$ (Mosser et al. 2012, conferir). Para $\large \nu_{\max}=35$ dá ~15 μHz, em torno de 4 ordens radiais. Essa janela é útil como região de análise na etapa seguinte.

**Exemplo numérico (experimento sintético, $\large \nu_{\max}$ verdadeiro = 35 μHz).**

| Método | $\large \nu_{\max}$ recuperado |
|---|---|
| Ajuste gaussiano junto com o fundo | 35,03 μHz |
| Suavização do espectro dividido pelo fundo | 36,22 μHz |

Diferença de 3,4% entre dois métodos razoáveis, na mesma série. Essa é a **incerteza sistemática de método**, e é maior que a incerteza estatística (próxima seção).

**Uma relação útil como prior.** Entre as gigantes, $\large \Delta\nu$ e $\large \nu_{\max}$ andam juntos: $\large \Delta\nu\approx0{,}263\,\nu_{\max}^{0{,}772}$ (Stello et al. 2009, conferir). Para $\large \nu_{\max}=35$ dá 4,1 μHz. Serve para saber onde procurar $\large \Delta\nu$ e para sinalizar medidas absurdas.

**Armadilha.** Uma gigante com $\large \nu_{\max}$ **baixo** (poucos μHz) tem poucos modos dentro do envelope e períodos longos: a série precisa cobrir muitas oscilações. O caso oposto também morde: com $\large \nu_{\max}$ perto de Nyquist, o envelope é cortado e o máximo fica enviesado.

---
## Extraindo $\large \Delta\nu$

**Intuição.** Dentro do envelope, os modos formam um "pente" de picos igualmente espaçados. Medir $\large \Delta\nu$ é achar o espaçamento do pente. Como o espectro é ruidoso demais para ler picos a olho, usa-se uma técnica que procura **periodicidade no próprio espectro**.

**Formalização (autocorrelação).** Depois de dividir o espectro pelo fundo, define-se a razão sinal-ruído $\large s(\nu)=P(\nu)/B_{\text{fundo}}(\nu)$ na janela em torno de $\large \nu_{\max}$. A autocorrelação é

$$
\huge C(\tau)=\sum_\nu\big[s(\nu)-\bar s\big]\big[s(\nu+\tau)-\bar s\big]
$$

Se os picos se repetem a cada $\large \Delta\nu$, então $\large C(\tau)$ tem um máximo em $\large \tau=\Delta\nu$. Também pode aparecer um máximo em $\large \Delta\nu/2$, porque os modos $\large \ell=1$ ficam no meio do espaço entre os $\large \ell=0$ (relação assintótica do arquivo de asterossismologia). Por isso a busca é restrita a uma faixa em torno do valor esperado (o prior da seção anterior).

**Variante: espectro do espectro.** A transformada de Fourier do próprio espectro (na janela do envelope) tem um pico na "quefrência" $\large 1/\Delta\nu$ (ou $\large 2/\Delta\nu$ pelo mesmo motivo). Dá resultado equivalente e é outra forma de checagem cruzada.

**Verificação visual: diagrama échelle.** Cortar o espectro em tiras de comprimento $\large \Delta\nu$ e empilhá-las, de forma que o eixo horizontal seja $\large \nu\bmod\Delta\nu$ e o vertical seja $\large \nu$. Se $\large \Delta\nu$ está certo, os modos de mesmo grau $\large \ell$ formam **colunas verticais**. Se está errado, as colunas ficam inclinadas (para $\large \Delta\nu$ ligeiramente pequeno demais, inclinam num sentido; para grande demais, no outro). É a melhor checagem de bom senso do pipeline inteiro.

![[echelle_exemplo.png]]

*Diagrama échelle da estrela sintética do experimento (a figura repete o painel duas vezes na horizontal, convenção usual). Com $\large \Delta\nu=4{,}0\ \mu$Hz, as colunas verticais aparecem em $\large \nu\bmod\Delta\nu\approx1{,}6\ \mu$Hz ($\large \ell=1$, a mais forte), $\large \approx3{,}6\ \mu$Hz ($\large \ell=0$) e $\large \approx3{,}1\ \mu$Hz ($\large \ell=2$, mais fraca), exatamente onde o padrão assintótico com $\large \varepsilon=0{,}9$ e $\large \delta\nu_{02}=0{,}48\ \mu$Hz prevê. Colunas retas confirmam que o $\large \Delta\nu$ está correto.*

**Exemplo numérico (experimento sintético, $\large \Delta\nu$ verdadeiro = 4,0 μHz).** Usando como janela o intervalo $\large \nu_{\max}\pm$ largura do envelope, e restringindo a busca a $\large \pm30\%$ do prior (4,1 μHz), a autocorrelação deu $\large \Delta\nu=3{,}993\ \mu$Hz. Erro de 0,2%.

**Armadilha.** Qualquer periodicidade espectral produz pico na autocorrelação. Em dados reais, a função janela com lacunas (seção da curva de luz) introduz periodicidades falsas, e o ruído também. Por isso: (1) restringir a faixa de busca, (2) confirmar no diagrama échelle, (3) não aceitar o primeiro pico sem checar $\large \Delta\nu/2$ e $\large 2\Delta\nu$.

---
## O padrão fino: $\large \varepsilon$, $\large \delta\nu_{02}$ e modos individuais

**Intuição.** $\large \nu_{\max}$ e $\large \Delta\nu$ são médias sobre muitos modos. Medir as frequências **individuais** dá informação mais fina (e mais frágil), porque a estrela vira a vários números em vez de dois.

**O que sai do padrão assintótico** (fórmula no arquivo de asterossismologia, seção "Modos p e g"):

- **$\large \varepsilon$ (deslocamento):** colocando as frequências dos modos radiais $\large \ell=0$ contra o índice $\large n$, o gráfico é aproximadamente uma reta $\large \nu_{n,0}=\Delta\nu(n+\varepsilon)$. A inclinação é $\large \Delta\nu$ e o intercepto é $\large \Delta\nu\cdot\varepsilon$. Sinaliza efeitos das camadas externas e tem sido usado como diagnóstico auxiliar de estágio evolutivo.
- **$\large \delta\nu_{02}$ (pequena separação):** diferença entre um modo $\large \ell=0$ e o modo $\large \ell=2$ da ordem anterior, $\large \delta\nu_{02}=\nu_{n,0}-\nu_{n-1,2}$. Em geral é uma fração de $\large \Delta\nu$ (da ordem de 10%), e é mais sensível à estrutura profunda.

**Exemplo.** Com $\large \Delta\nu=4{,}0$ e $\large \varepsilon=0{,}9$ (valores do experimento), o modo radial de ordem $\large n=8$ fica em $\large 4{,}0\times8{,}9=35{,}6\ \mu$Hz, e o $\large \ell=2$ vizinho cerca de $\large 0{,}48\ \mu$Hz abaixo (usando $\large \delta\nu_{02}=0{,}12\Delta\nu$).

**Perfil de cada modo.** Um modo excitado estocasticamente e amortecido tem perfil **lorentziano**:

$$
\huge P_{\text{modo}}(\nu)=\frac{H}{1+\left[\dfrac{2(\nu-\nu_0)}{\Gamma}\right]^2}
$$

onde $\large \nu_0$ é a frequência, $\large H$ a altura e $\large \Gamma$ a largura a meia altura. A largura mede o **tempo de vida** do modo: $\large \tau=1/(\pi\Gamma)$.

**Exemplo numérico.** Com $\large \Gamma=0{,}15\ \mu$Hz, $\large \tau=1/(\pi\cdot0{,}15\times10^{-6}\ \text{Hz})\approx2{,}1\times10^6$ s, cerca de 25 dias. Um modo "vive" tipicamente semanas, o que é comparável a um setor do TESS (27 dias, $\large \delta\nu=0{,}43\ \mu$Hz): com resolução pior que a largura, o pico aparece **sem perfil lorentziano resolvido**, e a medida de $\large \Gamma$ fica impossível nesse caso.

**Procedimento para frequências individuais.** (1) dividir pelo fundo, (2) usar $\large \Delta\nu$ e $\large \varepsilon$ para saber onde esperar cada $\large \ell$, (3) testar cada pico contra a hipótese de ruído (limiar de falso alarme da seção da PSD), (4) ajustar lorentzianas por máxima verossimilhança.

**Armadilha.** Em estrelas de baixo sinal-ruído, a atribuição de $\large (n,\ell)$ pode estar errada, e uma frequência individual errada piora o ajuste de modelo em vez de melhorar. Para o escopo do projeto (3 meses), dois números por estrela ($\large \nu_{\max}$, $\large \Delta\nu$) já são o essencial; frequências individuais são uma extensão, e não um requisito.

---
## Modos mistos e $\large \Delta\Pi_1$: o que a duração dos dados permite

**Intuição.** O arquivo de asterossismologia mostrou que $\large \Delta\Pi_1$ separa RGB de RC e que ele **não está** na lista de features do ROADMAP. Medi-lo é bem mais difícil que medir $\large \Delta\nu$, e a razão é a **resolução em frequência**.

**Formalização.** Modos de gravidade têm espaçamento regular em **período**. Em frequência, perto de $\large \nu$, o espaçamento correspondente é

$$
\huge \delta\nu_g\approx\nu^2\,\Delta\Pi_1
$$

e o número de modos mistos entre dois modos radiais consecutivos é

$$
\huge N_g\approx\frac{\Delta\nu}{\nu^2\,\Delta\Pi_1}
$$

(válido para modos dominados por gravidade; o espaçamento real dos modos mistos varia, mas isso dá a ordem de grandeza).

**Exemplo numérico.** Para $\large \nu=35\ \mu\text{Hz}$ e $\large \Delta\Pi_1\approx80$ s (RGB):

$$
\huge \delta\nu_g\approx(35\times10^{-6})^2\times80\approx1\times10^{-7}\ \text{Hz}=0{,}098\ \mu\text{Hz} \qquad N_g\approx\frac{4{,}0}{0{,}098}\approx41
$$

Para $\large \Delta\Pi_1\approx300$ s (RC): $\large \delta\nu_g\approx0{,}37\ \mu$Hz e $\large N_g\approx11$.

Comparar com a resolução $\large \delta\nu\sim1/T$ (seção da curva de luz):

| Duração | $\large 1/T$ | Resolve RGB (0,098 μHz)? | Resolve RC (0,37 μHz)? |
|---|---|---|---|
| 1 setor TESS (27 d) | 0,43 μHz | não | não |
| ~1 ano (TESS, visão contínua) | 0,032 μHz | sim | sim |
| 4 anos (Kepler) | 0,008 μHz | sim | sim |

Ou seja: com um único setor do TESS **não dá** para medir $\large \Delta\Pi_1$, mesmo para gigantes brilhantes.

**Como medir.** O método usual constrói um diagrama análogo ao échelle, mas em **período**: toma os períodos $\large 1/\nu$ dos modos $\large \ell=1$ e os dobra módulo $\large \Delta\Pi_1$. Quando o valor está certo, os modos g-dominantes alinham-se em colunas. Como o acoplamento com os modos p distorce o padrão, os métodos publicados usam uma coordenada de período "esticada" que compensa o acoplamento (Mosser et al., conferir). Reimplementar isso é um projeto por si só.

**O que isso muda para o projeto.** Três caminhos, em ordem crescente de esforço:

1. **Usar $\large \Delta\Pi_1$ de um catálogo publicado** (para estrelas do Kepler existem tabelas de $\large \Delta\Pi_1$ e de estágio evolutivo), sem medir. Mantém o foco do projeto em $\large \nu_{\max}$ e $\large \Delta\nu$.
2. **Não usar $\large \Delta\Pi_1$ como feature** quando o rótulo de estágio vem dele. É o aviso do arquivo de asterossismologia ("Ponto de atenção para a Fase 05"): incluí-lo é vazamento e transforma o problema em trivial.
3. **Medir $\large \Delta\Pi_1$ você mesmo**, só se houver tempo e série longa, e então tratá-lo como produto à parte, e não como feature do classificador.

**Armadilha.** Estimar $\large \Delta\Pi_1$ em série curta pode dar um número com cara de resultado, mas que reflete a janela espectral e não a estrela. A verificação mínima é a tabela acima: se $\large 1/T$ não é bem menor que $\large \delta\nu_g$, a medida não é confiável.

---
## Experimento sintético: o pipeline de ponta a ponta

**O que foi feito.** Para testar as etapas deste arquivo sem depender de dados reais, foi gerada uma curva de luz sintética de uma gigante do tipo clump, com verdade conhecida, e o pipeline (PSD, ajuste de fundo, $\large \nu_{\max}$, $\large \Delta\nu$) foi aplicado.

**Estrela sintética.** $\large \nu_{\max}=35\ \mu$Hz, $\large \Delta\nu=4{,}0\ \mu$Hz, $\large \varepsilon=0{,}9$, largura de modo $\large \Gamma=0{,}15\ \mu$Hz, granulação $\large a=60$ ppm e $\large b=45\ \mu$Hz, ruído branco $\large W=5\ \text{ppm}^2/\mu$Hz. Série uniforme de 65 536 pontos na cadência longa do Kepler. A série é gerada sorteando o espectro em torno do modelo (distribuição exponencial) e invertendo a transformada.

**Resultado de uma realização.**

| Grandeza | Verdade | Recuperado |
|---|---|---|
| $\large \nu_{\max}$ (ajuste gaussiano) | 35,0 μHz | 35,03 μHz |
| $\large \nu_{\max}$ (suavização) | 35,0 μHz | 36,22 μHz |
| $\large \Delta\nu$ (autocorrelação) | 4,00 μHz | 3,993 μHz |

**Dispersão em 20 realizações independentes** (mesma estrela, ruído diferente): $\large \nu_{\max}=35{,}15\pm0{,}37\ \mu$Hz (~1,1%) e $\large \Delta\nu=3{,}997\pm0{,}019\ \mu$Hz (~0,5%).

**Como ler esses números.** São **otimistas**. O experimento não tem lacunas, nem modos mistos, nem ruído não estacionário, nem contaminação de vizinhas, e o modelo usado para gerar os dados é o mesmo usado para ajustá-los. Em dados reais, espere incertezas maiores e sistemáticos de método da ordem do que a tabela de $\large \nu_{\max}$ mostrou (3%). O valor do experimento é outro: mostra que **as fórmulas e as unidades deste arquivo estão consistentes**, e fornece um caso de teste com resposta conhecida para validar qualquer implementação do projeto antes de usá-la com dados reais.

**Núcleo do código testado** (apenas `numpy` e `scipy`; adapte `dt` e a faixa de frequência à missão):

```python
import numpy as np
from scipy.optimize import minimize

def psd(x, dt):
    """PSD em ppm²/µHz de uma série uniforme x (ppm), passo dt (s)."""
    N = len(x)
    X = np.fft.rfft(x - x.mean())
    nu = np.fft.rfftfreq(N, dt) * 1e6                  # µHz
    return nu, 2 * dt * np.abs(X) ** 2 / N * 1e-6      # Parseval: sum(P)*dnu = var(x)

def modelo_fundo(th, nu, nu_nyq):
    la, lb, lW, lH, numax, lsig = th
    a, b, W, H, sig = np.exp([la, lb, lW, lH, lsig])
    eta2 = np.sinc(nu / (2 * nu_nyq)) ** 2             # np.sinc(x) = sin(pi x)/(pi x)
    harvey = (2 * np.sqrt(2) / np.pi) * a**2 / b / (1 + (nu / b) ** 4)
    return eta2 * (harvey + H * np.exp(-(nu - numax) ** 2 / (2 * sig**2))) + W

def ajusta_fundo(nu, P, nu_nyq, x0):
    m = (nu > 1) & (nu < nu_nyq)
    nll = lambda th: np.sum(np.log(modelo_fundo(th, nu[m], nu_nyq))
                            + P[m] / modelo_fundo(th, nu[m], nu_nyq))  # χ² com 2 gl.
    return minimize(nll, x0, method="Nelder-Mead",
                    options=dict(maxiter=4000, xatol=1e-3, fatol=1e-3)).x

def dnu_acf(nu, snr, numax, largura_env):
    """snr = P / fundo (sem envelope). Busca o pico da ACF perto do prior."""
    m = (nu > numax - largura_env) & (nu < numax + largura_env)
    s = snr[m] - snr[m].mean()
    d_nu = nu[1] - nu[0]
    lags = np.arange(1, int(12 / d_nu))
    acf = np.array([np.sum(s[:-l] * s[l:]) for l in lags]) / len(s)
    tau = lags * d_nu
    acf = np.convolve(acf, np.ones(5) / 5, mode="same")
    prior = 0.263 * numax**0.772
    faixa = (tau > 0.7 * prior) & (tau < 1.3 * prior)
    return tau[np.argmax(np.where(faixa, acf, -np.inf))]
```

Com dados reais, a leitura e a limpeza costumam ser feitas pelo `lightkurve` (`search_lightcurve`, `download_all`, `stitch`, `remove_nans`, `remove_outliers`); esse trecho **não foi executado** aqui, por falta de acesso ao MAST neste ambiente. Em séries com lacunas, o periodograma de Lomb-Scargle substitui o `rfft`.

---
## Incertezas, detecção e qualidade

**Intuição.** Nem toda estrela tem oscilação detectável, e nem toda medida tem a mesma confiança. Uma tabela de features que mistura os dois casos sem marcar a diferença contamina o classificador.

**Três perguntas, nesta ordem.**

1. **Detectou?** O envelope está significativamente acima do fundo? Critério: altura do envelope em relação ao fundo no mesmo $\large \nu_{\max}$, e o limiar de falso alarme da seção da PSD. Registrar como coluna booleana.
2. **Qual a incerteza estatística?** Obtida de repetição (por exemplo, simulações como a do experimento, ou reamostragem) ou da posterior de uma amostragem bayesiana (MCMC), em vez de uma fórmula única.
3. **Qual a incerteza de método?** Rodar dois métodos independentes (ajuste e suavização, por exemplo) e registrar a diferença. No experimento, 3,4% em $\large \nu_{\max}$ contra 1,1% estatístico.

**Equivalente aos cortes de qualidade do Trilho A.** O arquivo de asterossismologia diz que o corte de qualidade sísmica é o equivalente do `parallax_over_error`. Concretamente: manter só estrelas com detecção confirmada, incerteza relativa menor que um limite (por exemplo 5% em $\large \nu_{\max}$ e 2% em $\large \Delta\nu$, valores a decidir e justificar) e concordância razoável com o prior $\large \Delta\nu$–$\large \nu_{\max}$.

**Armadilha.** Como no Trilho A (arquivo de Física Observacional, seção de qualidade), **o corte muda a amostra**. Exigir detecção forte privilegia estrelas brilhantes e de baixa gravidade (amplitude maior e S/N maior); o modelo final só vale para o tipo de estrela que sobreviveu. Documentar o corte é parte do resultado.

---
## Da curva de luz à tabela de features

**Intuição.** O produto final do pipeline é uma tabela com **uma linha por estrela** e colunas que o classificador do Trilho B consome. Tudo o que foi feito acima existe para preencher essa tabela com valores confiáveis.

**Colunas sugeridas.**

| Coluna | Origem | Observação |
|---|---|---|
| `id_estrela`, `id_gaia` | Cadastro | Chave única; ver cross-match abaixo |
| `missao`, `cadencia_s`, `duracao_d`, `duty_cycle` | Metadados da série | Decidem o que é mensurável |
| `numax`, `numax_err_stat`, `numax_err_met` | Este arquivo | μHz; as duas incertezas separadas |
| `dnu`, `dnu_err_stat`, `dnu_err_met` | Este arquivo | μHz |
| `detectou` | Teste de falso alarme | Booleano |
| `teff`, `feh` | Catálogo espectroscópico | Vem de fora (não da curva de luz) |
| `dPi1` | Catálogo publicado | **Só se não for a origem do rótulo** |

**Cross-match entre catálogos.** Os identificadores do satélite (KIC, EPIC, TIC) precisam ser ligados ao Gaia DR3 e aos catálogos espectroscópicos. O problema físico é o mesmo do cross-match LAMOST↔Gaia (arquivo de Física Observacional): **a época das posições é diferente** (Gaia é dado em 2016,0), então estrelas de alto movimento próprio podem falhar no pareamento se o raio de busca for pequeno. Existem tabelas de correspondência prontas para o campo do Kepler, mas conferir a versão e o critério de pareamento antes de usar.

**Duplicatas e validação.** Uma estrela observada em vários *quarters*, setores ou cadências **continua sendo uma estrela**: combinar as séries em uma única linha, ou, se mantiver várias, usar validação cruzada **agrupada por estrela** (arquivo de ML_Math, seção de validação cruzada). Caso contrário, o vazamento por duplicatas dá resultados inflados.

---
## Efeitos de seleção e circularidade para o ML

**Intuição.** O que entra na tabela não é uma amostra aleatória de estrelas. Os mecanismos abaixo moldam a amostra antes de qualquer modelo.

- **Detectabilidade.** A amplitude dos modos depende de luminosidade e massa; estrelas mais quentes e menos evoluídas oscilam com amplitude menor, e a atividade magnética pode **suprimir** os modos. Só entram na tabela estrelas cujas oscilações foram detectadas, o que enviesa a amostra para certos estados evolutivos e níveis de atividade.
- **Campo e brilho.** O Kepler olhou um campo fixo com limite de brilho; o TESS, estrelas brilhantes de todo o céu. As distribuições de magnitude, e portanto de distância e de população estelar (disco fino, disco espesso), diferem entre as duas amostras.
- **Circularidade.** Massas e raios publicados (por exemplo, no APOKASC, como o arquivo de asterossismologia já alerta) saem das **mesmas** relações de escala, com correções. Prever massa a partir de $\large \nu_{\max}$, $\large \Delta\nu$ e $\large T_{\text{eff}}$ reaprende a fórmula.
- **Rótulo de estágio.** Se o rótulo RGB/RC saiu de $\large \Delta\Pi_1$, essa feature não pode entrar (seção anterior).

**Conexão com SHAP.** A lição de Sahlmann & Gómez ([[ML_Math]], seção de interpretação) vale aqui: se `magnitude` ou `id` de missão aparecerem no topo da importância, é sinal de seleção e não de física. Para o Trilho B, as features esperadas no topo são $\large \nu_{\max}$, $\large \Delta\nu$ e $\large T_{\text{eff}}$.

**Armadilha.** Um bom resultado no Kepler **não** garante o mesmo no TESS: o ruído, a duração e a seleção mudam, e o modelo treinado numa missão extrapola na outra. Declarar a missão de origem como parte da afirmação científica.

---
## Ferramentas e por onde começar

| Ferramenta | Uso |
|---|---|
| `lightkurve` | Download do MAST, limpeza, periodograma, utilidades de sismologia |
| `astropy` (`LombScargle`) | Periodograma para séries com lacunas; consultas a catálogos via `astroquery` |
| `pySYD` | Extração automatizada de $\large \nu_{\max}$ e $\large \Delta\nu$ (método SYD), útil como **referência independente** |
| `PBjam` | Ajuste bayesiano de frequências individuais com prior do diagrama échelle |
| `emcee`, `dynesty` | Amostragem bayesiana de posteriores |

**Roteiro mínimo sugerido.**

1. Reproduzir o experimento sintético deste arquivo e conferir os números da tabela de resultados.
2. Escolher 3 a 5 gigantes do Kepler com $\large \nu_{\max}$ e $\large \Delta\nu$ publicados, rodar o pipeline e comparar. Esperar discrepâncias da ordem de poucos por cento; uma diferença de dezenas de por cento indica bug.
3. Rodar o `pySYD` nas mesmas estrelas e comparar com o pipeline próprio (a concordância entre os dois é um teste mais forte que a comparação com um só).
4. Escalar para uma amostra, aplicar o corte de qualidade da seção anterior e montar a tabela de features.
5. Só então passar ao classificador ([[ML_Math]]).

**Decisão aberta.** Se o projeto vai **medir** $\large \nu_{\max}$ e $\large \Delta\nu$ ou **usá-los de catálogo**. Medir ensina o pipeline e dá incertezas próprias, mas custa semanas; usar catálogo é rápido e aceita as incertezas e o método do autor. Uma combinação razoável é medir numa subamostra pequena, para validar, e usar o catálogo no restante.

---
## Referências

Conferir as citações antes de usar em texto formal (foram lembradas de memória, sem consulta direta nesta sessão).

- Kjeldsen & Bedding (1995), relações de escala; Brown et al. (1991), origem da relação de $\large \nu_{\max}$.
- Stello et al. (2009), relação empírica entre $\large \Delta\nu$ e $\large \nu_{\max}$.
- Huber et al. (2009), método SYD de extração automatizada; Huber et al. (2011), medidas em amostra do Kepler.
- Mosser et al. (2012), parâmetros sísmicos globais e largura do envelope; e trabalhos subsequentes do mesmo grupo sobre modos mistos e espaçamento de períodos.
- Kallinger et al. (2014), modelagem do fundo de granulação.
- Bedding et al. (2011), separação de RGB e RC pelo espaçamento de períodos.
- Chaplin & Miglio (2013), revisão sobre asterossismologia de estrelas tipo solar e gigantes vermelhas; Hekker & Christensen-Dalsgaard (2017), revisão sobre sismologia de gigantes.
- Chontos et al. (2022), `pySYD`; Lightkurve Collaboration (2018).