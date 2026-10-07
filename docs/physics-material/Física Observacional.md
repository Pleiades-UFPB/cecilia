
Este arquivo parte de um ponto de luz no céu e chega às propriedades físicas de uma estrela. É a base para entender o que o `cecilia` chama de "dado", "rótulo" e "feature", principalmente no Trilho A (classificação espectral).

---
## A ideia central

**Intuição.** Uma estrela é, em boa aproximação, uma esfera de gás quente que irradia. O que vemos da Terra é só o brilho em algumas faixas de cor. O projeto aposta que esse pouco de informação (cores e brilho) carrega o suficiente para dizer que tipo de estrela é.

**Analogia.** Um ferreiro olha a cor de uma peça no fogo e sabe a temperatura sem termômetro. Vermelho escuro é mais frio, laranja é mais quente, branco-azulado é mais quente ainda. Nós fazemos o mesmo com estrelas, só que com números.

**O pano de fundo histórico.** Cecilia Payne (1925) mostrou que a sequência de classes espectrais (O, B, A, F, G, K, M) é, antes de tudo, uma **sequência de temperatura**, e não de composição química. Usou a física atômica da equação de *Saha* para provar isso: 

$$
\huge \frac{n_{i+1}\,n_e}{n_i} = \frac{2\,g_{i+1}}{g_i}\left(\frac{2\pi m_e k_B T}{h^2}\right)^{3/2} e^{-\chi_i/(k_B T)}
$$

Aqui $\large n_i$ e $\large n_{i+1}$ são as densidades de átomos com $\large i$ e $\large i+1$ elétrons removidos, $\large n_e$ é a densidade de elétrons livres, $\large g$ são os pesos estatísticos, $\large \chi_i$ é a energia de ionização e $\large T$ é a temperatura.

A equação de *Saha* diz qual fração dos átomos está ionizada a uma dada temperatura. Em baixa $\large T$ o fator exponencial é minúsculo e quase tudo fica neutro. Em alta $\large T$ a ionização domina. Combinada com a distribuição de *Boltzmann*, que diz quantos átomos neutros estão em cada nível de excitação, ela prevê quando uma linha espectral é mais forte. 

Isso resolve o problema central. Se a composição química fosse a mesma em todas as estrelas, o que mudaria de uma classe para outra seria apenas a temperatura, e a temperatura sozinha já bastaria para mudar quais linhas aparecem. 

Tome as linhas de Balmer do hidrogênio, que exigem átomos neutros com o elétron já no segundo nível de energia. Numa estrela fria (classe M), quase todo o hidrogênio está no nível fundamental, e as linhas ficam fracas. Numa estrela muito quente (classe O), o hidrogênio está quase todo ionizado, e as linhas também ficam fracas. As linhas são mais fortes em temperaturas intermediárias, por volta de $\large 10^4$ K (classe A). 

O mesmo raciocínio vale para cada elemento, cada um com seu pico de temperatura. Estrelas de classes diferentes podem ter a mesma composição e ainda assim exibir espectros muito diferentes. A sequência O, B, A, F, G, K, M é, portanto, uma sequência de temperatura, e não de composição.

**Em resumo:** Estrelas parecem diferentes porque a temperatura da atmosfera muda quais átomos estão excitados ou ionizados, e não porque são feitas de coisas muito diferentes. Ela também concluiu que hidrogênio e hélio dominam em massa, uma conclusão que na época foi desencorajada e depois confirmada.

**Formalização.** O projeto percorre uma cadeia de inferência:

$$
\huge \underbrace{(G,\ G_{BP},\ G_{RP},\ J,\ H,\ K_s,\ \varpi)}_{\text{observáveis}} \;\longrightarrow\; \underbrace{(\text{cores},\ M_G)}_{\text{derivados}} \;\longrightarrow\; \underbrace{(T_{\text{eff}},\ L,\ R,\ g)}_{\text{físicos}} \;\longrightarrow\; \underbrace{\text{classe}}_{\text{rótulo}}
$$

Cada seta perde ou mistura informação. Poeira, binárias e a diferença entre anãs e gigantes criam ambiguidades. Este arquivo percorre essa cadeia seta por seta.

**Armadilha.** "Classe espectral = temperatura" vale como regra geral, mas é uma aproximação. Duas estrelas com mesma temperatura podem ter linhas espectrais diferentes por causa de gravidade superficial e metalicidade. É por isso que o problema não é trivial e por isso que existe machine learning no projeto.

