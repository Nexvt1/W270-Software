"""
Gerenciador de Conexão Bluetooth Low Energy (BLE) com o Volante PCYES / PXN.
Executa em background thread para comunicação fluida sem congelar a interface.
"""

import asyncio
import threading
import time
from typing import Callable, Optional, Dict, Any, List
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from wheel_protocol import (
    SERVICE_UUID,
    WRITE_CHAR_UUID,
    NOTIFY_CHAR_UUID,
    REPORT_ID_READ_STATE_RESP,
    REPORT_ID_READ_PROFILE_RESP,
    REPORT_ID_TESTING_RESP,
    build_read_state_packet,
    build_read_profile_packet,
    build_angle_packet,
    build_ffb_packet,
    build_force_packet,
    build_mapping_packet,
    build_reset_packet,
    build_switch_mode_packet,
    build_test_mode_packet,
    build_calibrate_packet,
    pack_profile_block,
    unpack_state_data,
    unpack_profile_data,
    unpack_test_data
)

# Nomes de dispositivos suportados pelo app
SUPPORTED_NAMES = [
    "FFB WHEEL",
    "PCYES",
    "PXN-V10",
    "PXN-V99",
    "PXN-V12",
    "V12LITE",
    "DD WHEEL",
    "PXN-VD6",
    "PXN-VD10",
    "FFB W FORCE",
    "LS D101",
    "DM1X",
    "DP1X"
]


