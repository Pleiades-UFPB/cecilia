
Este arquivo cobre a física "por dentro" da estrela: como ondas que atravessam o interior nos contam a massa, o raio e o estágio evolutivo (Trilho B), e como se descreve matematicamente a estrutura interna que a Fase 07 pretende visualizar. 


Constantes solares usadas nos exemplos: $\large T_{\text{eff},\odot}=5772$ K, $\large \nu_{\max,\odot}\approx3090\ \mu\text{Hz}$, $\large \Delta\nu_\odot\approx135{,}1\ \mu\text{Hz}$, $\large \log g_\odot = 4{,}438$ (cgs).

---
## A estrela como instrumento musical

**Intuição.** A superfície de uma estrela como o Sol *treme*, de forma muito sutil, porque a convecção nas camadas externas "bate" continuamente no interior, como se alguém tamborilasse uma panela. O interior responde com ondas sonoras que ficam presas dentro da estrela, em modos de vibração definidos pelo tamanho e pela densidade.

**Analogia.** Uma corda de violão ou um tubo de órgão. O comprimento e o material determinam as notas que ela emite. A estrela é um tubo de órgão esférico e gasoso: medindo as "notas", deduzimos suas dimensões e sua constituição sem nunca entrar nela.

**Formalização.** Para uma corda de comprimento $\large L$ e velocidade de onda $\large v$, as frequências permitidas são

$$
\huge f_n = n\,\frac{v}{2L}, \qquad n=1,2,3,\dots
$$

O espaçamento entre notas consecutivas é $\large v/2L$, ou seja, o inverso do tempo de ida e volta da onda. Numa estrela, o papel de $\large v$ é feito pela **velocidade do som** $\large c_s = \sqrt{\Gamma_1 P/\rho}$, que varia com o raio. O espaçamento entre modos consecutivos (**separação grande**) é o inverso do tempo de ida e volta do som através da estrela:

$$
\huge \Delta\nu = \left(2\int_0^R \frac{dr}{c_s(r)}\right)^{-1}
$$

**Por que $\large \Delta\nu$ mede a densidade média.** Pela estimativa de equilíbrio (seção 7), $\large c_s^2\sim GM/R$. O tempo de travessia é então $\large R/c_s\sim\sqrt{R^3/GM}$, e

$$
\huge \Delta\nu\ \propto\ \sqrt{\frac{GM}{R^3}}\ \propto\ \sqrt{\bar\rho}
$$

Quanto mais densa a estrela, mais rápido o som a cruza, e maior o espaçamento. Gigantes, enormes e tênues, têm $\large \Delta\nu$ muito pequeno.

**Exemplo numérico.** Para o Sol, $\large \sqrt{GM/R}\approx4{,}4\times10^5$ m/s e $\large R/c_s\approx1600$ s, o que daria $\large \Delta\nu\sim1/(2\cdot1600)\approx310\ \mu\text{Hz}$. O valor real é 135 μHz: a estimativa erra por um fator de ordem 2, o que é esperado, pois usamos uma velocidade típica em vez de integrar. A *escala* está certa, e é isso que a análise dimensional promete.

**Armadilha.** Os modos são ondas *estacionárias* de amplitude minúscula: algumas partes por milhão de variação de brilho. Só foram detectados de forma rotineira em milhares de estrelas com telescópios espaciais (CoRoT, Kepler, TESS).

---
## Modos p e g, e modos mistos

**Intuição.** Há dois tipos de "força de restauração" que fazem uma bolha de gás voltar ao lugar depois de deslocada, e cada uma dá uma família de ondas.

- **Modos p (pressão):** o gás comprimido empurra de volta. São ondas sonoras. Têm frequências mais altas e vivem sobretudo no envelope.
- **Modos g (gravidade):** a **flutuabilidade** puxa de volta (como uma rolha afundada que sobe). São mais lentos, e ficam confinados em regiões radiativas estáveis, no caso das gigantes, o núcleo.

**Analogia.** Um tambor (modo p, a pele elástica empurra de volta) e uma banheira com ondas de superfície (modo g, a gravidade nivela a água).

**Formalização.** Cada modo é rotulado por $\large (n,\ell,m)$: ordem radial $\large n$, grau angular $\large \ell$ (número de linhas nodais na superfície) e ordem azimutal $\large m$. Na aproximação assintótica, os modos p têm espaçamento igual em **frequência**:

$$
\huge \nu_{n,\ell}\approx\Delta\nu\left(n+\frac{\ell}{2}+\varepsilon\right)
$$