---
## Luz como medida: fluxo e luminosidade

**Intuição.** Existem duas quantidades diferentes. A **luminosidade** $\large L$ é quanta energia a estrela emite por segundo (propriedade da estrela). O **fluxo** $\large F$ é quanta energia chega por segundo em cada metro quadrado do nosso detector (depende também da distância).

**Formalização.** A energia emitida se distribui sobre uma esfera de área $\large 4\pi d^2$:

$$
\huge F = \frac{L}{4\pi d^2}
$$

Duas consequências: dobrar a distância divide o fluxo por 4, e para saber $\large L$ a partir do fluxo medido é preciso conhecer $\large d$. 

Por isso a paralaxe (deslocamento aparente de um objeto próximo contra o fundo distante quando o observador se move) do Gaia é tão importante: 

A relação $\large F = L/(4\pi d^2)$ é uma equação com duas incógnitas: sem $\large d$, uma estrela fraca e próxima é indistinguível de uma estrela luminosa e distante. A paralaxe mede $\large d$ de forma **geométrica**. O Gaia entrega paralaxes para mais de um bilhão de estrelas, com precisão da ordem de décimos de milissegundo de arco, vindo do espaço, sem a turbulência da atmosfera e com um método homogêneo para toda a amostra. Isso torna possível um diagrama HR observacional em grande escala, em que anãs e gigantes se separam sem depender de modelos. 

**Exemplo numérico.** O Sol tem $\large L_\odot = 3{,}828\times10^{26}\ \text{W}$. A $\large d = 1\ \text{UA} = 1{,}496\times10^{11}\ \text{m}$:

$$
\huge F = \frac{3{,}828\times10^{26}}{4\pi\,(1{,}496\times10^{11})^2} \approx 1361\ \text{W/m}^2
$$

É a "constante solar" medida no topo da atmosfera da Terra.

**Armadilha.** Brilho aparente não diz nada sobre a natureza da estrela sem a distância. Uma estrela intrinsecamente fraca e próxima pode ter o mesmo fluxo que uma gigante muito distante.

---
## Magnitudes

**Intuição.** Astrônomos medem brilho em **magnitudes**, uma escala logarítmica e *invertida*: quanto menor o número, mais brilhante. Vem de uma convenção grega antiga em que estrelas de "primeira magnitude" eram as mais brilhantes.

**Formalização (Pogson).** Por definição, 5 magnitudes correspondem a um fator 100 em fluxo:

$$
\huge m_1 - m_2 = -2{,}5\,\log_{10}\!\left(\frac{F_1}{F_2}\right)
$$

A **magnitude absoluta** $\large M$ é a magnitude que a estrela teria a 10 *pc*, uma distância padrão. A diferença $\large m-M$ é o **módulo de distância**:

$$
\huge m - M = 5\log_{10}\!\left(\frac{d}{10\ \text{pc}}\right) = 5\log_{10} d - 5
$$

Com a paralaxe $\large \varpi$ em miliarcsegundos, $\large d = 1000/\varpi$ *pc*, e fica uma forma prática:

$$
\huge M = m + 5\log_{10}\varpi_{\text{mas}} - 10
$$

**Exemplo numérico.** Uma estrela com $\large G = 12{,}0$ e $\large \varpi = 5{,}0$ mas está a $\large d = 200$ *pc*.

$$
\huge M_G = 12{,}0 + 5\log_{10}(5{,}0) - 10 = 12{,}0 + 3{,}495 - 10 \approx 5{,}5
$$

Conferindo pelo caminho longo: $\large 5\log_{10}200 - 5 = 6{,}505$ e $\large 12{,}0-6{,}505 = 5{,}495$. ✓

Conferência com o Sol: $\large m_V=-26{,}74$ a $\large 4{,}848\times10^{-6}$ pc dá $\large M_V \approx 4{,}83$.

**Armadilha.** Como a escala é invertida, é fácil errar o sinal ao interpretar. Menor magnitude significa mais brilhante, e subir no eixo vertical de um HR corresponde a magnitudes *menores*. Por isso o eixo costuma ser invertido nos gráficos.

---
## Distância por paralaxe

**Intuição.** Estique o braço e olhe seu dedo com um olho de cada vez: ele "pula" contra o fundo. Quanto mais perto o dedo, maior o pulo. O Gaia faz isso com a órbita da Terra: mede o deslocamento aparente de uma estrela ao longo de um ano.

