"""
Gerenciador de Calibração de Hardware para o Volante PCYES W270.
Controla o ponto zero (centro 0°), batentes de rotação e calibração de sensores Hall
dos pedais (acelerador, freio, embreagem) com zonas mortas personalizáveis.
"""

import os
import json
import threading
from typing import Dict, Any, Tuple

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")

DEFAULT_CALIBRATION: Dict[str, Any] = {
    "wheel": {
        "center_offset": 0.0,      # Desvio de alinhamento central
        "deadzone_percent": 0.0,   # Zona morta central (0% a 10%)
        "min_raw": -1.0,           # Batente esquerdo máximo
        "max_raw": 1.0             # Batente direito máximo
    },
    "pedals": {
        "acc": {
            "min_raw": 1.0,        # Posição de repouso (solto)
            "max_raw": -1.0,       # Fundo de curso (100% pressionado)
            "deadzone_low": 1.5,   # % inicial de folga
            "deadzone_high": 2.0   # % final para atingir 100% garantido
        },
        "brake": {
            "min_raw": 1.0,
            "max_raw": -1.0,
            "deadzone_low": 2.0,
            "deadzone_high": 2.5
        },
        "clutch": {
            "min_raw": 1.0,
            "max_raw": -1.0,
            "deadzone_low": 2.0,
            "deadzone_high": 2.5
        }
    }
}


class CalibrationManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.data: Dict[str, Any] = self.load()

    def _merge_defaults(self, loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Mescla dados carregados com o esquema padrão para evitar chaves ausentes."""
        res = json.loads(json.dumps(DEFAULT_CALIBRATION))
        if isinstance(loaded, dict):
            if isinstance(loaded.get("wheel"), dict):
                res["wheel"].update(loaded["wheel"])
            if isinstance(loaded.get("pedals"), dict):
                for p in ["acc", "brake", "clutch"]:
                    if isinstance(loaded["pedals"].get(p), dict):
                        res["pedals"][p].update(loaded["pedals"][p])
        return res

    def load(self) -> Dict[str, Any]:
        """Carrega calibração persistente do arquivo calibration.json."""
        if os.path.exists(CALIBRATION_FILE):
            try:
                with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    return self._merge_defaults(loaded)
            except Exception as e:
                print(f"[Calibração] Erro ao carregar {CALIBRATION_FILE}: {e}")
        return json.loads(json.dumps(DEFAULT_CALIBRATION))

    def save(self, data: Dict[str, Any]) -> bool:
        """Salva a calibração atual no disco."""
        try:
            with self._lock:
                self.data = self._merge_defaults(data)
                with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Calibração] Erro ao salvar: {e}")
            return False

    def reset(self) -> Dict[str, Any]:
        """Restaura a calibração de fábrica."""
        self.data = json.loads(json.dumps(DEFAULT_CALIBRATION))
        self.save(self.data)
        return self.data

    def set_wheel_center(self, raw_center_value: float) -> Dict[str, Any]:
        """Define a posição atual do volante como Centro Físico 0.0°."""
        self.data["wheel"]["center_offset"] = round(float(raw_center_value), 4)
        self.save(self.data)
        return self.data

    def set_wheel_limits(self, min_raw: float, max_raw: float) -> Dict[str, Any]:
        """Define os limites físicos esquerdo e direito alcançados no esterço."""
        self.data["wheel"]["min_raw"] = round(float(min_raw), 4)
        self.data["wheel"]["max_raw"] = round(float(max_raw), 4)
        self.save(self.data)
        return self.data

    def set_pedal_calibration(self, pedal_name: str, min_raw: float, max_raw: float,
                               deadzone_low: float = 1.5, deadzone_high: float = 2.0) -> Dict[str, Any]:
        """Calibra ponto de repouso e fim de curso para um pedal Hall."""
        if pedal_name in self.data["pedals"]:
            self.data["pedals"][pedal_name] = {
                "min_raw": round(float(min_raw), 4),
                "max_raw": round(float(max_raw), 4),
                "deadzone_low": max(0.0, min(15.0, float(deadzone_low))),
                "deadzone_high": max(0.0, min(15.0, float(deadzone_high)))
            }
            self.save(self.data)
        return self.data

    def apply_wheel(self, raw_axis: float) -> float:
        """Aplica o offset de centro, limites físicos e zona morta ao eixo do volante."""
        with self._lock:
            wheel_cfg = dict(self.data["wheel"])

        offset = wheel_cfg.get("center_offset", 0.0)
        min_raw = wheel_cfg.get("min_raw", -1.0)
        max_raw = wheel_cfg.get("max_raw", 1.0)
        deadzone = wheel_cfg.get("deadzone_percent", 0.0) / 100.0

        if raw_axis >= offset:
            span = max(0.001, max_raw - offset)
            calibrated = (raw_axis - offset) / span
        else:
            span = max(0.001, offset - min_raw)
            calibrated = (raw_axis - offset) / span

        calibrated = max(-1.0, min(1.0, calibrated))

        if abs(calibrated) <= deadzone:
            return 0.0

        # Remapeia o curso restante suavemente após a zona morta
        if calibrated > 0:
            calibrated = (calibrated - deadzone) / max(0.001, 1.0 - deadzone)
        else:
            calibrated = (calibrated + deadzone) / max(0.001, 1.0 - deadzone)

        return max(-1.0, min(1.0, calibrated))

    def apply_pedal(self, pedal_name: str, raw_axis: float) -> float:
        """
        Normaliza e calibra o valor do pedal para 0.0% a 100.0%.
        Aplica compensação de repouso, fim de curso e zonas mortas anti-arrasto.
        """
        with self._lock:
            cfg = dict(self.data["pedals"].get(pedal_name) or {})

        if not cfg:
            # Fallback padrão se não configurado: [-1.0, 1.0] com repouso em 1.0
            return max(0.0, min(100.0, (1.0 - raw_axis) * 50.0))

        min_raw = cfg.get("min_raw", 1.0)
        max_raw = cfg.get("max_raw", -1.0)
        dz_low = cfg.get("deadzone_low", 1.5)
        dz_high = cfg.get("deadzone_high", 2.0)

        diff = max_raw - min_raw
        if abs(diff) < 0.001:
            return 0.0

        # Razão linear 0.0 a 1.0
        ratio = (raw_axis - min_raw) / diff
        percent = ratio * 100.0

        # Aplica Deadzone Inferior (Repouso)
        if percent <= dz_low:
            return 0.0

        # Aplica Deadzone Superior (Fundo de Curso)
        if percent >= (100.0 - dz_high):
            return 100.0

        # Remapeia linearmente o miolo útil
        useful_range = (100.0 - dz_high) - dz_low
        if useful_range > 0:
            calibrated_percent = ((percent - dz_low) / useful_range) * 100.0
            return max(0.0, min(100.0, calibrated_percent))

        return max(0.0, min(100.0, percent))