e os modos g têm espaçamento igual em **período**, com

$$
\huge \Delta\Pi_\ell = \frac{2\pi^2}{\sqrt{\ell(\ell+1)}}\left(\int\frac{N}{r}\,dr\right)^{-1}
$$

onde $\large N$ é a frequência de Brunt-Väisälä, que mede a estabilidade à flutuabilidade, e a integral é feita na região onde o modo g existe (o núcleo, para gigantes).

**Modos mistos.** Em gigantes, os modos $\large \ell=1$ do envelope (tipo p) e do núcleo (tipo g) têm frequências sobrepostas e se **acoplam**. O resultado são modos que são "meio p, meio g", que carregam informação **do núcleo** até a superfície, onde podemos medi-la.

**Exemplo.** Para $\large \ell=1$ o termo fica $\large 2\pi^2/\sqrt2$; o espaçamento $\large \Delta\Pi_1$ é da ordem de dezenas a centenas de segundos para gigantes, como veremos na seção 5.

**Armadilha.** O ROADMAP lista $\large \nu_{\max}$ e $\large \Delta\nu$ como features, e ambos vêm dos modos p. A informação sobre o **núcleo** (que é o que de fato distingue RGB de RC) está em $\large \Delta\Pi_1$, que vem dos modos mistos e não está na lista de features candidatas. Voltaremos a isso na seção 5.

---
## Os dois números centrais: $\large \nu_{\max}$ e $\large \Delta\nu$

**Intuição.** Se você observa o brilho de uma estrela ao longo de meses e decompõe a curva em frequências, vê um **espectro de potência** com uma "corcunda" de picos. Dois números resumem quase tudo:

- $\large \nu_{\max}$: a frequência onde a corcunda é mais alta (onde os modos têm mais energia).
- $\large \Delta\nu$: o espaçamento regular entre os picos.

**Analogia.** Uma cesta de sinos tocados ao acaso: alguns soam alto, outros baixo. $\large \nu_{\max}$ é o tom em que a cesta "soa mais forte", e $\large \Delta\nu$ é a distância regular entre as notas.

**Formalização.** O espectro de potência de uma série temporal $\large x(t)$ é

$$
\huge P(\nu)=\left|\int x(t)\,e^{-2\pi i\nu t}\,dt\right|^2
$$

A resolução em frequência é $\large \delta\nu\sim1/T$, onde $\large T$ é a duração da observação. Quatro anos de Kepler dão $\large \delta\nu\approx 1/(1{,}26\times10^{8}\ \text{s})\approx0{,}008\ \mu\text{Hz}$, mais que suficiente para resolver $\large \Delta\nu$ de alguns μHz em gigantes.

**Por que $\large \nu_{\max}$ existe.** A convecção excita ondas num intervalo de frequências, e o envelope de amplitude é uma corcunda porque a excitação é eficiente perto da escala de tempo característica das células convectivas, enquanto acima da **frequência de corte acústica** $\large \nu_{\text{ac}}$ as ondas escapam em vez de ficarem presas. Isso conecta $\large \nu_{\max}$ à atmosfera (seção 4).

**Exemplo.** No Sol, $\large \nu_{\max}\approx3090\ \mu\text{Hz}$, que corresponde a um período de cerca de 5,4 minutos, as famosas "oscilações de 5 minutos". Numa gigante com $\large \nu_{\max}\approx35\ \mu\text{Hz}$ o período é de cerca de 8 horas.

**Armadilha.** Tanto $\large \nu_{\max}$ quanto $\large \Delta\nu$ são **medidas** com incerteza, e dependem do método de extração. A qualidade cai quando a razão sinal-ruído é baixa (estrelas fracas) ou a série é curta. Um corte de qualidade sísmica é o equivalente, aqui, de `parallax_over_error` do Trilho A.

---
## Relações de escala: de $\large (\nu_{\max},\Delta\nu,T_{\text{eff}})$ para massa e raio

**Intuição.** Com dois números sísmicos e a temperatura, que são três observáveis, é possível resolver para duas incógnitas, **massa** e **raio**, sem nenhuma medida de distância.

**Formalização.** Normalizadas pelo Sol, as duas relações são

$$
\huge \frac{\Delta\nu}{\Delta\nu_\odot}=\left(\frac{M}{M_\odot}\right)^{1/2}\left(\frac{R}{R_\odot}\right)^{-3/2} \qquad\quad \frac{\nu_{\max}}{\nu_{\max,\odot}}=\left(\frac{M}{M_\odot}\right)\left(\frac{R}{R_\odot}\right)^{-2}\left(\frac{T_{\text{eff}}}{T_{\text{eff},\odot}}\right)^{-1/2}
$$