**Formalização.** Por definição de *parsec*, $\large d[\text{pc}] = 1/\varpi[\text{arcsec}]$. O que importa para ML é o **erro**. Se $\large \sigma_\varpi$ é a incerteza da paralaxe, a incerteza relativa na distância (para erros pequenos) é

$$
\huge \frac{\sigma_d}{d} \approx \frac{\sigma_\varpi}{\varpi} = \frac{1}{\texttt{parallax\_over\_error}}
$$

Ou seja, `parallax_over_error` é a razão sinal-ruído da paralaxe, e seu inverso é o erro fracionário na distância.

![[Pasted image 20261007115919.png]]

**Exemplo numérico**:

$\large \varpi = 5{,}0\pm0{,}5$ mas dá $\large d=200$ *pc* com erro de 10%, ou seja, $\large \varpi/\sigma_\varpi = 10$. 

Já $\large \varpi = 1{,}0\pm0{,}5$ mas dá erro de 50%, e o erro na magnitude absoluta é grande (o erro em $\large M$ é aproximadamente $\large 2{,}17\,\sigma_\varpi/\varpi$ magnitudes, ou seja, mais de 1 magnitude).

**Armadilha.** Para S/N baixo, $\large 1/\varpi$ é **enviesado**: o erro é simétrico em $\large \varpi$, mas a inversa não é linear, então $\large E[1/\varpi]\neq 1/E[\varpi]$. Paralaxes medidas podem inclusive ser negativas. Por isso o corte de qualidade não é detalhe estético: ele garante que a "distância" é confiável, e portanto também a magnitude absoluta, que alimenta o diagrama HR.

---
## Cor e temperatura

**Intuição.** A cor de uma estrela diz sua temperatura. E há um truque importante: a cor **não depende da distância**.

**Formalização (cor).** Um índice de cor é a diferença de magnitudes em duas bandas:

$$
\huge \text{BP}-\text{RP} = -2{,}5\,\log_{10}\!\left(\frac{F_{BP}}{F_{RP}}\right)
$$

Ao dividir os fluxos, o fator $\large 1/(4\pi d^2)$ cancela. Logo a cor é propriedade da estrela (a menos da poeira), e não da distância.


**Formalização (corpo negro).** Uma estrela emite aproximadamente como um corpo negro de temperatura $\large T_{\text{eff}}$. A intensidade por comprimento de onda é a lei de Planck:

$$
\huge B_\lambda(T) = \frac{2hc^2}{\lambda^5}\,\frac{1}{e^{hc/\lambda k T} - 1}
$$

Dela saem duas leis úteis. A **lei de Wien** diz onde o espectro tem pico:

$$
\huge \lambda_{\max}\,T = b \approx 2{,}898\times10^{-3}\ \text{m·K}
$$

E a **lei de Stefan-Boltzmann** diz quanta energia sai por unidade de área da superfície, e portanto a luminosidade total:

$$
\huge L = 4\pi R^2\,\sigma\,T_{\text{eff}}^4
$$

A **temperatura efetiva** $\large T_{\text{eff}}$ é *definida* por esta última equação: é a temperatura de um corpo negro com o mesmo raio e a mesma luminosidade da estrela.

**Exemplo numérico.** Para o Sol, $\large T_{\text{eff}} = 5772$ K, então $\large \lambda_{\max} = 2{,}898\times10^{-3}/5772 \approx 502$ nm (verde-azulado). Com $\large R_\odot = 6{,}957\times10^{8}$ m e $\large \sigma=5{,}670\times10^{-8}$ W m⁻² K⁻⁴, a lei de Stefan-Boltzmann devolve $\large L_\odot \approx 3{,}83\times10^{26}$ W. ✓

Uma estrela de 10 000 K tem pico em 290 nm (ultravioleta) e, nas bandas ópticas, parece azul-esbranquiçada.

**Armadilha.** Estrelas **não** são corpos negros perfeitos. As linhas de absorção e a opacidade da atmosfera deformam o espectro. Por isso a relação entre cor e $\large T_{\text{eff}}$ é calibrada empiricamente e depende de gravidade e metalicidade, e um modelo de ML pode aprender essas correções melhor que uma fórmula simples.

---
## Extinção e avermelhamento

**Intuição.** Entre nós e as estrelas há poeira interestelar. A poeira atenua a luz e **atenua mais o azul que o vermelho**. O resultado é uma estrela mais fraca e mais vermelha do que de fato é.

