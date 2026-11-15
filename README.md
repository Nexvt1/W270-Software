# 🏎️ PCYES W270 Control Center - POWER THE GAME

Aplicativo oficial desktop para PC Windows desenvolvido sob medida para o volante **PCYES W270 Force Feedback 3.2Nm 1080°** (baseado na engenharia reversa do app móvel oficial e integrado com a identidade visual da [PCYES](https://www.pcyes.com.br/)).

---

## ⚡ Recursos Principais do PCYES W270 Hub:

- **Design Oficial PCYES Gaming:**
  - Identidade visual escura com detalhes em fibra de carbono, vermelho característico da PCYES (`#e30613`) e tipografia gamer moderna.
  - Exibição de status de hardware em tempo real: **3.2 Nm Dual Motor**, **1080° de Rotação**, **Sensores Magnéticos Hall nos Pedais** e **Câmbio 6+1**.
- **Seletor Rápido de Modos (D-Input / X-Input):**
  - Alternância imediata com 1 clique no topo entre o modo **PC DirectInput** (para simuladores profissionais) e **Modo X-Input** (reconhecido como controle Xbox, ideal para jogos sem suporte nativo a volante como Need for Speed).
- **Ângulo Ajustável até 1080°:**
  - Ajuste por slider de 10 em 10 graus de **90° até 1080°**, além de atalhos rápidos (**270°**, **360°**, **540°**, **900°** e **1080°**).
- **Força do Motor Duplo (3.2 Nm) & Efeitos:**
  - Força Geral do Force Feedback (0-100%).
  - Inversão de Direção do FFB (FFB Reverse).
  - Mola de Centralização (Centering Spring).
  - Amortecimento Hidráulico (Damping).
  - Fricção Mecânica (Friction).
  - Inércia da Caixa de Direção (Inertia).
- **Curvas de Pedais com 4 Estágios:**
  - Curvas Bézier interativas para Acelerador, Freio e Embreagem.
  - Presets: Linear (1:1), Competição, Conforto e Agressivo.
- **Módulo de Câmbio H-Pattern 6+1:**
  - Monitoramento das 6 marchas + Ré com trava física.
  - Detecção da chave de **Freio de Mão (Botão 25)** e do **Seletor de Caixa Alta/Baixa (Botão 26)** para simulação de caminhões de 12 a 18 marchas.
- **Diagnóstico & Telemetria em 60 FPS:**
  - Rotação virtual do volante em tempo real sincronizada com o volante físico.
  - Barras animadas de pressão dos pedais.
  - Matriz de teste dos 18 botões físicos.

---

## 🎮 Jogos com Guias Nativos Pré-Configurados:

Para jogos que oficialmente **não possuem suporte nativo ou perfil pronto para o PCYES W270**, o aplicativo inclui configurações de FFB/rotação otimizadas e o passo a passo de como configurar no menu de cada jogo:

1. **BeamNG.drive:** Instruções de vinculação do Eixo 0, linearidade 1.0 e desativação de mola duplicada.
2. **Forza Horizon 5 & Forza Motorsport:** Guia de criação do Perfil de Roda Personalizado, inversão de FFB e escala mecânica.
3. **Assetto Corsa & Competizione:** Ganho ótimo de 75-80% para evitar clipping dos 3.2 Nm e desativação de subesterço artificial.
4. **Automobilista 2 (AMS2) / Project CARS 2:** Tipo 'Custom Wheel', ganho 75%, Low Force Boost 12%.
5. **CarX Drift Racing Online:** Assistência de direção desligada, suavização 0.25 para contraesterço rápido de drift e chave de freio de mão mapeada.
6. **Need for Speed (Unbound / Heat):** Alternância automática para Modo X-Input (o jogo reconhece nativamente com botões e pedais mapeados).
7. **City Car Driving:** Rotação completa de 1080°, embreagem manual com ponto de mordida e setas no aro.
8. **Euro Truck Simulator 2 / American Truck:** 1080°, layout de câmbio Range/Splitter com o botão 26 do câmbio W270.
9. **Dirt Rally 2.0 / EA SPORTS WRC:** Giro a 540°, saturação 100% e retorno rápido de cascalho.
10. **F1 23 / F1 24:** Giro rápido a 360° para curvas de Mônaco sem tirar as mãos do volante.
11. **SnowRunner / MudRunner:** Amortecimento reforçado para lama e atoleiros pesados.
12. **Padrão de Fábrica:** Calibração neutra recomendada.

---

## 🚀 Como Executar

Dê um duplo-clique no arquivo:
👉 **`iniciar.bat`** (ou execute `python main.py` no terminal).