A primeira vem da seção 1 ($\large \Delta\nu\propto\sqrt{\bar\rho}$). A segunda se apoia na hipótese de que $\large \nu_{\max}$ é proporcional à frequência de corte acústica:

$$
\huge \nu_{\max}\ \propto\ \nu_{\text{ac}}=\frac{c_s}{4\pi H_P}\ \propto\ \frac{\sqrt{T}}{T/g}=\frac{g}{\sqrt{T}}
$$

onde $\large H_P\propto T/g$ é a escala de altura de pressão da atmosfera. Esta segunda relação é **empírica e heurística**, com sustentação teórica parcial, e é um tema ativo de pesquisa.

**Invertendo.** Chamando $\large \delta=\Delta\nu/\Delta\nu_\odot$, $\large \nu=\nu_{\max}/\nu_{\max,\odot}$ e $\large \tau=T_{\text{eff}}/T_{\text{eff},\odot}$:

$$
\huge \frac{R}{R_\odot}=\nu\,\delta^{-2}\,\tau^{1/2} \qquad\quad \frac{M}{M_\odot}=\nu^{3}\,\delta^{-4}\,\tau^{3/2}
$$

Passo a passo: da primeira relação, $\large M/M_\odot=\delta^2(R/R_\odot)^3$. Substituindo na segunda, $\large \nu=\delta^{2}(R/R_\odot)\,\tau^{-1/2}$, que dá o raio. Depois, $\large M/M_\odot=\delta^2\,(\nu\delta^{-2}\tau^{1/2})^3=\nu^3\delta^{-4}\tau^{3/2}$.

**Exemplo numérico.** Uma estrela com $\large \nu_{\max}=35\ \mu\text{Hz}$, $\large \Delta\nu=4{,}0\ \mu\text{Hz}$ e $\large T_{\text{eff}}=4800$ K:

- $\large \nu=35/3090=0{,}01133$
- $\large \delta=4{,}0/135{,}1=0{,}02961$
- $\large \tau=4800/5772=0{,}8316$

$$
\huge \frac{R}{R_\odot}=\frac{0{,}01133}{(0{,}02961)^2}\sqrt{0{,}8316}\approx 11{,}8 \qquad\quad \frac{M}{M_\odot}=\frac{(0{,}01133)^3}{(0{,}02961)^4}\,(0{,}8316)^{3/2}\approx 1{,}4
$$

Uma gigante de aproximadamente 12 raios solares e 1,4 massa solar, valores típicos de uma estrela do *red clump*.

**O exercício de "redescobrir a fórmula".** Em escala logarítmica a relação é **linear**:

$$
\huge \log\frac{M}{M_\odot}=3\log\nu-4\log\delta+\tfrac32\log\tau
$$

Por isso uma regressão linear nos logaritmos acharia os expoentes 3, −4 e 3/2 quase exatamente. Já um modelo de árvores (Random Forest, XGBoost) aproxima a função por **degraus**: bom dentro do intervalo de treino, ruim fora dele, porque árvores não extrapolam. O exercício é didático justamente por mostrar essa diferença entre modelos e por mostrar que o ML "reencontra" uma lei que já conhecemos. Como o ROADMAP já avisa, não é resultado novo.

**Armadilha.** As massas publicadas em catálogos como o APOKASC tipicamente são derivadas **dessas mesmas relações** (com correções). Então prever "massa" a partir de $\large \nu_{\max}$, $\large \Delta\nu$ e $\large T_{\text{eff}}$ é, em grande parte, aprender a própria fórmula de volta: um caso de circularidade a declarar no relatório. Além disso, as relações têm desvios sistemáticos de poucos por cento que dependem do estágio evolutivo e da metalicidade.

---
## RGB vs RC: o que acontece dentro da gigante

**Intuição.** Existem dois tipos de gigantes que, de fora, parecem quase iguais, mas têm interiores completamente diferentes.

- **RGB (*red giant branch*, ramo das gigantes vermelhas):** o núcleo de hélio **inerte e degenerado** não queima nada. A energia vem de uma **casca** de hidrogênio ao redor dele. A estrela sobe a luminosidade conforme o núcleo cresce.
- **RC (*red clump*, "aglomerado vermelho"):** o núcleo de hélio **queima**, por meio da reação triplo-alfa ($\large 3\,{}^4\text{He}\to{}^{12}\text{C}$), e há ainda uma casca de H queimando por fora.

