"""
Protocolo de Comunicação do Volante PCYES / PXN (V10, V99, V12, W270).
Engenharia reversa feita a partir do aplicativo móvel oficial (RacingWheel_release.apk).
"""

import struct

# Report IDs (GATT Characteristic ffe1 / ffe2)
REPORT_ID_READ_STATE_REQ    = 0x50  # 80
REPORT_ID_READ_STATE_RESP   = 0xD0  # 208
REPORT_ID_READ_PROFILE_REQ  = 0x51  # 81
REPORT_ID_READ_PROFILE_RESP = 0xD1  # 209
REPORT_ID_WRITE_PROFILE_REQ = 0x52  # 82
REPORT_ID_WRITE_PROFILE_RESP= 0xD2  # 210
REPORT_ID_EDIT_PARAMS_REQ   = 0x53  # 83
REPORT_ID_EDIT_PARAMS_RESP  = 0xD3  # 211
REPORT_ID_TESTING_REQ       = 0x54  # 84
REPORT_ID_TESTING_RESP      = 0xD4  # 212

# Comandos de edição rápida (Report 0x53)
CMD_SWITCH_MODE             = 1
CMD_UPDATE_KEYMAP           = 2
CMD_UPDATE_FFB              = 3
CMD_UPDATE_ANGLE            = 4
CMD_UPDATE_PEDAL            = 6
CMD_UPDATE_SHIFTER          = 7
CMD_RESET_PROFILE           = 8
CMD_UPDATE_FORCE            = 9
CMD_UPDATE_PANEL            = 10
CMD_UPDATE_LED_1            = 11
CMD_UPDATE_LED_2            = 12
CMD_UPDATE_CHART_1          = 13
CMD_UPDATE_CHART_2          = 14
CMD_UPDATE_CALIBRATE        = 15
CMD_UPDATE_ROAD_SENSITIVITY = 16
CMD_UPDATE_FAN_LEVEL        = 17
CMD_TOGGLE_DOUBLE_CLUTCH    = 18
CMD_SEND_VIRTUAL_KEY        = 19

# Sequência de teclas por bloco do perfil
KEY_SEQUENCE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 16],
    [14, 15, 47, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33],
    [34, 35]
]

# Mapa de Códigos de Tecla (KeyCodes)
KEYCODES = {
    0: "VIEW",
    1: "L3",
    2: "R3",
    3: "MENU",
    4: "D-PAD CIMA",
    5: "D-PAD DIR",
    6: "D-PAD BAIXO",
    7: "D-PAD ESQ",
    8: "Y / TRIÂNGULO",
    9: "B / CÍRCULO",
    10: "A / X (CRUZ)",
    11: "X / QUADRADO",
    12: "L1 / LB",
    13: "R1 / RB",
    14: "L2 / LT",
    15: "R2 / RT",
    16: "HOME / GUIA",
    17: "SHARE",
    18: "ENCODER ESQ",
    19: "ENCODER DIR",
    20: "ACELERADOR",
    21: "FREIO",
    22: "EMBREAGEM",
    23: "GU (MARCHA CIMA)",
    24: "GD (MARCHA BAIXO)",
    25: "FREIO DE MÃO",
    26: "TROCA DE MARCHA",
    27: "MARCHA 1",
    28: "MARCHA 2",
    29: "MARCHA 3",
    30: "MARCHA 4",
    31: "MARCHA 5",
    32: "MARCHA 6",
    33: "MARCHA RÉ",
    34: "LX-",
    35: "LX+",
    36: "BORBOLETA SUP ESQ",
    37: "BORBOLETA SUP DIR",
    38: "BORBOLETA INF ESQ",
    39: "BORBOLETA INF DIR",
    40: "ENCODER FREIO",
    41: "ENCODER FREIO ESQ",
    42: "ENCODER FREIO DIR",
    43: "ENCODER TC",
    44: "ENCODER TC ESQ",
    45: "ENCODER TC DIR",
    46: "RESET",
    47: "RESERVADO",
    48: "MOUSE ESQ",
    49: "MOUSE DIR",
    50: "MOUSE MEIO",
}

# UUIDs de Bluetooth Low Energy (BLE)
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"


def build_read_state_packet():
    """Lê estado atual do volante (modo, versão, ângulo atual, etc)."""
    return bytearray([REPORT_ID_READ_STATE_REQ, 1])


def build_read_profile_packet(mode: int, block_num: int):
    """Lê bloco de perfil (0 a 5)."""
    return bytearray([REPORT_ID_READ_PROFILE_REQ, mode & 0xFF, block_num & 0xFF])


def build_angle_packet(angle: int):
    """Define ângulo máximo de rotação (ex: 270, 900, 1080 graus)."""
    angle = max(90, min(1080, angle))
    return bytearray([
        REPORT_ID_EDIT_PARAMS_REQ,
        CMD_UPDATE_ANGLE,
        1,
        1,
        angle & 0xFF,
        (angle >> 8) & 0xFF
    ])


