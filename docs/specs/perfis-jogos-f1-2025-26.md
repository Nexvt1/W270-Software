# Especificação Técnica: Padronização em Dezenas dos Perfis e Perfil F1 2025/2026 (400°)

## 1. Visão Geral e Objetivo
O objetivo desta funcionalidade é padronizar todos os valores numéricos dos perfis de jogos e simuladores do volante PCYES W270 exclusivamente em múltiplos inteiros de 10 (`10, 20, 30, 40, 50, 60, 70, 80, 90, 100`, com `0` apenas para desativação/origem) e introduzir o novo perfil oficial para **F1 2025 / 2026** com rotação de direção fixada em **400°**.

## 2. Arquitetura e Componentes
- **Camada de Perfis (`profiles/*.json` e `profile_manager.py`):**
  - Todos os 23 perfis (`DEFAULT_PROFILES` e arquivos individuais JSON) contêm valores inteiros estritamente arredondados em escala decimal de 10 para `ffb`, `spring`, `damping`, `friction`, `inertia`, `roadSensitivity` e pontos das curvas Bézier de pedais (`accChart`, `brakeChart`, `clutchChart`).
  - Criação do perfil `f1_25_26.json` com identificador `f1_25_26`, `angle: 400`, `ffb: 80` (2.56 Nm) e dinâmicas físicas otimizadas.
- **Camada de Protocolo (`wheel_protocol.py`):**
  - Curvas de fallback de pedais (`acc_chart`, `brake_chart`, `clutch_chart`) alinhadas com pontos `[[0, 0], [30, 30], [70, 70], [100, 100]]`.
- **Interface Gráfica (`gui/index.html` e `gui/js/app.js`):**
  - Sliders de FFB, mola, amortecimento, fricção, inércia e pontos de pedal ajustados com `step="10"`.
  - Inclusão do botão de preset rápido de **400° (F1 2025/26)** na aba Volante.
  - Ajuste das pílulas de força de FFB para múltiplos de 10 (`20%`, `50%`, `70%`, `80%`, `100%`).
  - Associação e enquadramento da arte de capa oficial do **EA SPORTS F1 25 / 2026 Season Pack** em `gui/assets/games/f1_25_26.jpg` (460x215 px).

## 3. Fluxo de Execução
1. **Inicialização:** `ProfileManager` carrega e valida os 23 perfis garantindo persistência sem inconsistências decimais.
2. **Seleção de Perfil:** Ao carregar a tela de jogos ou selecionar um jogo, a interface renderiza as especificações em múltiplos de 10 e exibe o crachá angular de 400° para o F1 2025/26.
3. **Aplicação no Hardware:** Ao clicar em *Aplicar*, o comando é empacotado pelo `wheel_protocol` com valores inteiros e enviado via USB DirectInput/BLE aos motores de 3.2 Nm do W270.
4. **Criação de Novos Perfis:** Ao salvar uma personalização pelo modal, as forças e curvas são automaticamente normalizadas com `Math.round(v / 10) * 10`.

## 4. O Porquê das Decisões
- **Múltiplos de 10:** Elimina valores arbitrários (como 15%, 25%, 33%, 35%, 65%, 85%), proporcionando precisão tátil, clareza visual e eliminando micro-flutuações imperceptíveis nos atuadores do volante.
- **Ângulo de 400° para F1 25/26:** Atende às configurações de regulamento e geometria de esterço dos novos monopostos de Fórmula 1, permitindo contorno rápido sem cruzamento de braços e sem zonas mortas.
- **Step 10 na UI:** Garante que qualquer ajuste manual realizado pelo usuário permaneça em harmonia com a regra de dezenas inteiras.

## 5. Pontos de Atenção e Evoluções Futuras
- O perfil clássico `f1_24` (360°) foi mantido e também padronizado para permitir alternância entre as eras da categoria.
- Caso o usuário utilize o Content Manager ou configurações in-game de outros simuladores, recomenda-se manter a linearidade em 100% para preservar as curvas configuradas no aplicativo.