**Analogia.** Dois prédios com a mesma altura e fachada, mas um é um depósito parado, e o outro tem uma fornalha ligada no subsolo. A estrutura interna é muito diferente, apesar da silhueta semelhante.

**A física da transição.** Em estrelas com massa inicial abaixo de aproximadamente 2 massas solares, o núcleo de He do RGB é degenerado: a pressão vem do princípio de exclusão de Pauli e quase não depende da temperatura. Quando a temperatura central atinge cerca de $\large 10^8$ K, o He "ignora" violentamente (**flash do hélio**), o núcleo se expande, e a estrela se rearranja no clump.

**Por que o clump é um aglomerado.** O flash ocorre sempre com uma massa de núcleo quase idêntica (cerca de 0,47 massa solar), então as RC têm luminosidade quase igual, da ordem de 50 $\large L_\odot$, e temperaturas parecidas. Elas se acumulam numa região estreita do diagrama, daí o nome, e por isso servem como **velas padrão**.

**Por que é difícil separar só com $\large \nu_{\max}$ e $\large \Delta\nu$.** Ambos os tipos obedecem às mesmas relações de escala. Uma estrela RGB com o mesmo raio e massa de uma RC tem os mesmos $\large \nu_{\max}$ e $\large \Delta\nu$. O clump ocupa uma região bem definida do plano, mas **estrelas RGB passam pela mesma região** em sua subida, então os dois grupos se sobrepõem. Em Teff e log g há uma pequena diferença sistemática (para a mesma gravidade, as RC tendem a ser mais quentes que as RGB), que o ML pode explorar, mas é sutil.

**O que separa de verdade: $\large \Delta\Pi_1$.** O núcleo degenerado do RGB é muito denso e compacto, e a integral $\large \int N/r\,dr$ é grande, então $\large \Delta\Pi_1$ é pequeno, da ordem de algumas dezenas de segundos até pouco mais de uma centena. O núcleo convectivo e não degenerado do RC é menos denso, o que dá $\large \Delta\Pi_1$ da ordem de 250–300 s. Há pouca sobreposição: é por isso que os catálogos de referência atribuem o estágio evolutivo com base nesse espaçamento. Esta informação é nova e exige a análise de modos mistos (seção 2).

**Ponto de atenção para a Fase 05.** As features candidatas do ROADMAP ($\large \nu_{\max}$, $\large \Delta\nu$, Teff, [M/H]) deixam de fora o discriminador mais direto. Duas consequências:

- Se $\large \Delta\Pi_1$ estiver disponível no catálogo, **não** deve entrar como feature se o rótulo foi derivado dele, porque é vazamento (arquivo 02, seção 2.3). A pergunta de pesquisa fica sendo: *quão bem dá para recuperar o estágio sem a feature que o define?*
- Se o rótulo vier de outra fonte, usar $\large \Delta\Pi_1$ muda o problema de "difícil" para "quase trivial". A decisão é de desenho experimental, e cabe numa sessão de `/paul:discover`.

**Armadilha.** Um modelo de ML que alcança alta acurácia nesse problema pode estar *redescobrindo* o rótulo por meio de correlações com a definição dele. A interpretação (SHAP, arquivo 02, seção 10) é a forma de verificar se a física aprendida é a esperada.

---
## 6. Diagrama Kiel e espaço $\large \nu_{\max}$–$\large \Delta\nu$

**Intuição.** O diagrama de **Kiel** é o primo do HR em que, no lugar da luminosidade, usa-se a **gravidade superficial** $\large \log g$. A vantagem é que $\large g$ pode ser obtida pela sismologia, **sem medir a distância**.

**Formalização.** A gravidade superficial é $\large g=GM/R^2$. Das relações da seção 4:

$$
\huge \frac{g}{g_\odot}=\frac{\nu_{\max}}{\nu_{\max,\odot}}\left(\frac{T_{\text{eff}}}{T_{\text{eff},\odot}}\right)^{1/2}
$$

Ou seja, $\large \log g$ sai direto de $\large \nu_{\max}$ e de $\large T_{\text{eff}}$.

**Exemplo numérico.** Para $\large \nu_{\max}=35\ \mu\text{Hz}$ e $\large T_{\text{eff}}=4800$ K: $\large g/g_\odot=0{,}01133\times\sqrt{0{,}8316}=0{,}01033$, então

$$
\huge \log g=4{,}438+\log_{10}(0{,}01033)=4{,}438-1{,}986\approx 2{,}45
$$

valor típico de uma gigante do clump.

