"""
PCYES W270 Control Center - POWER THE GAME
Port oficial do aplicativo de volante para Windows com suporte nativo e telemetria.
"""

import os
import sys
import ctypes
import threading
import time
import webview

from wheel_ble import WheelBLEManager
from usb_telemetry import USBTelemetryReader
from profile_manager import ProfileManager


class AppAPI:
    """Classe exposta ao frontend Javascript através de window.pywebview.api"""

    def __init__(self, ble_mgr: WheelBLEManager, usb_mgr: USBTelemetryReader, prof_mgr: ProfileManager):
        self.ble = ble_mgr
        self.usb = usb_mgr
        self.profiles = prof_mgr
        # Usar _window (com underscore) para o PyWebView NÃO inspecionar recursivamente o objeto COM WinForms!
        self._window = None
        self.latest_usb_data = {}

        # Registra callback de telemetria USB
        self.usb.start(self._on_usb_data)

    def set_window(self, window):
        self._window = window

    def _on_usb_data(self, data):
        self.latest_usb_data = data

    def get_connection_status(self):
        is_usb = self.usb.is_connected()
        is_connected = self.ble.is_connected or is_usb
        dev_name = "PCYES W270 (USB)" if is_usb else self.ble.device_name
        return {
            "connected": is_connected,
            "device_name": dev_name,
            "device_address": "USB Conectado" if is_usb else self.ble.device_address
        }

    def scan_devices(self):
        return self.ble.scan_devices()

    def connect_device(self, address=None):
        self.ble.connect(address)
        return True

    def disconnect_device(self):
        self.ble.disconnect()
        return True

    def get_wheel_state(self):
        params = self.ble.profile.get("params", [900, 70, 60, 60, 70, 70])
        # Pega a temperatura calculada continuamente a partir da telemetria USB ou BLE
        current_temp = self.latest_usb_data.get("temperature", self.ble.state.get("temperature", 23.0))
        current_fan = self.latest_usb_data.get("fanLevel", self.ble.state.get("fanLevel", 0))
        return {
            "angle": params[0] if len(params) > 0 else 900,
            "ffb": params[1] if len(params) > 1 else 70,
            "spring": params[2] if len(params) > 2 else 60,
            "damping": params[3] if len(params) > 3 else 60,
            "friction": params[4] if len(params) > 4 else 70,
            "inertia": params[5] if len(params) > 5 else 70,
            "ffbReverse": self.ble.profile.get("ffbReverse", False),
            "mode": self.ble.state.get("mode", 1),
            "temperature": round(current_temp, 1),
            "fanLevel": current_fan,
            "accChart": self.ble.profile.get("accChart", [[0, 0], [33, 33], [66, 66], [100, 100]]),
            "brakeChart": self.ble.profile.get("brakeChart", [[0, 0], [33, 33], [66, 66], [100, 100]]),
            "clutchChart": self.ble.profile.get("clutchChart", [[0, 0], [33, 33], [66, 66], [100, 100]]),
            "keymap": self.ble.profile.get("keymap", {})
        }

    def set_angle(self, angle: int):
        self.ble.set_angle(angle)
        return True

    def set_ffb(self, percent: int, reverse: bool):
        self.usb.set_ffb_level(percent)
        self.ble.set_ffb(percent, reverse)
        return True

    def set_force(self, spring: int, damping: int, friction: int, inertia: int):
        self.ble.set_force(spring, damping, friction, inertia)
        return True

    def set_mapping(self, target: int, replace: int):
        self.ble.set_mapping(target, replace)
        return True

    def reset_wheel(self):
        self.ble.reset_settings()
        return True

    def switch_mode(self, mode: int):
        self.ble.switch_mode(mode)
        return True

    def set_test_mode(self, enable: bool):
        self.ble.set_test_mode(enable)
        return True

    def get_telemetry(self):
        res = {}
        if self.latest_usb_data and self.latest_usb_data.get("rawAxes"):
            res = dict(self.latest_usb_data)
            if self.ble.telemetry.get("gear"):
                res["gear"] = self.ble.telemetry["gear"]
        else:
            res = dict(self.ble.telemetry)

        # Dados térmicos dos motores W270
        current_temp = self.latest_usb_data.get("temperature", self.ble.state.get("temperature", 23.0))
        current_fan = self.latest_usb_data.get("fanLevel", self.ble.state.get("fanLevel", 0))
        res["temperature"] = round(current_temp, 1)
        res["fanLevel"] = current_fan
        return res

    def get_calibration(self):
        return self.usb.calibration.data

    def save_calibration(self, data: dict):
        return self.usb.calibration.save(data)

    def reset_calibration(self):
        return self.usb.calibration.reset()

    def set_wheel_center(self):
        raw = self.latest_usb_data.get("rawWheelAxis", 0.0)
        res = self.usb.calibration.set_wheel_center(raw)
        self.ble.calibrate_center(1)
        self.ble.calibrate_center(2)
        return {"success": True, "offset": raw, "data": res}

    def set_wheel_limits(self, min_raw: float, max_raw: float):
        return self.usb.calibration.set_wheel_limits(min_raw, max_raw)

    def set_pedal_calibration(self, pedal_name: str, min_raw: float, max_raw: float, deadzone_low: float, deadzone_high: float):
        return self.usb.calibration.set_pedal_calibration(pedal_name, min_raw, max_raw, deadzone_low, deadzone_high)

    def list_profiles(self):
        return self.profiles.list_profiles()

    def get_profile(self, profile_id: str):
        return self.profiles.get_profile(profile_id)

    def save_profile(self, profile_data: dict):
        return self.profiles.save_profile(profile_data)

    def delete_profile(self, profile_id: str):
        return self.profiles.delete_profile(profile_id)

    def apply_profile(self, profile_data: dict):
        self.ble.apply_full_profile(profile_data)
        return True

    def apply_profile_by_id(self, profile_id: str):
        prof = self.profiles.get_profile(profile_id)
        if prof:
            self.ble.set_angle(prof.get("angle", 900))
            self.ble.set_ffb(prof.get("ffb", 70), prof.get("ffbReverse", False))
            self.ble.set_force(
                prof.get("spring", 60),
                prof.get("damping", 60),
                prof.get("friction", 70),
                prof.get("inertia", 70)
            )
            self.ble.apply_full_profile(prof)
            return True
        return False

    def export_profile(self, profile_id: str):
        if not self._window:
            return False
        dest = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=f"{profile_id}.json",
            file_types=('Arquivos JSON (*.json)',)
        )
        if dest:
            filepath = dest if isinstance(dest, str) else dest[0]
            return self.profiles.export_profile(profile_id, filepath)
        return False

    def import_profile(self):
        if not self._window:
            return None
        files = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=('Arquivos JSON (*.json)',)
        )
        if files:
            filepath = files[0] if isinstance(files, (list, tuple)) else files
            return self.profiles.import_profile(filepath)
        return None


