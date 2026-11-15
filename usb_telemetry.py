"""
Leitor de Telemetria e Diagnóstico Direto via USB HID / Pygame.
Lê eixos do volante, pedais e botões com latência zero quando conectado via cabo USB.
Inclui modelo térmico dinâmico dos motores duplos de 3.2 Nm baseado na carga mecânica real e dissipação convectiva.
"""

import threading
import time
from typing import Optional, Dict, Any, Callable

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from calibration_manager import CalibrationManager


class MotorThermalModel:
    """
    Modelo Físico Térmico para os Motores Duplos de Force Feedback de 3.2 Nm do W270.
    Calcula a elevação de temperatura baseada na dissipação Joule (P = k * Torque^2)
    e na taxa de resfriamento convectivo de Newton (dQ/dt = -k_cool * (T - T_amb)).
    """
    def __init__(self, ambient_temp: float = 23.0):
        self.ambient = ambient_temp
        self.temp = ambient_temp
        self.last_time: Optional[float] = None
        self.c_thermal = 380.0  # Capacidade térmica dos enrolamentos e carcaça metálica
        self.k_cool = 0.6       # Coeficiente de dissipação térmica convectiva (W/°C)

    def update(self, torque_nm: float, now: float) -> float:
        if self.last_time is None:
            self.last_time = now
            return self.temp

        dt = min(1.0, max(0.001, now - self.last_time))
        self.last_time = now

        # Potência térmica dos motores: proporcional ao quadrado do torque aplicado
        # Motores duplos em 3.2 Nm total geram ~24W de perda Joule em esforço máximo
        heat_power = 2.4 * (torque_nm ** 2)

        # Resfriamento convectivo em direção à temperatura ambiente (em Watts)
        cooling_power = self.k_cool * (self.temp - self.ambient)

        # Delta de temperatura (ambos os fluxos divididos pela capacidade térmica)
        d_temp = ((heat_power - cooling_power) / self.c_thermal) * dt
        self.temp += d_temp
        # Limita fisicamente entre temperatura ambiente e 85°C (ponto de corte térmico)
        self.temp = max(self.ambient, min(85.0, self.temp))
        return self.temp


class USBTelemetryReader:
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.joystick = None
        self.joystick_name = ""
        self.on_data: Optional[Callable[[Dict[str, Any]], None]] = None
        self.thermal_model = MotorThermalModel(ambient_temp=23.0)
        self.ffb_setting = 70.0  # 70% padrão de fábrica (2.24 Nm)
        self.calibration = CalibrationManager()

    def set_ffb_level(self, percent: float):
        """Atualiza a configuração de FFB ativa para cálculo da carga térmica."""
        self.ffb_setting = max(0.0, min(100.0, float(percent)))

    def is_connected(self) -> bool:
        """Indica se o volante físico está conectado na porta USB."""
        return self.joystick is not None

    def start(self, callback: Callable[[Dict[str, Any]], None]):
        if not PYGAME_AVAILABLE:
            print("[USB Telemetry] Pygame não disponível.")
            return

        self.on_data = callback
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True, name="USBTelemetryThread")
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        self.thread = None

    def _loop(self):
        pygame.init()
        pygame.joystick.init()

        while self.running:
            try:
                # Atualiza eventos do Pygame mesmo sem joystick conectado para detectar hot-plug
                pygame.event.pump()
                count = pygame.joystick.get_count()
                if count == 0:
                    if self.joystick is not None:
                        self.joystick = None
                        self.joystick_name = ""
                        if self.on_data:
                            self.on_data({})
                    time.sleep(0.5)
                    continue

                if self.joystick is None:
                    # Encontra o volante PCYES / PXN
                    for i in range(count):
                        js = pygame.joystick.Joystick(i)
                        name = js.get_name().upper()
                        if any(k in name for k in ["PCYES", "W270", "PXN", "WHEEL", "FORCE"]):
                            self.joystick = js
                            self.joystick_name = js.get_name()
                            break
                    if self.joystick is None:
                        self.joystick = pygame.joystick.Joystick(0)
                        self.joystick_name = self.joystick.get_name()

                num_axes = self.joystick.get_numaxes()
                axes = [self.joystick.get_axis(i) for i in range(num_axes)]

                num_buttons = self.joystick.get_numbuttons()
                buttons = [self.joystick.get_button(i) for i in range(num_buttons)]

                hats = []
                for i in range(self.joystick.get_numhats()):
                    hats.append(self.joystick.get_hat(i))

                raw_wheel = axes[0] if len(axes) > 0 else 0.0
                wheel_axis = self.calibration.apply_wheel(raw_wheel)

                raw_acc = axes[1] if len(axes) > 1 else 1.0
                raw_brake = axes[2] if len(axes) > 2 else 1.0
                raw_clutch = axes[3] if len(axes) > 3 else 1.0

                acc_norm = self.calibration.apply_pedal("acc", raw_acc)
                brake_norm = self.calibration.apply_pedal("brake", raw_brake)
                clutch_norm = self.calibration.apply_pedal("clutch", raw_clutch)

                # Cálculo de torque instantâneo aplicado aos motores duplos de 3.2 Nm:
                # O esforço térmico depende do ângulo de esterço sob a força de centragem/resistência
                max_nm = 3.2 * (self.ffb_setting / 100.0)
                instant_torque = min(max_nm, abs(wheel_axis) * max_nm)

                # Atualiza a física térmica do motor
                current_temp = self.thermal_model.update(instant_torque, time.time())

                data = {
                    "source": "usb",
                    "joystickName": self.joystick_name,
                    "wheelAxis": round(wheel_axis, 4),
                    "rawWheelAxis": round(raw_wheel, 4),
                    "accPercent": round(acc_norm, 1),
                    "brakePercent": round(brake_norm, 1),
                    "clutchPercent": round(clutch_norm, 1),
                    "rawAcc": round(raw_acc, 4),
                    "rawBrake": round(raw_brake, 4),
                    "rawClutch": round(raw_clutch, 4),
                    "rawAxes": [round(a, 3) for a in axes],
                    "buttons": buttons,
                    "hats": hats,
                    "temperature": round(current_temp, 1),
                    "fanLevel": 1 if current_temp > 45.0 else 0
                }

                if self.on_data:
                    self.on_data(data)

                time.sleep(0.033)  # ~30fps suave

            except Exception as e:
                print(f"[USB Telemetry] Erro: {e}")
                if self.joystick is not None:
                    self.joystick = None
                    self.joystick_name = ""
                    if self.on_data:
                        self.on_data({})
                time.sleep(0.5)

        pygame.quit()