**Por que o Trilho B vê o Kiel e não o HR.** No HR é preciso conhecer $\large L$, ou seja, a distância. Em catálogos asterossísmicos, $\large g$ vem da sismologia e é independente da paralaxe, o que dá um plano limpo para visualizar o estágio evolutivo.

**Armadilha.** Quando se comparam os dois diagramas (HR do Trilho A, Kiel do Trilho B), lembre que os eixos medem coisas diferentes: luminosidade (uma propriedade que depende do raio) contra gravidade (propriedade que depende de massa e raio). Estrelas que ocupam posições análogas não estão necessariamente em fases análogas.

---
## Equilíbrio hidrostático

**Intuição.** Uma estrela não colapsa nem explode: em cada camada, a **pressão** que empurra para fora equilibra o **peso** da matéria acima, que puxa para dentro.

**Analogia.** Uma pilha de colchões. O colchão de baixo é mais comprimido que o de cima, porque sustenta mais peso. A pressão cresce conforme se desce.

**Formalização.** Considere uma fina casca de espessura $\large dr$ e área $\large A$ no raio $\large r$. O peso é $\large dm\cdot g=(\rho A\,dr)\,\dfrac{Gm(r)}{r^2}$, e a pressão que o sustenta é a diferença de pressão entre as faces, vezes a área. Igualando:

$$
\huge \frac{dP}{dr}=-\frac{G\,m(r)\,\rho(r)}{r^2}
$$

onde $\large m(r)$ é a massa contida dentro do raio $\large r$. O sinal negativo indica que a pressão **cai** para fora.

**Estimativa de ordem de grandeza.** Trocando derivadas por razões, $\large P_c\sim GM^2/R^4$. Para o Sol:

$$
\huge P_c\sim\frac{(6{,}67\times10^{-11})(1{,}99\times10^{30})^2}{(6{,}96\times10^{8})^4}\approx10^{15}\ \text{Pa}
$$

O valor real é cerca de $\large 2{,}5\times10^{16}$ Pa. Está uns 20 vezes acima, porque a estimativa ignora que a matéria se concentra no centro, mas acerta a escala (bilhões de atmosferas).

**Temperatura central.** Combinando com a lei dos gases ideais, $\large kT\sim G M\,\mu m_H/R$. Com $\large \mu\approx0{,}6$ (massa média por partícula, em unidades de $\large m_H$):

$$
\huge T_c\sim\frac{(6{,}67\times10^{-11})(1{,}99\times10^{30})(0{,}6)(1{,}67\times10^{-27})}{(1{,}38\times10^{-23})(6{,}96\times10^{8})}\approx1{,}4\times10^{7}\ \text{K}
$$

O valor real é aproximadamente $\large 1{,}57\times10^7$ K. É um resultado impressionante para um cálculo de uma linha: o equilíbrio hidrostático sozinho prevê que o centro do Sol é quente o bastante para fusão nuclear.

**Armadilha.** Equilíbrio hidrostático **não** diz de onde vem a energia, nem como ela é transportada. Para fechar o sistema são necessárias mais equações (seção 8). Além disso, a hipótese de equilíbrio falha em fases rápidas (flash do hélio, explosões).

---
## As equações da estrutura estelar

**Intuição.** Modelar o interior de uma estrela é fazer uma **contabilidade** em cada camada: massa, força, energia e calor. Cada equação é uma conta que precisa fechar.

**Formalização.** As quatro equações de estrutura em simetria esférica e regime estacionário:

$$
\huge \frac{dm}{dr}=4\pi r^2\rho \qquad\quad \frac{dP}{dr}=-\frac{G\,m\,\rho}{r^2}
$$

$$
\huge \frac{dL}{dr}=4\pi r^2\rho\,\varepsilon \qquad\quad \frac{dT}{dr}=-\,\frac{T}{P}\,\frac{G\,m\,\rho}{r^2}\,\nabla
$$

onde $\large L(r)$ é a luminosidade que atravessa o raio $\large r$, $\large \varepsilon$ é a energia gerada por unidade de massa por segundo, e $\large \nabla=d\ln T/d\ln P$ é o gradiente de temperatura. As quatro contas são:

- **Conservação de massa:** a massa de uma casca é densidade vezes volume.
- **Equilíbrio hidrostático:** a seção anterior.
- **Conservação de energia:** a luminosidade aumenta quando a casca gera energia.
- **Transporte de energia:** como o calor vai para fora (radiação ou convecção, seção 10).