**Formalização.** A magnitude observada passa a incluir um termo de extinção $\large A_\lambda$ na banda $\large \lambda$:

$$
\huge m_\lambda = M_\lambda + 5\log_{10}\!\left(\frac{d}{10\ \text{pc}}\right) + A_\lambda
$$

E a cor observada fica acrescida do **excesso de cor** $\large E$:

$$
\huge (\text{BP}-\text{RP})_{\text{obs}} = (\text{BP}-\text{RP})_0 + E(\text{BP}-\text{RP})
$$

Em V, $\large A_V \approx R_V\,E(B-V)$ com $\large R_V\approx 3{,}1$ para a poeira típica do meio interestelar.

![[bernard68.jpg]]

Essa é a Bernard 68, na sua versão visível e infravermelho. É uma nuvem de poeira escura que tapa as estrelas de fundo, e em infravermelho elas aparecem. É a demonstração mais clara de extinção.

**Exemplo numérico.** Se $\large E(B-V) = 0{,}1$, então $\large A_V\approx0{,}31$ *mag*. A estrela parece 0,31 *mag* mais fraca e aproximadamente 0,1 mag mais vermelha. Pode parecer pouco, mas a sequência principal inteira cobre só algumas magnitudes de cor, então 0,1 *mag* já empurra uma estrela para a classe vizinha.

A poeira se acumula com a distância percorrida. Perto do Sol (poucas centenas de *pc*, 200 *pc*) a extinção é pequena, em geral décimos de magnitude no máximo, mas depende bastante da direção. Limitar o volume é uma forma barata de **evitar ter de corrigir** extinção. A alternativa (amostra maior com correção) dá mais estrelas e traz mais incerteza, porque a correção usa mapas 3D de poeira que têm erros próprios.

**Armadilha.** Extinção é um **confundidor degenerado**. Uma estrela intrinsecamente fria e uma estrela mais quente avermelhada pela poeira podem ter a mesma cor observada. O modelo de ML pode aprender essa degenerescência de forma implícita e isso é um viés a vigiar.

---
## O diagrama de Hertzsprung-Russell

**Intuição.** O diagrama HR é um mapa de populações de estrelas. Em vez de latitude e longitude, usa **temperatura** (ou cor) e **luminosidade** (ou magnitude absoluta). Estrelas não se espalham ao acaso: concentram-se em regiões que correspondem a fases físicas distintas.

**Analogia.** Um gráfico de peso por altura de pessoas. Não há pontos em qualquer lugar: a maioria se concentra numa faixa, com poucos casos extremos. Cada região do HR conta uma história sobre o que a estrela está fazendo.

### Imagens de Exemplo

![[gaia_HR.jpg]]

"Three Hertzsprung-Russell diagrams obtained using data from the second release of ESA's Gaia mission, showing stars with three different selections based on the star velocities."

![[HR_sunlike.png]]

![[H-R_ESO.png]]

**Regiões principais.**

- **Sequência principal:** a faixa diagonal onde estrelas queimam hidrogênio no núcleo. É onde passam a maior parte da vida. Quanto mais massiva, mais quente e mais luminosa.

- **Ramo das gigantes (vermelhas):** estrelas que esgotaram o H no núcleo e se expandiram. Frias, mas muito luminosas porque o raio é enorme.

- **Anãs brancas:** quentes, mas pequenas e pouco luminosas (restos de estrelas de massa baixa e intermediária).

**Formalização.** A leitura vem da lei de Stefan-Boltzmann. Normalizando pelo Sol:

$$
\huge \frac{L}{L_\odot} = \left(\frac{R}{R_\odot}\right)^2\left(\frac{T_{\text{eff}}}{T_{\text{eff},\odot}}\right)^4
$$

Para $\large T_{\text{eff}}$ fixo, mais luminosidade significa mais raio. Linhas de raio constante são retas no plano $\large (\log T, \log L)$, com inclinação fixa. Estrelas acima da sequência principal à mesma temperatura são, portanto, maiores.

**Exemplo numérico.** Uma gigante com $\large T_{\text{eff}}=4500$ K e $\large L=50\,L_\odot$:

$$
\huge \frac{R}{R_\odot} = \frac{\sqrt{L/L_\odot}}{(T_{\text{eff}}/T_{\text{eff},\odot})^2} = \frac{\sqrt{50}}{(4500/5772)^2} = \frac{7{,}07}{0{,}608} \approx 11{,}6
$$