def build_ffb_packet(mode: int, ffb_percent: int, reverse: bool):
    """Define força geral do Force Feedback (0-100%) e inversão."""
    ffb = max(0, min(100, ffb_percent))
    return bytearray([
        REPORT_ID_EDIT_PARAMS_REQ,
        CMD_UPDATE_FFB,
        mode & 0xFF,
        ffb,
        1 if reverse else 0
    ])


def build_force_packet(spring: int, damping: int, friction: int, inertia: int):
    """
    Define forças avançadas de feedback:
    spring: Mola de retorno ao centro (0-100%)
    damping: Amortecimento do volante (0-100%)
    friction: Fricção mecânica (0-100%)
    inertia: Inércia da direção (0-100%)
    """
    return bytearray([
        REPORT_ID_EDIT_PARAMS_REQ,
        CMD_UPDATE_FORCE,
        1,
        max(0, min(100, spring)),
        max(0, min(100, damping)),
        max(0, min(100, friction)),
        max(0, min(100, inertia))
    ])


def build_calibrate_packet(step: int = 1):
    """
    Comando oficial de calibração do centro físico do hardware PCYES/PXN.
    step = 1: Inicia calibração
    step = 2: Grava e confirma calibração no firmware/EEPROM
    """
    return bytearray([
        REPORT_ID_EDIT_PARAMS_REQ,
        CMD_UPDATE_CALIBRATE,
        1 if step == 1 else 2
    ])



def build_mapping_packet(mode: int, target_key: int, replace_key: int):
    """Remapeia um botão físico para outro botão."""
    return bytearray([
        REPORT_ID_EDIT_PARAMS_REQ,
        CMD_UPDATE_KEYMAP,
        mode & 0xFF,
        target_key & 0xFF,
        replace_key & 0xFF
    ])


def build_reset_packet(mode: int):
    """Restaura as configurações de fábrica do volante."""
    return bytearray([
        REPORT_ID_EDIT_PARAMS_REQ,
        CMD_RESET_PROFILE,
        mode & 0xFF
    ])


def build_switch_mode_packet(mode: int):
    """Alterna modo do volante (D-Input / X-Input)."""
    return bytearray([
        REPORT_ID_EDIT_PARAMS_REQ,
        CMD_SWITCH_MODE,
        mode & 0xFF
    ])


def build_test_mode_packet(enable: bool):
    """Ativa ou desativa modo de telemetria/teste em tempo real."""
    return bytearray([
        REPORT_ID_TESTING_REQ,
        1 if enable else 2
    ])


def pack_profile_block(num: int, mode: int, profile_data: dict) -> bytearray:
    """Empacota um bloco de perfil de 20 bytes para envio (Report 0x52)."""
    buf = bytearray(20)
    buf[0] = REPORT_ID_WRITE_PROFILE_REQ
    buf[1] = mode & 0xFF
    buf[2] = num & 0xFF

    keymap = profile_data.get("keymap", {})
    params = profile_data.get("params", [900, 70, 60, 60, 70, 70])
    ffb_reverse = profile_data.get("ffbReverse", False)
    acc_chart = profile_data.get("accChart", [[0, 0], [33, 33], [66, 66], [100, 100]])
    brake_chart = profile_data.get("brakeChart", [[0, 0], [33, 33], [66, 66], [100, 100]])
    clutch_chart = profile_data.get("clutchChart", [[0, 0], [33, 33], [66, 66], [100, 100]])

    pos = 3
    if num == 0:
        for k in KEY_SEQUENCE[0]:
            val = keymap.get(k, k)
            buf[pos] = val & 0xFF
            pos += 1
    elif num == 1:
        for k in KEY_SEQUENCE[1]:
            val = keymap.get(k, k)
            buf[pos] = val & 0xFF
            pos += 1
    elif num == 2:
        for k in KEY_SEQUENCE[2]:
            val = keymap.get(k, k)
            buf[pos] = val & 0xFF
            pos += 1
        angle = int(params[0])
        buf[pos] = angle & 0xFF
        buf[pos + 1] = (angle >> 8) & 0xFF
        pos += 2
        for i in range(1, 6):
            buf[pos] = int(params[i]) & 0xFF
            pos += 1
        buf[pos] = 1 if ffb_reverse else 0
    elif num == 3:
        for pt in acc_chart:
            struct.pack_into("<HH", buf, pos, int(pt[0]), int(pt[1]))
            pos += 4
    elif num == 4:
        for pt in brake_chart:
            struct.pack_into("<HH", buf, pos, int(pt[0]), int(pt[1]))
            pos += 4
    elif num == 5:
        for pt in clutch_chart:
            struct.pack_into("<HH", buf, pos, int(pt[0]), int(pt[1]))
            pos += 4

    return buf