Faltam **relações constitutivas**: a equação de estado $\large P(\rho,T,X_i)$, a **opacidade** $\large \kappa(\rho,T,X_i)$ e a taxa de geração de energia $\large \varepsilon(\rho,T,X_i)$. Elas carregam a física microscópica (gás ideal, radiação, reações nucleares).

**Condições de contorno.** No centro, $\large m(0)=0$ e $\large L(0)=0$. Na superfície, $\large P$ e $\large T$ se ajustam à atmosfera, com $\large m(R)=M$ e $\large L(R)=L$.

**Teorema de Vogt-Russell (em termos informais).** Dada a **massa total e a composição química** (e a história de como a composição evoluiu), a estrutura da estrela fica essencialmente determinada. Por isso a massa é o parâmetro mais importante na vida de uma estrela.

**Composição.** Descreve-se por frações em massa $\large X$ (hidrogênio), $\large Y$ (hélio) e $\large Z$ (todo o resto, os "metais" em linguagem astronômica), com

$$
\huge X+Y+Z=1
$$

Na fotosfera solar, aproximadamente $\large X\approx0{,}74$, $\large Y\approx0{,}25$ e $\large Z\approx0{,}013$.

**Armadilha.** São equações **acopladas e não lineares** e, em geral, sem solução analítica. Resolvem-se numericamente (como faz o MESA). A elegância está em que quatro equações diferenciais mais três relações de microfísica fecham o problema.

---
## O polítropo de Lane-Emden

**Intuição.** Se supusermos que pressão e densidade seguem uma relação de potência simples, as equações de estrutura colapsam numa única equação para um único perfil adimensional. É um modelo de brinquedo que, mesmo sendo grosseiro, acerta a forma geral do interior.

**Formalização.** Assume-se um **polítropo** de índice $\large n$:

$$
\huge P=K\,\rho^{\,1+1/n}
$$

Para chegar à equação, comece com o equilíbrio hidrostático, multiplique por $\large r^2/\rho$ e derive em relação a $\large r$, usando $\large dm/dr=4\pi r^2\rho$:

$$
\huge \frac{1}{r^2}\frac{d}{dr}\!\left(\frac{r^2}{\rho}\frac{dP}{dr}\right)=-4\pi G\rho
$$

Com $\large \rho=\rho_c\,\theta^{\,n}$ e $\large r=a\,\xi$, onde $\large a^2=\dfrac{(n+1)K\rho_c^{\,1/n-1}}{4\pi G}$, resulta na **equação de Lane-Emden**:

$$
\huge \frac{1}{\xi^2}\frac{d}{d\xi}\!\left(\xi^2\frac{d\theta}{d\xi}\right)=-\theta^{\,n}, \qquad \theta(0)=1,\quad \theta'(0)=0
$$

A superfície da estrela é o primeiro zero $\large \theta(\xi_1)=0$. A densidade e a temperatura (gás ideal, $\large T=\mu m_H P/k\rho$) ficam

$$
\huge \rho(r)=\rho_c\,\theta^{\,n} \qquad\quad T(r)=T_c\,\theta
$$

**Soluções exatas.**

- $\large n=0$ (densidade uniforme): $\large \theta=1-\xi^2/6$, com $\large \xi_1=\sqrt6$.
- $\large n=1$: $\large \theta=\dfrac{\sin\xi}{\xi}$, com $\large \xi_1=\pi$.
- $\large n=5$: $\large \theta=(1+\xi^2/3)^{-1/2}$, que **nunca** chega a zero (raio infinito).

Para outros valores, integra-se numericamente. Dois casos de interesse físico são $\large n=1{,}5$ (gás totalmente convectivo, adiabático e monoatômico, $\large n=1/(\gamma-1)$ com $\large \gamma=5/3$), com $\large \xi_1\approx3{,}654$, e $\large n=3$ (**modelo de Eddington**, um modelo razoável para estrelas radiativas de massa média), com $\large \xi_1\approx6{,}897$.

**Quão concentrada é a estrela.** A razão entre densidade central e média é