Raio 11,6 vezes o do Sol, mesmo sendo mais fria. Esse mesmo raciocínio (gigante = mesma cor, mais brilho) é o que separa anãs de gigantes no Trilho A.

**Armadilha.** O HR **teórico** usa $\large T_{\text{eff}}$ e $\large L$. O HR **observacional** usa cor e $\large M_G$. Eles contam a mesma história, mas a conversão depende de calibrações e de extinção. E o eixo da temperatura costuma ser invertido (quente à esquerda), uma convenção histórica que confunde no começo.

---
## Classes espectrais e classe de luminosidade

**Intuição.** O espectro de uma estrela tem linhas escuras (absorção) em comprimentos de onda característicos de cada átomo. Quais linhas aparecem com força depende da **temperatura** da atmosfera. As classes espectrais organizam isso:

- **O**: acima de aproximadamente $\large 30.000 K$.
- **B**: aproximadamente $\large [10.000, 30.000 ]K$.
- **A**: aproximadamente $\large [7.500, 10.000]K$.
- **F**: aproximadamente $\large [6.000, 7.500] K$.
- **G**: aproximadamente $\large [5.200, 6.000] K$. O sol está aqui, é uma estrela G2.
- **K**: aproximadamente $\large [3.700, 5.200] K$.
- **M**: aproximadamente $\large [2.400, 3.700] K$ .

![[classification.jpg]]

Os limites são aproximados e variam entre fontes. Átomos de hidrogênio fazem linhas fortes na faixa onde estão **excitados**, mas **ainda não ionizados**.

**Formalização.** Dois ingredientes. A **distribuição de Boltzmann** dá a fração de átomos em níveis excitados:

$$
\huge \frac{n_2}{n_1} = \frac{g_2}{g_1}\,e^{-\Delta E/kT}
$$

E a **equação de Saha** dá o equilíbrio de ionização:

$$
\huge \frac{n_{i+1}\,n_e}{n_i} = \frac{2\,g_{i+1}}{g_i}\left(\frac{2\pi m_e k T}{h^2}\right)^{3/2} e^{-\chi_i/kT}
$$

Aqui $\large \chi_i$ é a energia de ionização, $\large n_e$ a densidade de elétrons e $\large g$ os pesos estatísticos.

**O insight de Payne.** As linhas de Balmer do hidrogênio atingem o máximo em torno de 10 000 K (classe A), e *não* porque há mais hidrogênio nas estrelas A. Em estrelas mais frias poucos átomos têm o nível $\large n=2$ populado; em estrelas mais quentes o hidrogênio está ionizado. A força da linha é um compromisso entre Boltzmann e Saha.

**Classe de luminosidade.** A letra (OBAFGKM) vem acompanhada de numeral romano: V (anã, ou sequência principal), III (gigante), I (supergigante). A diferença vem da **gravidade superficial**. Gigantes têm gravidade menor e atmosferas menos densas, então as linhas são mais estreitas (menos alargamento por pressão). É por isso que cor sozinha (que fixa $\large T_{\text{eff}}$) não basta para separar anãs e gigantes frias, e magnitude absoluta ajuda.

**Exemplo numérico.** Uma estrela com $\large T_{\text{eff}}=5000$ K cai em K. Se for sequência principal, $\large M_G\approx6$; se for gigante, $\large M_G\approx1$, uma diferença de 5 magnitudes, ou seja, um fator 100 em luminosidade. Mesma cor, objetos muito diferentes.

**O que é um "rótulo LAMOST".** O LAMOST obtém espectros e o *pipeline* atribui o tipo comparando com modelos ou espectros de referência. O rótulo é uma **estimativa** e não uma verdade absoluta. Tem erros, incertezas nas fronteiras entre classes vizinhas e vieses próprios. Essa observação importa muito: quando o modelo "erra", às vezes o rótulo é que está errado.

**Armadilha.** A classe é discreta, mas a temperatura é contínua. Uma estrela com $\large T_{\text{eff}}\approx5200$ K está na fronteira G/K e qualquer pequeno erro troca a classe. Em ML, isso significa que os erros esperados se concentram nas fronteiras entre classes vizinhas (hipótese que a Fase 06 testa).

---
## Os catálogos como instrumentos

**Intuição.** Cada catálogo é um instrumento com viés próprio. Entender o que cada um mede (e o que não mede) evita confundir limitação do instrumento com física.

### Gaia DR3