def unpack_state_data(data: bytes) -> dict:
    """Decodifica notificação do Report 0xD0 (208)."""
    if len(data) < 10 or data[0] != REPORT_ID_READ_STATE_RESP:
        return {}
    mode = data[2]
    version = data[3] | (data[4] << 8)
    pedal_state = data[5]
    lever_state = data[6]
    angle_mode = data[7]
    current_angle = data[8] | (data[9] << 8)
    # Byte 10: Sensor de Temperatura Interna do Motor (°C)
    temperature = data[10] if len(data) > 10 else 0
    # Byte 14: Nível da Ventoinha / Cooler
    fan_level = data[14] if len(data) > 14 else 0
    return {
        "mode": mode,
        "version": version,
        "pedalState": pedal_state,
        "leverState": lever_state,
        "angleMode": angle_mode,
        "angle": current_angle,
        "temperature": temperature,
        "fanLevel": fan_level,
    }


def unpack_profile_data(data: bytes, current_profile: dict) -> dict:
    """Decodifica notificação do Report 0xD1 (209)."""
    if len(data) < 3 or data[0] != REPORT_ID_READ_PROFILE_RESP:
        return current_profile

    mode = data[1]
    num = data[2]
    current_profile["mode"] = mode

    keymap = current_profile.setdefault("keymap", {})
    params = current_profile.setdefault("params", [900, 70, 60, 60, 70, 70])

    pos = 3
    if num == 0:
        for k in KEY_SEQUENCE[0]:
            if pos < len(data):
                keymap[k] = data[pos]
                pos += 1
    elif num == 1:
        for k in KEY_SEQUENCE[1]:
            if pos < len(data):
                keymap[k] = data[pos]
                pos += 1
    elif num == 2:
        for k in KEY_SEQUENCE[2]:
            if pos < len(data):
                keymap[k] = data[pos]
                pos += 1
        if pos + 1 < len(data):
            params[0] = data[pos] | (data[pos + 1] << 8)
            pos += 2
        for i in range(1, 6):
            if pos < len(data):
                params[i] = data[pos]
                pos += 1
        if pos < len(data):
            current_profile["ffbReverse"] = (data[pos] == 1)
    elif num == 3:
        chart = []
        for _ in range(4):
            if pos + 3 < len(data):
                x, y = struct.unpack_from("<HH", data, pos)
                chart.append([x, y])
                pos += 4
        current_profile["accChart"] = chart
    elif num == 4:
        chart = []
        for _ in range(4):
            if pos + 3 < len(data):
                x, y = struct.unpack_from("<HH", data, pos)
                chart.append([x, y])
                pos += 4
        current_profile["brakeChart"] = chart
    elif num == 5:
        chart = []
        for _ in range(4):
            if pos + 3 < len(data):
                x, y = struct.unpack_from("<HH", data, pos)
                chart.append([x, y])
                pos += 4
        current_profile["clutchChart"] = chart

    return current_profile


def unpack_test_data(data: bytes) -> dict:
    """Decodifica notificação de telemetria em tempo real (Report 0xD4 / 212)."""
    if len(data) < 14 or data[0] != REPORT_ID_TESTING_RESP:
        return {}

    b2 = data[2]
    b3 = data[3]
    b4 = data[4]
    b12 = data[12]

    # Teclas ativas
    buttons = {}
    seq1 = [0, 1, 2, 3, 4, 5, 6, 7]
    for i, k in enumerate(seq1):
        buttons[k] = bool((b2 >> i) & 1)

    seq2 = [8, 9, 10, 11, 12, 13, 14, 15]
    for i, k in enumerate(seq2):
        buttons[k] = bool((b3 >> i) & 1)

    seq3 = [16, 17]
    for i, k in enumerate(seq3):
        buttons[k] = bool((b4 >> i) & 1)

    seq4 = [25, 26, 23, 24]
    for i, k in enumerate(seq4):
        buttons[k] = bool((b12 >> i) & 1)

    angle_raw = data[6]  # 0 a 255 (128 = centro)
    # Converter 128 em 0 graus (-100% a +100%)
    angle_norm = (angle_raw - 128) / 128.0

    acc = data[8]
    brake = data[9]
    clutch = data[10]

    gear_byte = data[13]
    gear_str = "N"
    if 1 <= gear_byte <= 6:
        gear_str = str(gear_byte)
    elif gear_byte == 255:
        gear_str = "R"

    return {
        "angleRaw": angle_raw,
        "angleNorm": angle_norm,
        "acc": acc,
        "brake": brake,
        "clutch": clutch,
        "gear": gear_str,
        "gearRaw": gear_byte,
        "buttons": buttons
    }