$$
\huge \frac{\rho_c}{\bar\rho}=\frac{\xi_1}{3\,|\theta'(\xi_1)|}
$$

Valores: $\large n=0\Rightarrow1$; $\large n=1\Rightarrow\pi^2/3\approx3{,}29$; $\large n=1{,}5\Rightarrow\approx6{,}0$; $\large n=3\Rightarrow\approx54$. O Sol real tem $\large \rho_c/\bar\rho\approx107$ (centro de $\large \sim150$ g/cm³ contra média de 1,41 g/cm³), ainda mais concentrado que $\large n=3$, mas bem mais perto dele que de $\large n=0$.

**O que o polítropo dá e não dá.** Fornece $\large \rho(r)$ e $\large T(r)$ com **forma** realista, e a escala vem de $\large M$ e $\large R$. Mas **não** tem composição ($\large X$, $\large Y$): para calcular $\large T$ foi preciso assumir $\large \mu$ constante, o que significa uma estrela de composição uniforme. Por isso a decisão aberta do ROADMAP aponta a combinação com o modelo solar para obter perfis de $\large X$ e $\large Y$.

**Armadilha.** O índice $\large n$ é um parâmetro de ajuste, e não uma medição. Uma mesma estrela real tem $\large n$ efetivo diferente em regiões diferentes (núcleo radiativo, envelope convectivo). O polítropo é um modelo didático, não uma previsão.

---
## Transporte de energia e as zonas internas

*Ligação com o projeto: Fase 07 (diagrama de camadas: núcleo, zona radiativa, zona convectiva).*

**Intuição.** A energia gerada no núcleo precisa chegar à superfície. Há dois mecanismos principais, e a estrela usa o que for mais eficiente em cada camada.

- **Radiação:** os fótons fazem um "passeio aleatório" de absorção e reemissão, atravessando camadas lentamente.
- **Convecção:** o próprio gás sobe e desce em células, carregando calor, como a água fervendo numa panela.

**Analogia.** Passar baldes de água numa fila de pessoas (radiação) contra correr com os baldes até o outro lado (convecção). A fila funciona bem se ela flui. Se há um gargalo, mais gente prefere correr.

**Formalização (radiativo).** Quando a energia é transportada por difusão de fótons, o gradiente de temperatura necessário é

$$
\huge \nabla_{\text{rad}}=\frac{3}{16\pi a c\,G}\,\frac{\kappa\,L\,P}{m\,T^4}
$$

onde $\large a$ é a constante de radiação. Gradientes grandes surgem quando a **opacidade** $\large \kappa$ é alta (o gás é "opaco" e a luz passa mal) ou o fluxo de energia por camada é muito alto.

**Critério de Schwarzschild.** Uma camada é instável à convecção se o gradiente radiativo necessário supera o gradiente adiabático:

$$
\huge \nabla_{\text{rad}}>\nabla_{\text{ad}}\quad\Longrightarrow\quad\text{convecção}
$$

Para um gás ideal monoatômico, $\large \nabla_{\text{ad}}=1-1/\gamma=0{,}4$. A intuição é que, se a radiação não consegue escoar o calor sem exigir um gradiente maior que o adiabático, uma bolha deslocada para cima fica mais quente que o ambiente e continua subindo.

**Exemplos de estrutura, em linhas gerais.**

- **Sol:** núcleo radiativo, e um envelope convectivo externo, que começa em cerca de $\large 0{,}71\,R_\odot$ (bem determinado por heliossismologia), onde a opacidade é alta por causa da temperatura relativamente baixa.
- **Estrelas mais massivas** (acima de aproximadamente 1,3 massa solar): **núcleo convectivo** (a geração de energia pelo ciclo CNO é muito sensível à temperatura, o que cria um fluxo concentrado e um gradiente alto) e envelope radiativo.
- **Anãs M de baixa massa** (abaixo de aproximadamente 0,35 massa solar): totalmente convectivas.
- **Gigantes:** envelope convectivo muito profundo (e é a convecção ali que excita as oscilações da seção 1).

**Armadilha.** A convecção real é tridimensional e turbulenta. Modelos 1D a representam pela **teoria do comprimento de mistura**, que tem um parâmetro livre (o comprimento de mistura $\large \alpha_{\text{MLT}}$) calibrado, em geral, para reproduzir o Sol.

---

## 11. O modelo solar padrão: perfis de T, ρ, X e Y

*Ligação com o projeto: Fase 07, opção (b) da decisão aberta.*

**Intuição.** O Sol é a única estrela cujo interior conhecemos com precisão suficiente para ter um modelo "de referência". Ele é construído evoluindo uma estrela de 1 massa solar por 4,6 bilhões de anos, ajustando parâmetros iniciais até acertar luminosidade, raio e composição superficial atuais, e depois é validado pela heliossismologia (as mesmas ondas das seções 1 a 3, no Sol). Tabelas desses modelos, como o Model S (Christensen-Dalsgaard et al. 1996), são públicas.

**O que elas contêm.** Para cada raio: $\large T$, $\large \rho$, $\large P$, $\large m(r)$, $\large L(r)$, $\large X$ e $\large Y$. Em ordens de grandeza: centro com $\large \rho_c\approx150$ g/cm³ e $\large T_c\approx1{,}57\times10^7$ K, e superfície com $\large T\sim5800$ K.

**Por que $\large X$ e $\large Y$ variam com o raio.** A fusão converte hidrogênio em hélio no núcleo. O resultado:

$$
\huge 4\,{}^1\text{H}\ \longrightarrow\ {}^4\text{He}+2e^{+}+2\nu_e+\text{energia}
$$

No centro, $\large X$ caiu de aproximadamente 0,70 (inicial) para algo em torno de 0,35 hoje, e $\large Y$ subiu, enquanto o envelope, bem misturado pela convecção e sem fusão, mantém praticamente a composição original (com pequena depleção por sedimentação gravitacional). O perfil de $\large X$ e $\large Y$ é, portanto, um **registro da idade e do histórico** do Sol.

**Exemplo numérico (a conta da fusão).** Quatro átomos de H têm massa $\large 4{,}0313$ u e um átomo de He-4 tem $\large 4{,}0026$ u. A diferença é

$$
\huge \frac{\Delta m}{m}=\frac{0{,}0287}{4{,}0313}\approx0{,}71\%
$$

e vira energia por $\large E=\Delta m\,c^2$ (cerca de 26,7 MeV por reação, parte dela levada por neutrinos). Para sustentar $\large L_\odot$, a massa de hidrogênio fundida por segundo é

$$
\huge \dot m_H=\frac{L_\odot}{0{,}0071\,c^2}=\frac{3{,}83\times10^{26}}{0{,}0071\times8{,}99\times10^{16}}\approx6\times10^{11}\ \text{kg/s}
$$

ou seja, cerca de 600 milhões de toneladas de hidrogênio por segundo. O Sol ainda tem estoque de sobra: está só no meio da vida.

**Zonas.** A geração de energia está concentrada no núcleo (a maior parte dentro de aproximadamente 0,25 $\large R_\odot$), seguida da zona radiativa até aproximadamente 0,71 $\large R_\odot$ e, por fim, da zona convectiva até a superfície (seção 10). O diagrama de camadas da Fase 07 representa exatamente isso.

**Armadilha.** O modelo solar é **só do Sol**. Aplicar seus perfis de $\large X$ e $\large Y$ a outras estrelas é uma aproximação por *escala* e não um cálculo. Estrelas de massa e idade diferentes têm núcleos convectivos, extensões de zonas e perfis de composição distintos. Nesse sentido, a combinação (a)+(b) do ROADMAP é um recurso didático para visualização e deve ser descrita assim.

---

## 12. O que o 1D esconde

*Ligação com o projeto: "Fora do roadmap" (hidrodinâmica 3D) e opção (c) da decisão aberta (MESA).*

**Intuição.** Modelos de estrutura 1D tratam a estrela como uma sequência de cascas concêntricas idênticas em todas as direções. É uma simplificação poderosa e, ao mesmo tempo, uma lista de coisas que não estão no modelo.

**O que fica de fora.**

- **Rotação e campos magnéticos:** quebram a simetria esférica e afetam a mistura interna.
- **Convecção tridimensional:** substituída por um parâmetro de comprimento de mistura.
- **Mistura além dos limites convectivos** (*overshooting*): a matéria "escorrega" um pouco além da fronteira, e o tamanho desse efeito é incerto, mas altera a duração das fases de vida.
- **Evolução temporal:** um polítropo ou um modelo solar tabelado é uma **fotografia**. O MESA (opção (c)) resolve também a **evolução**: dado $\large M$ e $\large Z$ iniciais, calcula a sequência completa de perfis ao longo do tempo, e isso seria o que permitiria mostrar como o interior de uma gigante RGB difere do de uma RC.

**Armadilha final.** Uma visualização bonita de interior estelar **dá a impressão** de que conhecemos o interior com a mesma certeza que o exterior. Não conhecemos. O que sabemos bem vem da física de equilíbrio e de ferramentas como a sismologia; o resto são modelos calibrados. Rotular a figura da Fase 07 como "ilustração didática de um modelo 1D" é a forma correta de não afirmar mais do que se sabe.

---

Fim da trilogia. Pontos de contato entre os arquivos: a lei de Stefan-Boltzmann do arquivo 01 conecta HR e Kiel; as ferramentas de interpretação do arquivo 02 são o que permite verificar se um classificador do Trilho B aprendeu a física descrita aqui.