def apply_pcyes_icon(window):
    """Aplica o ícone da PCYES na barra de títulos e na barra de tarefas do Windows."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ico_path = os.path.join(base_dir, "pcyes.ico")
        if os.path.exists(ico_path):
            WM_SETICON = 0x0080
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010
            LR_DEFAULTSIZE = 0x00000040

            h_icon = ctypes.windll.user32.LoadImageW(None, ico_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
            if h_icon:
                hwnd = ctypes.windll.user32.FindWindowW(None, "PCYES W270 Control Center")
                if hwnd:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 0, h_icon) # small
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 1, h_icon) # big
    except Exception as e:
        pass


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "gui", "index.html")

    ble_mgr = WheelBLEManager()
    usb_mgr = USBTelemetryReader()
    prof_mgr = ProfileManager()

    api = AppAPI(ble_mgr, usb_mgr, prof_mgr)

    # Inicia conexão BLE automática com o volante em segundo plano
    threading.Thread(target=ble_mgr.connect, daemon=True).start()

    window = webview.create_window(
        title="PCYES W270 Control Center",
        url=html_path,
        js_api=api,
        width=1120,
        height=740,
        min_size=(960, 640),
        background_color="#0d0f14"
    )
    api.set_window(window)

    # Quando a janela abrir, define o ícone e inicia
    window.events.shown += lambda: apply_pcyes_icon(window)

    webview.start(debug=False)

    # Ao fechar o app, encerra conexões
    usb_mgr.stop()
    ble_mgr.disconnect()


if __name__ == "__main__":
    main()