Satélite que mede astrometria (posição, paralaxe, movimento próprio) e fotometria em três bandas: $\large G$ (larga, óptica), $\large G_{BP}$ (azul) e $\large G_{RP}$ (vermelha).

A tabela `gaia_source` traz esses dados; a `astrophysical_parameters` traz parâmetros derivados, como `teff_gspphot`, estimados pelo algoritmo GSP-Phot a partir dos espectros de baixa resolução BP/RP e da paralaxe.

É administrado pela *European Space Association*, sua fotinha está abaixo:

![[esa-gaia-satellite.jpg]]

### 2MASS 

Levantamento no infravermelho próximo, em $\large J$, $\large H$ e $\large K_s$ (aproximadamente 1,25, 1,65 e 2,16 μm). A luz infravermelha é menos afetada pela poeira. O "vizinho 2MASS" é a tabela de correspondência já pronta do Gaia que associa cada estrela do Gaia à contraparte 2MASS mais provável, por posição.

"The Two Micron All-Sky Survey was an astronomical survey of the whole sky in infrared light. It took place between 1997 and 2001, in two different locations: at the U.S. Fred Lawrence Whipple Observatory on Mount Hopkins, Arizona, and at the Cerro Tololo Inter-American Observatory in Chile, each using a 1.3-meter telescope for the Northern and Southern Hemisphere, respectively"

| ![[2mass2.jpg]] |
| --------------- |
| ![[2mass1.jpg]] |

### LAMOST (LRS) 

Levantamento espectroscópico em baixa resolução (resolução $\large R\sim1800$, cobertura óptica de aproximadamente 3700–9000 Å). Fornece espectros e as classes espectrais usadas como rótulo.

É coordenado pela Academia Chinesa de Ciências, e está localizado em Beijing.

![[lamost.jpg]]


**O cross-match LAMOST ↔ Gaia.** Usar o ID publicado ou casar por posição. A dificuldade física está no **movimento próprio**: as posições do Gaia são dadas para a época 2016,0, enquanto as do LAMOST podem se referir a outra época. Uma estrela com movimento próprio de 100 mas/ano desloca-se $\large 100\times16 = 1600$ mas $\large =1{,}6''$ em 16 anos. Se o raio de busca for menor que isso, a estrela é perdida. Se for grande demais, aumentam os falsos pareamentos em campos densos.

**Seleção e vieses.** Nenhum desses catálogos é uma amostra "justa" do céu. O LAMOST tem uma região do céu e um limite de brilho e prioriza certos tipos de alvo. O Gaia tem seu limite de completude. Isso afeta a proporção das classes (por exemplo, muito mais K e G do que O e B) e pode induzir correlações espúrias entre magnitude aparente e classe.

**Armadilha.** `teff_gspphot` não é uma medida direta. É uma estimativa por modelo que usa fotometria Gaia, a mesma informação que o classificador do projeto usa como feature. Isso torna o *baseline* do ROADMAP (classe prevista por faixa de Teff) parcialmente circular: é modelo contra modelo, ambos alimentados por cores semelhantes. Vale ter isso em mente ao interpretar a comparação.

---
## Qualidade de dados: o que é "dado ruim" fisicamente

**Intuição.** Os cortes de qualidade existem porque cada um elimina uma fonte física de erro que corromperia as features.

**`parallax_over_error`.** Já visto na seção 4: elimina distâncias pouco confiáveis, logo magnitudes absolutas ruins.

**RUWE (*Renormalised Unit Weight Error*).** Mede o quão bem um modelo de estrela *única* ajusta as observações astrométricas. Em torno de 1 é um bom ajuste. Valores acima de aproximadamente 1,4 costumam ser tomados como suspeitos. O motivo físico mais comum é uma **companheira não resolvida** (binária): o fotocentro oscila, e a paralaxe e as cores podem estar contaminadas.

**Qualidade fotométrica do 2MASS.** Cada medida vem com um sinalizador de qualidade (de A, melhor, a classes piores), refletindo sinal-ruído, contaminação por vizinhas e saturação. Cores $\large J-H$ ou $\large H-K_s$ com qualidade ruim injetam ruído nas features.

**Armadilha.** Cortes de qualidade **mudam a amostra**, e não só a limpam. Exigir `parallax_over_error` alto privilegia estrelas próximas e brilhantes; exigir RUWE baixo remove binárias. O modelo final só vale para o tipo de estrela que sobreviveu aos cortes, e é por isso que o ROADMAP pede que os cortes sejam documentados e justificados.

---
