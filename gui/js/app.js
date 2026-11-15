/**
 * PCYES W270 Control Center - Frontend Application Logic
 * Comunicação direta com o backend Python via PyWebView (window.pywebview.api)
 * Cálculo em tempo real de Newtons-metro (Nm) para o motor duplo de 3.2 Nm do W270.
 */

const MAX_W270_TORQUE_NM = 3.2; // Capacidade total de pico dos motores duplos do PCYES W270

// Estado global do volante
let currentWheelState = {
  angle: 900,
  ffb: 70, // 70% = 2.24 Nm
  ffbReverse: false,
  spring: 60,
  damping: 60,
  friction: 70,
  inertia: 70,
  mode: 1, // 1 = D-Input, 2 = X-Input
  accChart: [[0, 0], [33, 33], [66, 66], [100, 100]],
  brakeChart: [[0, 0], [33, 33], [66, 66], [100, 100]],
  clutchChart: [[0, 0], [33, 33], [66, 66], [100, 100]],
  keymap: {}
};

let activePedal = 'acc'; // 'acc', 'brake', 'clutch'
let isTestModeActive = false;
let testPollInterval = null;
let peakLiveTorque = 0.0;

// Monitoramento Térmico e Pop-up de Segurança PCYES W270
let thermalAlertActive = false;
let thermalAlertMutedUntil = 0;

function triggerThermalAlert(temp) {
  const modal = document.getElementById('thermalAlertModal');
  const degEl = document.getElementById('modalTempDeg');
  if (degEl) degEl.textContent = `${Math.round(temp || 62)}°C`;
  if (modal) modal.classList.add('active');
  thermalAlertActive = true;
}

function dismissThermalAlert() {
  const modal = document.getElementById('thermalAlertModal');
  if (modal) modal.classList.remove('active');
  thermalAlertActive = false;
  thermalAlertMutedUntil = Date.now() + 60000; // Silencia pop-up por 60s
  showToast("Alerta dispensado. Fique atento à temperatura no cabeçalho.");
}

async function applySafeThermalMode() {
  const modal = document.getElementById('thermalAlertModal');
  if (modal) modal.classList.remove('active');
  thermalAlertActive = false;
  thermalAlertMutedUntil = Date.now() + 120000; // Silencia por 2 minutos

  // Reduz FFB protetivamente para 40% (1.28 Nm)
  updateFfbSlider(40);

  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.set_ffb(40, currentWheelState.ffbReverse);
    } catch (e) {}
  }

  showToast("Modo de Segurança ativado! Torque reduzido para 40% (1.28 Nm) para resfriar os motores.", "success");
}

// Nomes oficiais dos 18 botões físicos do aro do W270
const BUTTON_LIST = [
  { id: 10, name: "A / Cruz (Botão 1)" },
  { id: 9,  name: "B / Círculo (Botão 2)" },
  { id: 11, name: "X / Quadrado (Botão 3)" },
  { id: 8,  name: "Y / Triângulo (Botão 4)" },
  { id: 12, name: "Borboleta Esq (L1 / LB)" },
  { id: 13, name: "Borboleta Dir (R1 / RB)" },
  { id: 14, name: "L2 / LT (Gatilho Esq)" },
  { id: 15, name: "R2 / RT (Gatilho Dir)" },
  { id: 1,  name: "L3 (Analógico Esq)" },
  { id: 2,  name: "R3 (Analógico Dir)" },
  { id: 4,  name: "D-Pad Cima" },
  { id: 6,  name: "D-Pad Baixo" },
  { id: 7,  name: "D-Pad Esquerda" },
  { id: 5,  name: "D-Pad Direita" },
  { id: 0,  name: "View / Back" },
  { id: 3,  name: "Menu / Start" },
  { id: 16, name: "Home / Guia" },
  { id: 17, name: "Share / Capture" },
  { id: 25, name: "Freio de Mão (Câmbio)" },
  { id: 26, name: "Caixa Alta/Baixa (Câmbio)" },
];

document.addEventListener('DOMContentLoaded', () => {
  initButtonMappingUI();
  initTestMatrixUI();
  renderPedalChart();
  updateFfbSlider(currentWheelState.ffb);
  startStatusWatcher();
  loadGamesGuide();
});

// Troca de Abas
function switchTab(tabName) {
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));

  const navItems = document.querySelectorAll('.nav-item');
  const tabs = ['wheel', 'pedals', 'shifter', 'mapping', 'games', 'test', 'calibrate'];
  const idx = tabs.indexOf(tabName);
  if (idx !== -1 && navItems[idx]) {
    navItems[idx].classList.add('active');
  }

  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) {
    targetTab.classList.add('active');
  }

  if (tabName === 'test' || tabName === 'calibrate') {
    if (!isTestModeActive) {
      toggleTestMode();
    }
    if (tabName === 'calibrate') {
      loadCalibrationData();
    }
  } else if (tabName === 'games') {
    loadGamesGuide();
  }
}