class WheelBLEManager:
    def __init__(self):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.client: Optional[BleakClient] = None
        self.device: Optional[BLEDevice] = None
        self.is_connected = False
        self.is_connecting = False
        self.device_name = "Desconectado"
        self.device_address = ""

        # Estado e Perfil carregados da memória do volante
        self.state: Dict[str, Any] = {
            "mode": 1,
            "version": 0,
            "angle": 900,
            "pedalState": 0,
            "leverState": 0
        }
        self.profile: Dict[str, Any] = {
            "mode": 1,
            "params": [900, 70, 60, 60, 70, 70],
            "ffbReverse": False,
            "keymap": {},
            "accChart": [[0, 0], [33, 33], [66, 66], [100, 100]],
            "brakeChart": [[0, 0], [33, 33], [66, 66], [100, 100]],
            "clutchChart": [[0, 0], [33, 33], [66, 66], [100, 100]],
        }

        # Telemetria em tempo real
        self.telemetry: Dict[str, Any] = {
            "angleRaw": 128,
            "angleNorm": 0.0,
            "acc": 0,
            "brake": 0,
            "clutch": 0,
            "gear": "N",
            "gearRaw": 0,
            "buttons": {}
        }

        self.test_mode_active = False

        # Callbacks para interface gráfica
        self.on_state_change: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_profile_change: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_telemetry_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connection_change: Optional[Callable[[bool, str], None]] = None

        self._start_worker_thread()

    def _start_worker_thread(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(target=run_loop, daemon=True, name="WheelBLEThread")
        self.thread.start()
        while self.loop is None:
            time.sleep(0.01)

    def _run_async(self, coro):
        if self.loop and self.loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        return None

    def scan_devices(self, timeout=3.0) -> List[Dict[str, Any]]:
        future = self._run_async(self._scan_coro(timeout))
        if future:
            return future.result()
        return []

    async def _scan_coro(self, timeout=3.0) -> List[Dict[str, Any]]:
        found = []
        try:
            discovered = await BleakScanner.discover(return_adv=True, timeout=timeout)
            for d, adv in discovered.values():
                name = d.name or adv.local_name or ""
                is_wheel = any(k in name.upper() for k in SUPPORTED_NAMES)
                found.append({
                    "name": name,
                    "address": d.address,
                    "rssi": adv.rssi,
                    "isWheel": is_wheel
                })
        except Exception as e:
            print(f"[BLE] Erro no escaneamento: {e}")
        return found

    def connect(self, address: Optional[str] = None):
        self._run_async(self._connect_coro(address))

    def disconnect(self):
        self._run_async(self._disconnect_coro())

    async def _connect_coro(self, target_address: Optional[str] = None):
        if self.is_connecting or self.is_connected:
            return

        self.is_connecting = True
        if self.on_connection_change:
            self.on_connection_change(False, "Conectando...")

        try:
            target_device = None
            if target_address:
                target_device = await BleakScanner.find_device_by_address(target_address, timeout=5.0)
            else:
                # Procura automaticamente volante compatível
                devices = await BleakScanner.discover(return_adv=True, timeout=4.0)
                for d, adv in devices.values():
                    name = (d.name or adv.local_name or "").upper()
                    if any(k in name for k in SUPPORTED_NAMES):
                        target_device = d
                        break

            if not target_device:
                self.is_connecting = False
                if self.on_connection_change:
                    self.on_connection_change(False, "Volante não encontrado. Verifique se o Bluetooth está ativo.")
                return

            self.client = BleakClient(target_device, disconnected_callback=self._on_disconnected)
            await self.client.connect()
            self.is_connected = self.client.is_connected
            self.is_connecting = False
            self.device_name = target_device.name or "PCYES Racing Wheel"
            self.device_address = target_device.address

            print(f"[BLE] Conectado com sucesso a {self.device_name} ({self.device_address})")

            # Ativa notificações
            await self.client.start_notify(NOTIFY_CHAR_UUID, self._notification_handler)

            if self.on_connection_change:
                self.on_connection_change(True, self.device_name)

            # Solicita leitura de estado e todos os blocos de perfil
            await self._read_initial_data()

        except Exception as e:
            print(f"[BLE] Falha ao conectar: {e}")
            self.client = None
            self.is_connecting = False
            self.is_connected = False
            if self.on_connection_change:
                self.on_connection_change(False, f"Erro ao conectar: {e}")

    def _on_disconnected(self, client):
        print("[BLE] Dispositivo desconectado.")
        self.is_connected = False
        self.test_mode_active = False
        if self.on_connection_change:
            self.on_connection_change(False, "Desconectado")

    async def _disconnect_coro(self):
        if self.client and self.client.is_connected:
            try:
                if self.test_mode_active:
                    await self._send_packet_coro(build_test_mode_packet(False))
                await self.client.stop_notify(NOTIFY_CHAR_UUID)
                await self.client.disconnect()
            except Exception as e:
                print(f"[BLE] Erro ao desconectar: {e}")
        self.is_connected = False
        self.client = None
        if self.on_connection_change:
            self.on_connection_change(False, "Desconectado")

    def _notification_handler(self, sender, data: bytearray):
        if not data or len(data) == 0:
            return

        report_id = data[0]

        if report_id == REPORT_ID_READ_STATE_RESP:
            st = unpack_state_data(bytes(data))
            if st:
                self.state.update(st)
                if self.on_state_change:
                    self.on_state_change(self.state)

        elif report_id == REPORT_ID_READ_PROFILE_RESP:
            unpack_profile_data(bytes(data), self.profile)
            if self.on_profile_change:
                self.on_profile_change(self.profile)

        elif report_id == REPORT_ID_TESTING_RESP:
            tel = unpack_test_data(bytes(data))
            if tel:
                self.telemetry.update(tel)
                if self.on_telemetry_update:
                    self.on_telemetry_update(self.telemetry)

    async def _read_initial_data(self):
        if not self.is_connected or not self.client:
            return

        # 1. Lê estado do volante
        await self._send_packet_coro(build_read_state_packet())
        await asyncio.sleep(0.2)

        # 2. Lê blocos do perfil (0 a 5)
        mode = self.state.get("mode", 1)
        for i in range(6):
            await self._send_packet_coro(build_read_profile_packet(mode, i))
            await asyncio.sleep(0.15)

    async def _send_packet_coro(self, packet: bytearray):
        if self.client and self.client.is_connected:
            try:
                await self.client.write_gatt_char(WRITE_CHAR_UUID, packet, response=True)
            except Exception as e:
                print(f"[BLE] Erro ao enviar pacote {list(packet)}: {e}")

    # Comandos públicos executados de forma assíncrona
    def send_packet(self, packet: bytearray):
        self._run_async(self._send_packet_coro(packet))

    def set_angle(self, angle: int):
        """Ajusta o ângulo de rotação (90° a 1080°)."""
        self.profile.setdefault("params", [900, 70, 60, 60, 70, 70])[0] = angle
        self.send_packet(build_angle_packet(angle))

    def set_ffb(self, ffb_percent: int, reverse: bool = False):
        """Ajusta a força de Force Feedback geral (0-100%) e inversão."""
        mode = self.state.get("mode", 1)
        params = self.profile.setdefault("params", [900, 70, 60, 60, 70, 70])
        params[1] = ffb_percent
        self.profile["ffbReverse"] = reverse
        self.send_packet(build_ffb_packet(mode, ffb_percent, reverse))

    def set_force(self, spring: int, damping: int, friction: int, inertia: int):
        """Ajusta parâmetros avançados de forças."""
        params = self.profile.setdefault("params", [900, 70, 60, 60, 70, 70])
        params[2] = spring
        params[3] = damping
        params[4] = friction
        params[5] = inertia
        self.send_packet(build_force_packet(spring, damping, friction, inertia))

    def set_mapping(self, target: int, replace: int):
        """Remapeia tecla."""
        mode = self.state.get("mode", 1)
        self.profile.setdefault("keymap", {})[target] = replace
        self.send_packet(build_mapping_packet(mode, target, replace))

    def reset_settings(self):
        """Restaura padrões de fábrica."""
        mode = self.state.get("mode", 1)
        async def _reset():
            await self._send_packet_coro(build_reset_packet(mode))
            await asyncio.sleep(0.3)
            await self._read_initial_data()
        self._run_async(_reset())

    def switch_mode(self, mode: int):
        """Alterna modo (1 ou 2)."""
        self.send_packet(build_switch_mode_packet(mode))
        self.state["mode"] = mode

    def set_test_mode(self, enable: bool):
        """Ativa/Desativa modo de teste e telemetria contínua."""
        self.test_mode_active = enable
        self.send_packet(build_test_mode_packet(enable))

    def calibrate_center(self, step: int = 1):
        """Dispara comando de calibração do centro físico no hardware (step 1=início, 2=confirma)."""
        self.send_packet(build_calibrate_packet(step))

    def apply_full_profile(self, profile_data: dict):
        """Grava perfil completo (todos os 6 blocos) na memória do volante."""
        params = list(self.profile.get("params", [900, 70, 60, 60, 70, 70]))
        if "params" in profile_data and isinstance(profile_data["params"], list):
            params = list(profile_data["params"])
        else:
            if "angle" in profile_data:
                params[0] = int(profile_data["angle"])
            if "ffb" in profile_data:
                params[1] = int(profile_data["ffb"])
            if "spring" in profile_data:
                params[2] = int(profile_data["spring"])
            if "damping" in profile_data:
                params[3] = int(profile_data["damping"])
            if "friction" in profile_data:
                params[4] = int(profile_data["friction"])
            if "inertia" in profile_data:
                params[5] = int(profile_data["inertia"])

        self.profile.update(profile_data)
        self.profile["params"] = params

        async def _apply():
            mode = self.state.get("mode", 1)
            for i in range(6):
                block = pack_profile_block(i, mode, self.profile)
                await self._send_packet_coro(block)
                await asyncio.sleep(0.12)
            print("[BLE] Perfil completo aplicado com sucesso!")
        self._run_async(_apply())