// Watcher de Conexão com o W270
function startStatusWatcher() {
  setInterval(async () => {
    if (window.pywebview && window.pywebview.api) {
      try {
        const st = await window.pywebview.api.get_connection_status();
        updateConnectionBadge(st.connected, st.device_name);

        // Se não estiver com a telemetria de 60fps aberta, atualiza a temperatura no topo a cada 1.2s
        if (!isTestModeActive) {
          const wheelState = await window.pywebview.api.get_wheel_state();
          let temp = typeof wheelState.temperature === 'number' ? wheelState.temperature : 23.0;
          let tempColor = temp >= 60 ? "#ff1744" : (temp >= 45 ? "#ffea00" : "#00e676");
          let tempStatus = temp >= 60 ? "Quente!" : (temp >= 45 ? "Aquecendo" : "Normal");
          const hTemp = document.getElementById('headerTemp');
          const hStatus = document.getElementById('headerTempStatus');
          if (hTemp) {
            hTemp.textContent = `${temp.toFixed(1)}°C`;
            hTemp.style.color = tempColor;
          }
          if (hStatus) {
            hStatus.textContent = `/ ${tempStatus}`;
          }

          // Disparo automático do pop-up se esquentar mesmo fora da aba de teste
          if (temp >= 60) {
            if (!thermalAlertActive && Date.now() > thermalAlertMutedUntil) {
              triggerThermalAlert(temp);
            }
          } else if (temp < 55) {
            thermalAlertMutedUntil = 0;
          }
        }
      } catch (e) {}
    }
  }, 1200);
}

function updateConnectionBadge(connected, name) {
  const dot = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  const btn = document.getElementById('btnConnect');

  if (connected) {
    dot.classList.add('connected');
    text.textContent = `${name || "PCYES W270"} (Conectado)`;
    btn.textContent = "Desconectar";
  } else {
    dot.classList.remove('connected');
    text.textContent = name || "PCYES W270 Desconectado";
    btn.textContent = "Conectar";
  }
}

async function toggleConnect() {
  if (!window.pywebview || !window.pywebview.api) return;
  const st = await window.pywebview.api.get_connection_status();
  if (st.connected) {
    await window.pywebview.api.disconnect_device();
    showToast("Volante W270 desconectado.");
  } else {
    showToast("Procurando PCYES W270 via Bluetooth LE...");
    await window.pywebview.api.connect_device();
  }
}

async function toggleMode() {
  currentWheelState.mode = currentWheelState.mode === 1 ? 2 : 1;
  const btn = document.getElementById('btnMode');
  if (currentWheelState.mode === 1) {
    btn.textContent = "Modo: PC (D-Input)";
    btn.style.borderColor = "var(--pcyes-red)";
  } else {
    btn.textContent = "Modo: PC (X-Input)";
    btn.style.borderColor = "var(--accent-cyan)";
  }
  if (window.pywebview && window.pywebview.api) {
    await window.pywebview.api.switch_mode(currentWheelState.mode);
  }
  showToast(`Modo alterado para ${btn.textContent}`, "success");
}

async function resetToFactory() {
  if (confirm("Deseja restaurar as configurações padrão originais do PCYES W270?")) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.reset_wheel();
    }
    showToast("Configurações padrão do W270 restauradas!", "success");
    setTimeout(syncUIWithDeviceState, 600);
  }
}

async function syncUIWithDeviceState() {
  if (!window.pywebview || !window.pywebview.api) return;
  try {
    const data = await window.pywebview.api.get_wheel_state();
    if (data) {
      if (data.angle) updateAngleSlider(data.angle);
      if (data.ffb !== undefined) updateFfbSlider(data.ffb);
      if (data.ffbReverse !== undefined) {
        document.getElementById('switchFfbReverse').checked = data.ffbReverse;
        currentWheelState.ffbReverse = data.ffbReverse;
      }
      if (data.spring !== undefined) document.getElementById('sliderSpring').value = data.spring;
      if (data.damping !== undefined) document.getElementById('sliderDamping').value = data.damping;
      if (data.friction !== undefined) document.getElementById('sliderFriction').value = data.friction;
      if (data.inertia !== undefined) document.getElementById('sliderInertia').value = data.inertia;
      updateForceLabels();
    }
  } catch (e) {
    console.error("Erro ao sincronizar com W270:", e);
  }
}

// Controles de Volante
function updateAngleSlider(val) {
  val = parseInt(val);
  currentWheelState.angle = val;
  document.getElementById('sliderAngle').value = val;
  document.getElementById('valAngle').textContent = `${val}°`;

  document.querySelectorAll('.preset-pills .pill').forEach(p => p.classList.remove('active'));
  if (val === 900) {
    const p900 = document.getElementById('pill900');
    if (p900) p900.classList.add('active');
  }
}

function setAnglePreset(degrees) {
  updateAngleSlider(degrees);
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_angle(degrees);
    showToast(`Ângulo do W270 ajustado para ${degrees}°`, "success");
  }
}

// Cálculo e Atualização Dinâmica de Newtons-metro (Nm)
function updateFfbSlider(val) {
  val = parseInt(val);
  currentWheelState.ffb = val;
  
  // Cálculo exato: % de 3.2 Nm
  const nm = (val / 100.0) * MAX_W270_TORQUE_NM;

  // Atualiza slider e rótulo com porcentagem e Nm
  document.getElementById('sliderFfb').value = val;
  document.getElementById('valFfb').textContent = `${val}% • ${nm.toFixed(2)} Nm`;

  // Atualiza Widget de Torque na Aba Volante
  const widgetVal = document.getElementById('widgetTorqueVal');
  const widgetFill = document.getElementById('widgetTorqueFill');
  const widgetClip = document.getElementById('widgetClipStatus');
  if (widgetVal) widgetVal.textContent = nm.toFixed(2);
  if (widgetFill) widgetFill.style.width = `${val}%`;

  // Indicador de Clipping / Sobrecarga
  if (widgetClip) {
    if (val >= 90) {
      widgetClip.textContent = "Alto / Risco de Clip";
      widgetClip.className = "clip-badge clipping";
    } else {
      widgetClip.textContent = "Faixa Ideal";
      widgetClip.className = "clip-badge";
    }
  }

  // Atualiza Badge de Torque no Cabeçalho
  const headerTorque = document.getElementById('headerTorque');
  if (headerTorque) headerTorque.textContent = `${nm.toFixed(2)} Nm`;

  // Atualiza Especificações na Barra Lateral
  const sidebarTorque = document.getElementById('sidebarTorque');
  if (sidebarTorque) sidebarTorque.textContent = `${nm.toFixed(2)} Nm (${val}%)`;

  // Atualiza pills ativas
  ['pillFfb70'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('active', val === 70);
  });
}

function setFfbPreset(percent) {
  updateFfbSlider(percent);
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_ffb(percent, currentWheelState.ffbReverse);
    const nm = (percent / 100.0) * MAX_W270_TORQUE_NM;
    showToast(`Força ajustada para ${nm.toFixed(2)} Nm (${percent}%)`, "success");
  }
}

function toggleFfbReverse(checked) {
  currentWheelState.ffbReverse = checked;
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_ffb(currentWheelState.ffb, checked);
  }
  showToast(checked ? "Force Feedback Invertido (Ativado)" : "Force Feedback Normal (Desativado)");
}

function updateForceSlider() {
  currentWheelState.spring = parseInt(document.getElementById('sliderSpring').value);
  currentWheelState.damping = parseInt(document.getElementById('sliderDamping').value);
  currentWheelState.friction = parseInt(document.getElementById('sliderFriction').value);
  currentWheelState.inertia = parseInt(document.getElementById('sliderInertia').value);
  updateForceLabels();
}

function updateForceLabels() {
  document.getElementById('valSpring').textContent = `${document.getElementById('sliderSpring').value}%`;
  document.getElementById('valDamping').textContent = `${document.getElementById('sliderDamping').value}%`;
  document.getElementById('valFriction').textContent = `${document.getElementById('sliderFriction').value}%`;
  document.getElementById('valInertia').textContent = `${document.getElementById('sliderInertia').value}%`;
}

async function saveCurrentWheelSettings() {
  if (window.pywebview && window.pywebview.api) {
    await window.pywebview.api.set_angle(currentWheelState.angle);
    await window.pywebview.api.set_ffb(currentWheelState.ffb, currentWheelState.ffbReverse);
    await window.pywebview.api.set_force(
      currentWheelState.spring,
      currentWheelState.damping,
      currentWheelState.friction,
      currentWheelState.inertia
    );
    const nm = (currentWheelState.ffb / 100.0) * MAX_W270_TORQUE_NM;
    showToast(`Configurações gravadas! Torque ativo: ${nm.toFixed(2)} Nm`, "success");
  }
}

// Pedais com Sensores Hall
function selectPedal(pedalType) {
  activePedal = pedalType;
  document.getElementById('btnPedalAcc').className = pedalType === 'acc' ? 'btn btn-primary' : 'btn';
  document.getElementById('btnPedalBrake').className = pedalType === 'brake' ? 'btn btn-primary' : 'btn';
  document.getElementById('btnPedalClutch').className = pedalType === 'clutch' ? 'btn btn-primary' : 'btn';

  const chartKey = `${pedalType}Chart`;
  const chartData = currentWheelState[chartKey] || [[0, 0], [33, 33], [66, 66], [100, 100]];

  for (let i = 0; i < 4; i++) {
    const val = chartData[i][1];
    document.getElementById(`sliderPt${i}`).value = val;
    document.getElementById(`valPt${i}`).textContent = `${val}%`;
  }
  renderPedalChart();
}

function updatePedalPoint(ptIndex, val) {
  val = parseInt(val);
  const chartKey = `${activePedal}Chart`;
  if (!currentWheelState[chartKey]) {
    currentWheelState[chartKey] = [[0, 0], [33, 33], [66, 66], [100, 100]];
  }
  currentWheelState[chartKey][ptIndex][1] = val;
  document.getElementById(`valPt${ptIndex}`).textContent = `${val}%`;
  renderPedalChart();
}

function renderPedalChart() {
  const chartKey = `${activePedal}Chart`;
  const pts = currentWheelState[chartKey] || [[0, 0], [33, 33], [66, 66], [100, 100]];

  const mapX = (v) => 30 + (v / 100) * 250;
  const mapY = (v) => 170 - (v / 100) * 150;

  const p0 = [mapX(pts[0][0]), mapY(pts[0][1])];
  const p1 = [mapX(pts[1][0]), mapY(pts[1][1])];
  const p2 = [mapX(pts[2][0]), mapY(pts[2][1])];
  const p3 = [mapX(pts[3][0]), mapY(pts[3][1])];

  ['pt0', 'pt1', 'pt2', 'pt3'].forEach((id, i) => {
    const c = document.getElementById(id);
    const p = [p0, p1, p2, p3][i];
    if (c) {
      c.setAttribute('cx', p[0]);
      c.setAttribute('cy', p[1]);
    }
  });

  const d = `M ${p0[0]} ${p0[1]} C ${p1[0]} ${p1[1]}, ${p2[0]} ${p2[1]}, ${p3[0]} ${p3[1]}`;
  const path = document.getElementById('pedalCurvePath');
  if (path) {
    path.setAttribute('d', d);
  }
}

function applyPedalPreset(presetName) {
  let pts;
  if (presetName === 'linear') {
    pts = [[0, 0], [33, 33], [66, 66], [100, 100]];
  } else if (presetName === 'compete') {
    pts = [[0, 0], [20, 15], [55, 65], [100, 100]];
  } else if (presetName === 'comfort') {
    pts = [[0, 0], [35, 25], [70, 60], [100, 100]];
  } else if (presetName === 'aggressive') {
    pts = [[0, 0], [30, 45], [60, 80], [100, 100]];
  }

  const chartKey = `${activePedal}Chart`;
  currentWheelState[chartKey] = pts;
  selectPedal(activePedal);
  showToast(`Preset ${presetName.toUpperCase()} aplicado aos pedais.`);
}

async function saveCurrentPedalSettings() {
  if (window.pywebview && window.pywebview.api) {
    await window.pywebview.api.apply_profile({
      accChart: currentWheelState.accChart,
      brakeChart: currentWheelState.brakeChart,
      clutchChart: currentWheelState.clutchChart
    });
    showToast("Curvas de pedais gravadas com sucesso no W270!", "success");
  }
}

// Mapeamento dos 18 Botões
function initButtonMappingUI() {
  const container = document.getElementById('mappingContainer');
  if (!container) return;
  container.innerHTML = '';

  BUTTON_LIST.forEach(btn => {
    const div = document.createElement('div');
    div.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:10px; background:var(--bg-input); border-radius:var(--radius-xs); border:1px solid var(--border-card);";

    const label = document.createElement('span');
    label.style.fontWeight = '700';
    label.style.fontSize = '12px';
    label.textContent = btn.name;

    const select = document.createElement('select');
    select.style.cssText = "background:#0a0c10; color:#fff; border:1px solid var(--border-subtle); border-radius:4px; padding:4px 8px; font-weight:700; outline:none; font-size:12px;";
    select.id = `map-select-${btn.id}`;

    BUTTON_LIST.forEach(opt => {
      const o = document.createElement('option');
      o.value = opt.id;
      o.textContent = opt.name;
      if (opt.id === btn.id) o.selected = true;
      select.appendChild(o);
    });

    select.onchange = (e) => {
      const replaceId = parseInt(e.target.value);
      currentWheelState.keymap[btn.id] = replaceId;
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.set_mapping(btn.id, replaceId);
      }
      showToast(`Mapeado: ${btn.name} ➔ ${BUTTON_LIST.find(b => b.id === replaceId)?.name}`);
    };

    div.appendChild(label);
    div.appendChild(select);
    container.appendChild(div);
  });
}

async function resetKeymap() {
  currentWheelState.keymap = {};
  initButtonMappingUI();
  if (window.pywebview && window.pywebview.api) {
    await window.pywebview.api.reset_wheel();
  }
  showToast("Mapeamento do W270 restaurado ao padrão!");
}

// Matriz de Teste UI
function initTestMatrixUI() {
  const matrix = document.getElementById('testButtonMatrix');
  if (!matrix) return;
  matrix.innerHTML = '';

  BUTTON_LIST.forEach(btn => {
    const el = document.createElement('div');
    el.className = 'btn-indicator';
    el.id = `test-btn-${btn.id}`;
    el.textContent = btn.name.split(' ')[0];
    matrix.appendChild(el);
  });
}

// Telemetria 60 FPS & Medidor Dinâmico de Torque
async function toggleTestMode() {
  isTestModeActive = !isTestModeActive;
  const btn = document.getElementById('btnToggleTest');

  if (isTestModeActive) {
    btn.textContent = "Parar Teste";
    btn.className = "btn btn-cyan";
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.set_test_mode(true);
    }
    startTelemetryLoop();
  } else {
    btn.textContent = "Ativar Teste";
    btn.className = "btn btn-primary";
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.set_test_mode(false);
    }
    stopTelemetryLoop();
  }
}

function startTelemetryLoop() {
  if (testPollInterval) clearInterval(testPollInterval);
  testPollInterval = setInterval(async () => {
    if (!isTestModeActive || !window.pywebview || !window.pywebview.api) return;
    try {
      const data = await window.pywebview.api.get_telemetry();
      if (data) {
        renderLiveTelemetry(data);
      }
    } catch (e) {}
  }, 25); // ~40-60 fps
}

function stopTelemetryLoop() {
  if (testPollInterval) {
    clearInterval(testPollInterval);
    testPollInterval = null;
  }
}

function renderLiveTelemetry(data) {
  const wheelEl = document.getElementById('visualWheel');
  const angleReadout = document.getElementById('readoutAngle');

  let deg = 0;
  let degNorm = 0.0;

  if (data.source === 'usb') {
    const maxHalf = (currentWheelState.angle || 900) / 2.0;
    degNorm = data.wheelAxis || 0;
    deg = degNorm * maxHalf;
  } else {
    const maxHalf = (currentWheelState.angle || 900) / 2.0;
    degNorm = data.angleNorm || 0;
    deg = degNorm * maxHalf;
  }

  if (wheelEl) wheelEl.style.transform = `rotate(${deg}deg)`;
  if (angleReadout) angleReadout.textContent = `${deg > 0 ? '+' : ''}${deg.toFixed(1)}°`;

  // Cálculo Dinâmico de Torque em Tempo Real:
  // Conforme o volante desvia do centro ou reage à mola e forças, calcula os Nm instantâneos
  const ffbFactor = (currentWheelState.ffb || 70) / 100.0;
  const liveNm = Math.min(MAX_W270_TORQUE_NM * ffbFactor, Math.abs(degNorm) * MAX_W270_TORQUE_NM * ffbFactor * 1.1);

  if (liveNm > peakLiveTorque) {
    peakLiveTorque = liveNm;
  }

  const liveTorqueEl = document.getElementById('liveTorqueNm');
  const peakTorqueEl = document.getElementById('peakTorqueNm');
  if (liveTorqueEl) liveTorqueEl.textContent = `${liveNm.toFixed(2)} Nm`;
  if (peakTorqueEl) peakTorqueEl.textContent = `${peakLiveTorque.toFixed(2)} Nm`;

  // Temperatura dos motores duplos de 3.2 Nm calculada dinamicamente via telemetria física
  let currentTemp = typeof data.temperature === 'number' ? data.temperature : 23.0;

  let tempColor = "#00e676"; // Verde normal (< 45°C)
  let tempStatusText = "Normal";
  let tempFullStatus = "Motor Normal";
  if (currentTemp >= 60) {
    tempColor = "#ff1744"; // Vermelho crítico (>= 60°C)
    tempStatusText = "Quente!";
    tempFullStatus = "Alerta Térmico";
  } else if (currentTemp >= 45) {
    tempColor = "#ffea00"; // Amarelo alerta (45-59°C)
    tempStatusText = "Aquecendo";
    tempFullStatus = "Carga Alta";
  }

  // Atualiza widgets no topo (Header)
  const headerTemp = document.getElementById('headerTemp');
  const headerTempStatus = document.getElementById('headerTempStatus');
  if (headerTemp) {
    headerTemp.textContent = `${currentTemp.toFixed(1)}°C`;
    headerTemp.style.color = tempColor;
  }
  if (headerTempStatus) {
    headerTempStatus.textContent = `/ ${tempStatusText}`;
  }

  // Atualiza medidor na aba de Telemetria
  const liveTempNm = document.getElementById('liveTempNm');
  const liveTempStatus = document.getElementById('liveTempStatus');
  const liveTempIcon = document.getElementById('liveTempIcon');
  if (liveTempNm) {
    liveTempNm.textContent = `${currentTemp.toFixed(1)}°C`;
    liveTempNm.style.color = tempColor;
  }
  if (liveTempStatus) {
    liveTempStatus.textContent = tempFullStatus;
  }
  if (liveTempIcon) {
    liveTempIcon.style.fill = tempColor;
  }

  // Disparo automático do Pop-up de Alerta Térmico em Telemetria (>= 60°C)
  if (currentTemp >= 60) {
    if (!thermalAlertActive && Date.now() > thermalAlertMutedUntil) {
      triggerThermalAlert(currentTemp);
    }
  } else if (currentTemp < 55) {
    thermalAlertMutedUntil = 0;
  }

  // Pedais
  const accVal = data.source === 'usb' ? data.accPercent : Math.round((data.acc || 0) / 2.55);
  const brakeVal = data.source === 'usb' ? data.brakePercent : Math.round((data.brake || 0) / 2.55);
  const clutchVal = data.source === 'usb' ? data.clutchPercent : Math.round((data.clutch || 0) / 2.55);

  document.getElementById('barAcc').style.height = `${accVal}%`;
  document.getElementById('valAcc').textContent = `${Math.round(accVal)}%`;

  document.getElementById('barBrake').style.height = `${brakeVal}%`;
  document.getElementById('valBrake').textContent = `${Math.round(brakeVal)}%`;

  document.getElementById('barClutch').style.height = `${clutchVal}%`;
  document.getElementById('valClutch').textContent = `${Math.round(clutchVal)}%`;

  const gear = data.gear || "N";
  const readoutGear = document.getElementById('readoutGear');
  if (readoutGear) readoutGear.textContent = gear;

  ['1', '2', '3', '4', '5', '6', 'r', 'n'].forEach(g => {
    const el = document.getElementById(`gear-${g}`);
    if (el) {
      if (gear.toLowerCase() === g) el.classList.add('active');
      else el.classList.remove('active');
    }
    // Mostrador de marchas na aba de Calibração
    const gate = document.getElementById(`shifterGate-${g}`);
    if (gate) {
      if (gear.toLowerCase() === g) gate.classList.add('active');
      else gate.classList.remove('active');
    }
  });

  // Atualização em Tempo Real na Aba de Calibração
  const calibWheelEl = document.getElementById('calibVisualWheel');
  const calibAngleReadout = document.getElementById('calibAngleReadout');
  const calibRawWheelEl = document.getElementById('calibRawWheel');
  if (calibWheelEl) calibWheelEl.style.transform = `rotate(${deg}deg)`;
  if (calibAngleReadout) calibAngleReadout.textContent = `${deg > 0 ? '+' : ''}${deg.toFixed(1)}°`;
  if (calibRawWheelEl) {
    const rawW = data.rawWheelAxis !== undefined ? data.rawWheelAxis : degNorm;
    calibRawWheelEl.textContent = (rawW >= 0 ? '+' : '') + Number(rawW).toFixed(4);
  }

  // Pedais na aba de Calibração
  const calibBarAcc = document.getElementById('calibBarAcc');
  const calibValAcc = document.getElementById('calibValAcc');
  const calibRawAcc = document.getElementById('calibRawAcc');
  if (calibBarAcc) calibBarAcc.style.height = `${accVal}%`;
  if (calibValAcc) calibValAcc.textContent = `${Math.round(accVal)}%`;
  if (calibRawAcc) calibRawAcc.textContent = Number(data.rawAcc !== undefined ? data.rawAcc : 0).toFixed(4);

  const calibBarBrake = document.getElementById('calibBarBrake');
  const calibValBrake = document.getElementById('calibValBrake');
  const calibRawBrake = document.getElementById('calibRawBrake');
  if (calibBarBrake) calibBarBrake.style.height = `${brakeVal}%`;
  if (calibValBrake) calibValBrake.textContent = `${Math.round(brakeVal)}%`;
  if (calibRawBrake) calibRawBrake.textContent = Number(data.rawBrake !== undefined ? data.rawBrake : 0).toFixed(4);

  const calibBarClutch = document.getElementById('calibBarClutch');
  const calibValClutch = document.getElementById('calibValClutch');
  const calibRawClutch = document.getElementById('calibRawClutch');
  if (calibBarClutch) calibBarClutch.style.height = `${clutchVal}%`;
  if (calibValClutch) calibValClutch.textContent = `${Math.round(clutchVal)}%`;
  if (calibRawClutch) calibRawClutch.textContent = Number(data.rawClutch !== undefined ? data.rawClutch : 0).toFixed(4);

  lastTelemetryData = data;

  // Botões e switches do W270
  if (data.buttons) {
    if (Array.isArray(data.buttons)) {
      data.buttons.forEach((pressed, i) => {
        const el = document.getElementById(`test-btn-${i}`);
        if (el) {
          if (pressed) el.classList.add('active');
          else el.classList.remove('active');
        }
      });
      // Handbrake (Botão 25)
      const hb = document.getElementById('ind-handbrake');
      if (hb && data.buttons[25] !== undefined) {
        if (data.buttons[25]) {
          hb.textContent = "PUXADO (ATIVO)";
          hb.classList.add('active');
        } else {
          hb.textContent = "Desacionado";
          hb.classList.remove('active');
        }
      }
      // Range Splitter (Botão 26)
      const range = document.getElementById('ind-range');
      if (range && data.buttons[26] !== undefined) {
        if (data.buttons[26]) {
          range.textContent = "CAIXA ALTA (7ª a 12ª)";
          range.classList.add('active');
        } else {
          range.textContent = "Caixa Baixa (1ª a 6ª)";
          range.classList.remove('active');
        }
      }
    } else {
      Object.keys(data.buttons).forEach(k => {
        const pressed = data.buttons[k];
        const el = document.getElementById(`test-btn-${k}`);
        if (el) {
          if (pressed) el.classList.add('active');
          else el.classList.remove('active');
        }
      });
    }
  }
}

// ================= JOGOS & GUIAS NATIVOS =================
async function loadGamesGuide() {
  if (!window.pywebview || !window.pywebview.api) return;
  const grid = document.getElementById('gamesGuideGrid');
  if (!grid) return;
  grid.innerHTML = '<div style="color:var(--text-muted)">Carregando jogos e configurações nativas...</div>';

  try {
    const profiles = await window.pywebview.api.list_profiles();
    grid.innerHTML = '';

    profiles.forEach(p => {
      const card = document.createElement('div');
      card.className = 'game-card';

      const tipsHtml = (p.in_game_tips || []).map(tip => `<li>${tip}</li>`).join('');
      const gameNm = ((p.ffb || 70) / 100.0) * MAX_W270_TORQUE_NM;

      card.innerHTML = `
        <div class="game-card-header">
          <div>
            <div class="game-title">${p.name}</div>
            <div class="game-category">${p.category || p.game}</div>
          </div>
          <span class="btn-indicator" style="font-size:12px; border-color:var(--pcyes-red); color:#fff; background:var(--pcyes-red);">${p.angle}°</span>
        </div>

        <div class="game-specs-strip">
          <span>Rotação: <strong>${p.angle}°</strong></span> &bull;
          <span>Torque: <strong style="color:var(--pcyes-red);">${gameNm.toFixed(2)} Nm (${p.ffb}%)</strong></span> &bull;
          <span>Modo: <strong>${p.mode_required || "D-Input"}</strong></span>
        </div>

        <div style="font-size:12.5px; color:#cbd5e1;">${p.description || ""}</div>

        <div class="game-guide-box">
          <div style="font-weight:800; color:var(--accent-cyan); display:flex; align-items:center; gap:6px;">
            <svg style="width:14px; height:14px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            Guia de Configuração no Jogo (Sem Suporte Oficial):
          </div>
          <ul>${tipsHtml}</ul>
        </div>

        <div style="display:flex; gap:10px; margin-top:8px;">
          <button class="btn btn-primary" style="flex:1;" onclick="applyProfile('${p.id}')">
            ⚡ Aplicar ${gameNm.toFixed(2)} Nm no W270
          </button>
          <button class="btn" onclick="exportProfile('${p.id}')">Exportar</button>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = `<div style="color:var(--pcyes-red)">Erro ao carregar lista de jogos: ${e}</div>`;
  }
}

async function applyProfile(profileId) {
  if (!window.pywebview || !window.pywebview.api) return;
  showToast("Gravando configurações no PCYES W270...");
  const success = await window.pywebview.api.apply_profile_by_id(profileId);
  if (success) {
    showToast(`Perfil aplicado com sucesso no W270!`, "success");
    syncUIWithDeviceState();
  } else {
    showToast("Erro ao gravar perfil no volante.", "error");
  }
}

async function showSaveProfileModal() {
  const name = prompt("Nome do jogo ou simulador (Ex: Assetto Corsa EVO):");
  if (!name) return;

  const category = prompt("Categoria (Ex: Drift, GT3, Rally):") || "Simulação";
  const profile = {
    id: name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
    name: name,
    game: name,
    category: category,
    description: "Configuração nativa personalizada para PCYES W270.",
    angle: currentWheelState.angle,
    ffb: currentWheelState.ffb,
    ffbReverse: currentWheelState.ffbReverse,
    spring: currentWheelState.spring,
    damping: currentWheelState.damping,
    friction: currentWheelState.friction,
    inertia: currentWheelState.inertia,
    accChart: currentWheelState.accChart,
    brakeChart: currentWheelState.brakeChart,
    clutchChart: currentWheelState.clutchChart,
    in_game_tips: [
      "Perfil criado pelo usuário.",
      "Ajuste a sensibilidade de direção no jogo para 100% linear."
    ],
    keymap: currentWheelState.keymap
  };

  if (window.pywebview && window.pywebview.api) {
    await window.pywebview.api.save_profile(profile);
    showToast(`Perfil "${name}" salvo!`, "success");
    loadGamesGuide();
  }
}

async function exportProfile(profileId) {
  if (window.pywebview && window.pywebview.api) {
    const res = await window.pywebview.api.export_profile(profileId);
    if (res) showToast(`Perfil exportado com sucesso!`, "success");
  }
}

async function importProfileJson() {
  if (window.pywebview && window.pywebview.api) {
    const res = await window.pywebview.api.import_profile();
    if (res) {
      showToast(`Perfil "${res.name}" importado com sucesso!`, "success");
      loadGamesGuide();
    }
  }
}

// Toast PCYES
let toastTimer = null;
function showToast(msg, type = "normal") {
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toastMsg');
  toastMsg.textContent = msg;

  toast.className = 'toast show';
  if (type === 'success') toast.classList.add('success');
  if (type === 'error') toast.classList.add('error');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.className = 'toast';
  }, 3200);
}

// ================= SISTEMA DE CALIBRAÇÃO PCYES =================
let calibrationState = {
  wheel: { center_offset: 0.0, deadzone_percent: 0.0, min_raw: -1.0, max_raw: 1.0 },
  pedals: {
    acc: { min_raw: 1.0, max_raw: -1.0, deadzone_low: 1.5, deadzone_high: 2.0 },
    brake: { min_raw: 1.0, max_raw: -1.0, deadzone_low: 2.0, deadzone_high: 2.5 },
    clutch: { min_raw: 1.0, max_raw: -1.0, deadzone_low: 2.0, deadzone_high: 2.5 }
  }
};
let lastTelemetryData = {};

async function loadCalibrationData() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const data = await window.pywebview.api.get_calibration();
      if (data) {
        calibrationState = data;
        updateCalibrationUI();
      }
    } catch (e) {
      console.error("Erro ao carregar calibração:", e);
    }
  }
}

function updateCalibrationUI() {
  const offsetEl = document.getElementById('calibOffsetVal');
  if (offsetEl && calibrationState.wheel) {
    const off = calibrationState.wheel.center_offset || 0.0;
    offsetEl.textContent = (off >= 0 ? '+' : '') + Number(off).toFixed(4);
  }

  const sliderDz = document.getElementById('sliderWheelDeadzone');
  const valDz = document.getElementById('valWheelDeadzone');
  if (sliderDz && valDz && calibrationState.wheel) {
    const dz = calibrationState.wheel.deadzone_percent || 0.0;
    sliderDz.value = dz;
    valDz.textContent = `${dz.toFixed(1)}%`;
  }

  if (calibrationState.pedals) {
    ['acc', 'brake', 'clutch'].forEach(p => {
      const pCfg = calibrationState.pedals[p];
      if (pCfg) {
        const pUpper = p.charAt(0).toUpperCase() + p.slice(1);
        const dzEl = document.getElementById(`calib${pUpper}DzLow`);
        if (dzEl) dzEl.textContent = `${(pCfg.deadzone_low || 0).toFixed(1)}%`;
      }
    });
  }
}

async function calibrateCurrentCenter() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const res = await window.pywebview.api.set_wheel_center();
      if (res && res.success) {
        showToast(`Centro 0.0° calibrado com sucesso! (Offset: ${res.offset.toFixed(4)})`, "success");
        await loadCalibrationData();
      }
    } catch (e) {
      showToast("Erro ao calibrar centro do volante.", "error");
    }
  }
}

function updateWheelDeadzone(val) {
  val = parseFloat(val);
  if (!calibrationState.wheel) calibrationState.wheel = {};
  calibrationState.wheel.deadzone_percent = val;
  const valDz = document.getElementById('valWheelDeadzone');
  if (valDz) valDz.textContent = `${val.toFixed(1)}%`;
}

function setPedalMin(pedalName) {
  const rawKey = pedalName === 'acc' ? 'rawAcc' : (pedalName === 'brake' ? 'rawBrake' : 'rawClutch');
  const rawVal = lastTelemetryData[rawKey] !== undefined ? lastTelemetryData[rawKey] : 1.0;
  if (!calibrationState.pedals[pedalName]) calibrationState.pedals[pedalName] = {};
  calibrationState.pedals[pedalName].min_raw = round4(rawVal);
  showToast(`Ponto de repouso (0%) gravado para ${pedalName.toUpperCase()}: ${rawVal.toFixed(4)}`, "success");
}

function setPedalMax(pedalName) {
  const rawKey = pedalName === 'acc' ? 'rawAcc' : (pedalName === 'brake' ? 'rawBrake' : 'rawClutch');
  const rawVal = lastTelemetryData[rawKey] !== undefined ? lastTelemetryData[rawKey] : -1.0;
  if (!calibrationState.pedals[pedalName]) calibrationState.pedals[pedalName] = {};
  calibrationState.pedals[pedalName].max_raw = round4(rawVal);
  showToast(`Ponto de fundo (100%) gravado para ${pedalName.toUpperCase()}: ${rawVal.toFixed(4)}`, "success");
}

function updatePedalDz(pedalName, type, val) {
  val = parseFloat(val);
  if (!calibrationState.pedals[pedalName]) calibrationState.pedals[pedalName] = {};
  if (type === 'low') {
    calibrationState.pedals[pedalName].deadzone_low = val;
    const pUpper = pedalName.charAt(0).toUpperCase() + pedalName.slice(1);
    const dzEl = document.getElementById(`calib${pUpper}DzLow`);
    if (dzEl) dzEl.textContent = `${val.toFixed(1)}%`;
  }
}

async function saveFullCalibration() {
  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.save_calibration(calibrationState);
      showToast("Calibração de Volante e Pedais gravada com sucesso!", "success");
    } catch (e) {
      showToast("Erro ao gravar calibração.", "error");
    }
  }
}

async function resetCalibrationToDefault() {
  if (confirm("Deseja restaurar as calibrações de fábrica do volante e dos pedais?")) {
    if (window.pywebview && window.pywebview.api) {
      try {
        const def = await window.pywebview.api.reset_calibration();
        calibrationState = def;
        updateCalibrationUI();
        showToast("Calibração de fábrica restaurada!", "success");
      } catch (e) {}
    }
  }
}

// Auto-calibração inteligente de pedais durante 5 segundos
let isAutoCalibratingPedals = false;
function startAutoPedalCalib() {
  if (isAutoCalibratingPedals) return;
  isAutoCalibratingPedals = true;
  const btn = document.getElementById('btnAutoCalibPedal');
  if (btn) {
    btn.textContent = "⏳ Pressione todos os pedais a fundo (5s)...";
    btn.style.background = "var(--pcyes-red)";
  }

  const pedalExtremes = {
    acc: { min: 1.0, max: -1.0 },
    brake: { min: 1.0, max: -1.0 },
    clutch: { min: 1.0, max: -1.0 }
  };

  const timer = setInterval(() => {
    if (lastTelemetryData) {
      ['acc', 'brake', 'clutch'].forEach(p => {
        const k = p === 'acc' ? 'rawAcc' : (p === 'brake' ? 'rawBrake' : 'rawClutch');
        const v = lastTelemetryData[k];
        if (typeof v === 'number') {
          if (v > pedalExtremes[p].min) pedalExtremes[p].min = v;
          if (v < pedalExtremes[p].max) pedalExtremes[p].max = v;
        }
      });
    }
  }, 30);

  setTimeout(async () => {
    clearInterval(timer);
    isAutoCalibratingPedals = false;
    if (btn) {
      btn.textContent = "⚡ Auto-Calibrar Pedais (5s)";
      btn.style.background = "";
    }

    ['acc', 'brake', 'clutch'].forEach(p => {
      calibrationState.pedals[p].min_raw = round4(pedalExtremes[p].min);
      calibrationState.pedals[p].max_raw = round4(pedalExtremes[p].max);
    });

    await saveFullCalibration();
    showToast("Auto-calibração concluída! Todos os pedais foram calibrados com precisão.", "success");
  }, 5000);
}

function round4(n) {
  return Math.round(Number(n) * 10000) / 10000;
}
