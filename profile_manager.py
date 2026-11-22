"""
Gerenciador de Perfis de Jogos e Guias de Configuração Nativa para o Volante PCYES W270.
Inclui otimizações de 3.2 Nm e 1080° para simuladores e jogos sem suporte oficial de fábrica.
"""

import json
import os
import re
import shutil
from typing import List, Dict, Any, Optional

PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")

DEFAULT_PROFILES = [
    {
        "id": "assetto_corsa",
        "name": "Assetto Corsa",
        "game": "Assetto Corsa",
        "category": "Simulador GT & Drift",
        "mode_required": "D-Input",
        "description": "Fidelidade máxima para sentir zebras, transferência de peso e limite de aderência.",
        "angle": 900,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 0,
        "damping": 50,
        "friction": 60,
        "inertia": 50,
        "roadSensitivity": 90,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                50,
                60
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No Content Manager ou menu do AC: Configurações ➔ Controles ➔ Volante (DirectInput).",
            "Ganho Geral de FFB: 80% (ideal para os motores duplos de 3.2 Nm evitarem clipping).",
            "Filtro: 0% | Força Mínima: 0% | Zebras: 40% | Efeitos de Pista: 30% | Derrapagem (Slip): 20%.",
            "Efeito de Subesterço: DESATIVADO (garante alinhamento físico real e contraesterço veloz)."
        ],
        "keymap": {}
    },
    {
        "id": "assetto_corsa_competizione",
        "name": "Assetto Corsa Competizione",
        "game": "Assetto Corsa Competizione (ACC)",
        "category": "Simulador GT3 / GT4 Oficial",
        "mode_required": "D-Input",
        "description": "Configuração refinada para o motor de física ACC com telemetria direta de suspensão.",
        "angle": 900,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 0,
        "damping": 40,
        "friction": 50,
        "inertia": 50,
        "roadSensitivity": 90,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                50,
                60
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Opções ➔ Controles ➔ Tipo de Dispositivo: Volante Personalizado.",
            "Ganho (Gain): 70% a 80% | Força Mínima: 0% | Dynamic Damping: 100%.",
            "Efeitos de Estrada (Road Effects): 20% a 30%.",
            "Trava de Direção (Steer Lock): 900° (o ACC adapta automaticamente para cada carro GT3)."
        ],
        "keymap": {}
    },
    {
        "id": "automobilista_1",
        "name": "Automobilista (AMS 1)",
        "game": "Automobilista",
        "category": "Simulador Clássico Brasileiro",
        "mode_required": "D-Input",
        "description": "Física do motor rFactor 1 com FFB invertido necessário para o torque correto.",
        "angle": 900,
        "ffb": 80,
        "ffbReverse": True,
        "spring": 10,
        "damping": 40,
        "friction": 50,
        "inertia": 50,
        "roadSensitivity": 80,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Configurações ➔ Controles ➔ Volante Personalizado.",
            "Força de FFB: Configure valor NEGATIVO (ex: -80%) se não usar o botão Inverter FFB do app.",
            "Tipo de Efeitos: RealFeel Puro | Suavização: 0 a 2.",
            "Mapeie o Câmbio em H para as categorias de Stock Car antigas e Copa Classic."
        ],
        "keymap": {}
    },
    {
        "id": "automobilista_2",
        "name": "Automobilista 2 (AMS 2)",
        "game": "Automobilista 2",
        "category": "Simulador Nacional / Stock Car",
        "mode_required": "D-Input",
        "description": "Ajuste fino para Stock Car Pro Series, Copa Truck, Fórmula 1 e GT3 no Madness Engine.",
        "angle": 900,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 20,
        "damping": 40,
        "friction": 40,
        "inertia": 40,
        "roadSensitivity": 80,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Opções ➔ Controles: Tipo = 'Personalizado' (Custom Wheel).",
            "Execute a 'Calibração do Volante' (gire tudo até 900° e volte a 90°).",
            "Perfil de FFB: 'Default+' | Ganho: 80% | Low Force Boost (LFB): 10 | FX: 40 | Damping: 30.",
            "Para Copa Truck: Aumente o ângulo do W270 para 1080° para simulação fiel do caminhão."
        ],
        "keymap": {}
    },
    {
        "id": "beamng_drive",
        "name": "BeamNG.drive (Física Real)",
        "game": "BeamNG.drive",
        "category": "Simulador de Física & Deformação",
        "mode_required": "D-Input",
        "description": "Otimizado para a física de deformação de chassi em tempo real do BeamNG a 1000 Hz.",
        "angle": 900,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 30,
        "damping": 40,
        "friction": 40,
        "inertia": 50,
        "roadSensitivity": 90,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                60,
                60
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No BeamNG: Opções ➔ Controles ➔ Hardware ➔ 'PCYES W270'.",
            "Em 'Force Feedback': Marque 'Habilitar FFB' e vincule ao Eixo do Volante.",
            "Força de FFB: 280 a 320 (escala ideal para os 3.2 Nm) | Taxa de Atualização: 1000 Hz.",
            "Suavização: 150 (elimina oscilações indesejadas em retas sem perder sensibilidade de terreno).",
            "Se o volante puxar sozinho ao esterçar, clique em 'Inverter FFB'."
        ],
        "keymap": {}
    },
    {
        "id": "bus_simulator_18",
        "name": "Bus Simulator 18",
        "game": "Bus Simulator 18",
        "category": "Simulador de Ônibus Urbano",
        "mode_required": "D-Input",
        "description": "Ângulo máximo de 1080° com volante pesado simulando a coluna de direção de ônibus.",
        "angle": 1080,
        "ffb": 70,
        "ffbReverse": False,
        "spring": 70,
        "damping": 80,
        "friction": 70,
        "inertia": 90,
        "roadSensitivity": 40,
        "accChart": [
            [
                0,
                0
            ],
            [
                40,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Configurações ➔ Jogabilidade ➔ Dispositivo de Entrada: Volante.",
            "Graus de Rotação: 1080° | Sensibilidade de Direção: 1.0 (Linear) | Zona Morta: 0%.",
            "Mapeie as Borboletas (Paddles) para abrir/fechar portas dianteiras e traseiras dos passageiros.",
            "Use o D-Pad para olhar nos espelhos retrovisores e bilhetagem."
        ],
        "keymap": {}
    },
    {
        "id": "carx_drift",
        "name": "CarX Drift Racing Online",
        "game": "CarX Drift Racing Online",
        "category": "Drift & Manobras",
        "mode_required": "D-Input",
        "description": "Retorno ultrarrápido para transições suaves de drift e contraesterço sem travamentos.",
        "angle": 900,
        "ffb": 90,
        "ffbReverse": False,
        "spring": 40,
        "damping": 20,
        "friction": 20,
        "inertia": 20,
        "roadSensitivity": 70,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                40
            ],
            [
                60,
                80
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                60
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                50,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No CarX: Assistência de Direção = DESATIVADA (fundamental para pilotar no volante).",
            "Ângulo de Giro no CarX = 900°.",
            "Suavização de FFB = 0.2 a 0.3 (quanto menor, mais rápido o volante solta para a transição de drift).",
            "Mapeie o Freio de Mão para a chave de handbrake do câmbio do W270 (botão 25)."
        ],
        "keymap": {}
    },
    {
        "id": "city_car_driving",
        "name": "City Car Driving (Autoescola)",
        "game": "City Car Driving",
        "category": "Simulador Urbano",
        "mode_required": "D-Input",
        "description": "Direção urbana realista a 1080°, controle de ponto de embreagem e seta no volante.",
        "angle": 1080,
        "ffb": 70,
        "ffbReverse": False,
        "spring": 70,
        "damping": 60,
        "friction": 60,
        "inertia": 70,
        "roadSensitivity": 40,
        "accChart": [
            [
                0,
                0
            ],
            [
                40,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                40,
                30
            ],
            [
                70,
                60
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No menu Controles: selecione 'Volante'.",
            "Mapeie o Eixo X para Direção, Eixo Y para Acelerador, Eixo Z para Freio e Rotação Z para Embreagem.",
            "Ative 'Embreagem Manual' e 'Câmbio H' para treinamento realista de trânsito.",
            "Use o D-Pad para olhar para os lados e os botões L1/R1 para acionar as setas de conversão."
        ],
        "keymap": {}
    },
    {
        "id": "cms_2018",
        "name": "Car Mechanic Simulator 2018",
        "game": "Car Mechanic Simulator 2018",
        "category": "Oficina & Pista de Testes",
        "mode_required": "X-Input ou D-Input",
        "description": "Configuração rápida para testar os veículos montados na pista de testes e aceleração.",
        "angle": 900,
        "ffb": 60,
        "ffbReverse": False,
        "spring": 70,
        "damping": 60,
        "friction": 60,
        "inertia": 70,
        "roadSensitivity": 50,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "DICA: O CMS 2018 reconhece nativamente controles no modo X-Input.",
            "Alterne o botão 'Modo' no cabeçalho do app para 'PC: X-Input' (LED Azul no volante).",
            "Na Pista de Teste: O volante responderá imediatamente na direção e os pedais no acelerador/freio."
        ],
        "keymap": {}
    },
    {
        "id": "cms_2021",
        "name": "Car Mechanic Simulator 2021",
        "game": "Car Mechanic Simulator 2021",
        "category": "Oficina, Dinamômetro & Pista",
        "mode_required": "X-Input ou D-Input",
        "description": "Suporte aprimorado para teste de suspensão, alinhamento e voltas rápidas no circuito.",
        "angle": 900,
        "ffb": 70,
        "ffbReverse": False,
        "spring": 70,
        "damping": 60,
        "friction": 60,
        "inertia": 70,
        "roadSensitivity": 60,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Configurações ➔ Controles ➔ Direção: Conecte o volante e mapeie os eixos.",
            "Sensibilidade: 100% | Zonas Mortas: 0%.",
            "Ao testar carros no circuito fechado, o volante oferece centralização e peso progressivo."
        ],
        "keymap": {}
    },
    {
        "id": "default_w270",
        "name": "Padrão de Fábrica PCYES W270",
        "game": "Configuração Padrão W270",
        "category": "Padrão de Fábrica",
        "mode_required": "D-Input",
        "description": "Configuração balanceada recomendada pela engenharia da PCYES para uso geral.",
        "angle": 900,
        "ffb": 70,
        "ffbReverse": False,
        "spring": 60,
        "damping": 60,
        "friction": 70,
        "inertia": 70,
        "roadSensitivity": 50,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Perfil padrão balanceado para qualquer novo jogo que você queira experimentar.",
            "Caso sinta o volante muito pesado em manobras lentas, reduza a 'Fricção' ou 'Amortecimento'."
        ],
        "keymap": {}
    },
    {
        "id": "dirt_rally_2",
        "name": "Dirt Rally 2.0 & EA WRC",
        "game": "Dirt Rally 2.0 / EA SPORTS WRC",
        "category": "Rally / Todo Terreno",
        "mode_required": "D-Input",
        "description": "Contraesterço ágil a 540°, resposta imediata para saltos, poças de lama e cascalho.",
        "angle": 540,
        "ffb": 90,
        "ffbReverse": False,
        "spring": 40,
        "damping": 30,
        "friction": 40,
        "inertia": 30,
        "roadSensitivity": 100,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                30
            ],
            [
                50,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No Dirt Rally: Calibre o volante a 540° ou ative 'Soft Lock' a 540°.",
            "Saturação da Direção: 100%, Zona Morta: 0%, Linearidade: 0.",
            "Torque / Alinhamento Automático: 80%, Atrito da Roda: 30%, Atrito do Pneu: 40%, Suspensão: 80%."
        ],
        "keymap": {}
    },
    {
        "id": "euro_truck_2",
        "name": "Euro Truck Simulator 2",
        "game": "Euro Truck Simulator 2",
        "category": "Simulador de Caminhão & Cargas",
        "mode_required": "D-Input",
        "description": "Rotação total a 1080°, suporte a divisor de caixa alta/baixa e peso hidráulico de direção.",
        "angle": 1080,
        "ffb": 60,
        "ffbReverse": False,
        "spring": 70,
        "damping": 80,
        "friction": 70,
        "inertia": 90,
        "roadSensitivity": 40,
        "accChart": [
            [
                0,
                0
            ],
            [
                40,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Assistente de Entrada: Selecione 'Volante' ➔ 'Câmbio em H'.",
            "Layout do Câmbio: Escolha 'Range' ou 'Splitter' (para marchas de 1 a 12 ou 18).",
            "Mapeie o botão lateral do câmbio W270 (botão 26) como 'Divisor de Marchas 1'.",
            "Sensibilidade da Direção = 100% (Linear) | Não Linearidade = 0%.",
            "Centragem em Alta Velocidade = 70% | Atrito da Superfície = 80%."
        ],
        "keymap": {}
    },
    {
        "id": "f1_24",
        "name": "F1 23 & F1 24",
        "game": "EA SPORTS F1 23 / F1 24",
        "category": "Fórmula 1 Monoposto",
        "mode_required": "D-Input",
        "description": "Giro curto de 360° para curvas fechadas em circuitos como Mônaco sem tirar as mãos.",
        "angle": 360,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 30,
        "damping": 30,
        "friction": 30,
        "inertia": 30,
        "roadSensitivity": 90,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                80
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                60,
                80
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No F1: Acesse Configurações de Controle ➔ Calibração.",
            "Ângulo de Rotação Máxima da Direção = 360°.",
            "Zona Morta da Direção = 0, Linearidade da Direção = 0.",
            "Em Force Feedback: Força do Efeito = 80%, Efeitos de Pista = 40%, Efeitos de Zebra = 40%, Amortecedor = 20%."
        ],
        "keymap": {}
    },
    {
        "id": "f1_25_26",
        "name": "F1 2025 / 2026",
        "game": "EA SPORTS F1 25 / F1 26",
        "category": "Fórmula 1 Monoposto",
        "mode_required": "D-Input",
        "description": "Giro ágil de 400° ajustado para os monopostos e regulamentos de 2025 e 2026 com resposta de alta fidelidade.",
        "angle": 400,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 30,
        "damping": 30,
        "friction": 30,
        "inertia": 30,
        "roadSensitivity": 90,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                80
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                60,
                80
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No F1: Acesse Configurações de Controle ➔ Calibração.",
            "Ângulo de Rotação Máxima da Direção = 400°.",
            "Zona Morta da Direção = 0, Linearidade da Direção = 0.",
            "Em Force Feedback: Força do Efeito = 80%, Efeitos de Pista = 40%, Efeitos de Zebra = 40%, Amortecedor = 20%."
        ],
        "keymap": {}
    },
    {
        "id": "forza_horizon",
        "name": "Forza Horizon (FH5 / FH6)",
        "game": "Forza Horizon",
        "category": "Mundo Aberto / Arcade-Sim",
        "mode_required": "D-Input (Perfil Personalizado)",
        "description": "Corrige o problema de direção dura e falta de contraesterço em drift e corridas.",
        "angle": 540,
        "ffb": 70,
        "ffbReverse": True,
        "spring": 50,
        "damping": 40,
        "friction": 40,
        "inertia": 40,
        "roadSensitivity": 70,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No menu do Forza: Configurações de Controle ➔ Roda ➔ 'Perfil Personalizado 1'.",
            "Mapeie manualmente: Esterçar Esquerda/Direita, Acelerador, Freio e Embreagem.",
            "Em 'Controles Avançados': Escala de FFB = 75, Força de Alinhamento = 80, Trilha Mecânica = 65, Amortecimento Central = 25.",
            "Todas as Zonas Mortas Internas = 0, Zonas Mortas Externas = 100."
        ],
        "keymap": {}
    },
    {
        "id": "mon_bazou",
        "name": "Mon Bazou",
        "game": "Mon Bazou",
        "category": "Sobrevivência Automotiva & Tuning",
        "mode_required": "D-Input",
        "description": "Calibração completa para câmbio manual, embreagem real e direção de ferro-velho/tuning.",
        "angle": 900,
        "ffb": 70,
        "ffbReverse": False,
        "spring": 60,
        "damping": 50,
        "friction": 50,
        "inertia": 50,
        "roadSensitivity": 60,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Opções ➔ Controles: Ative a opção 'Wheel Input'.",
            "Mapeie o Volante para o Eixo X e configure Acelerador, Freio e Embreagem.",
            "Em 'Transmissão': Selecione 'Manual with Clutch' para usar o H-Shifter e os pedais Hall.",
            "Ajuste a Deadzone para 0% para resposta imediata sem atraso nos pedais."
        ],
        "keymap": {}
    },
    {
        "id": "my_summer_car",
        "name": "My Summer Car",
        "game": "My Summer Car",
        "category": "Simulador Finlandês de Mecânica",
        "mode_required": "D-Input",
        "description": "Alinhamento fiel para pilotar a van, o trator e o Satsuma pelas estradas de terra.",
        "angle": 900,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 50,
        "damping": 50,
        "friction": 60,
        "inertia": 60,
        "roadSensitivity": 80,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                40,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Menu de Configurações ➔ Car Controls ➔ Ative 'Force Feedback'.",
            "Mapeie o Volante no eixo Steering e marque 'Non-linear: 0%'.",
            "Pedais: Se o carro acelerar sozinho, clique no botão 'Invert' no menu do jogo.",
            "Câmbio: Mapeie as marchas do H-Shifter W270 (1 a 6 + Ré).",
            "Dica: O Satsuma sem alinhamento nas rodas puxará o volante exatamente como um carro real!"
        ],
        "keymap": {}
    },
    {
        "id": "need_for_speed",
        "name": "Need for Speed (Unbound / Heat)",
        "game": "Need for Speed Unbound / Heat / Payback",
        "category": "Arcade / Corridas Clandestinas",
        "mode_required": "X-Input",
        "description": "Como o NFS não suporta volantes DirectInput genericamente, utiliza emulação X-Input nativa.",
        "angle": 360,
        "ffb": 60,
        "ffbReverse": False,
        "spring": 50,
        "damping": 50,
        "friction": 50,
        "inertia": 40,
        "roadSensitivity": 50,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "ATENÇÃO: A franquia Need for Speed no PC NÃO tem suporte nativo para volantes DirectInput genéricos.",
            "SOLUÇÃO: Alterne o W270 para o 'Modo X-Input' pelo botão no topo do aplicativo.",
            "No Modo X-Input, o jogo reconhecerá o volante como um controle oficial Xbox 360/One, funcionando perfeitamente em todas as corridas, menus e nitro!",
            "Recomendamos ângulo de 360° a 540° para respostas rápidas de drift e curvas de alta velocidade."
        ],
        "keymap": {}
    },
    {
        "id": "snowrunner",
        "name": "SnowRunner & MudRunner",
        "game": "SnowRunner / Expeditions",
        "category": "Off-Road Pesado",
        "mode_required": "D-Input",
        "description": "Amortecimento reforçado para simular terreno pesado de lama, atoleiros e neve.",
        "angle": 900,
        "ffb": 90,
        "ffbReverse": False,
        "spring": 60,
        "damping": 90,
        "friction": 80,
        "inertia": 80,
        "roadSensitivity": 60,
        "accChart": [
            [
                0,
                0
            ],
            [
                40,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "No SnowRunner: Configurações ➔ Volante ➔ Tipo de Volante: 'DirectInput'.",
            "Mapeie os eixos manualmente em 'Configurar Controles'.",
            "Ganho de FFB = 80%, Fricção do Terreno = 80%, Força de Centralização = 50%."
        ],
        "keymap": {}
    },
    {
        "id": "the_crew_2",
        "name": "The Crew 2",
        "game": "The Crew 2",
        "category": "Mundo Aberto EUA / Arcade",
        "mode_required": "D-Input ou X-Input",
        "description": "Resposta dinâmica e rápida a 540° para carros de rua, hipercarros e off-road.",
        "angle": 540,
        "ffb": 70,
        "ffbReverse": False,
        "spring": 50,
        "damping": 40,
        "friction": 50,
        "inertia": 50,
        "roadSensitivity": 70,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Opções ➔ Controles ➔ Volante: Selecione Dispositivo Personalizado.",
            "Linearidade da Direção: 50% (Linear 1:1) | Zona Morta: 0%.",
            "Fixação de Ângulo: 540° | Força de Force Feedback: 70%.",
            "Use as Borboletas (Paddle Shifters) para trocas instantâneas em corridas de alta velocidade."
        ],
        "keymap": {}
    },
    {
        "id": "wrc_10",
        "name": "WRC 10 FIA World Rally",
        "game": "WRC 10",
        "category": "Rally Oficial FIA",
        "mode_required": "D-Input",
        "description": "Giro ágil de 540° com contraesterço agressivo para cascalho, neve e asfalto.",
        "angle": 540,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 40,
        "damping": 60,
        "friction": 70,
        "inertia": 60,
        "roadSensitivity": 90,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                60,
                80
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Opções ➔ Controles ➔ 'PCYES W270'.",
            "Força Geral de FFB: 80% | Fricção de Pneu: 60% | Terreno/Solo: 70% | Colisão: 50%.",
            "Bloqueio de Direção (Soft Lock): 540°.",
            "Mapeie a chave do câmbio W270 (botão 25) para o Freio de Mão hidráulico de rally."
        ],
        "keymap": {}
    },
    {
        "id": "wrc_generations",
        "name": "WRC Generations",
        "game": "WRC Generations",
        "category": "Rally Híbrido Rally1",
        "mode_required": "D-Input",
        "description": "Sensibilidade de torque de tração integral e resposta de esterço para carros híbridos Rally1.",
        "angle": 540,
        "ffb": 80,
        "ffbReverse": False,
        "spring": 40,
        "damping": 50,
        "friction": 70,
        "inertia": 60,
        "roadSensitivity": 90,
        "accChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                60,
                80
            ],
            [
                100,
                100
            ]
        ],
        "brakeChart": [
            [
                0,
                0
            ],
            [
                20,
                20
            ],
            [
                60,
                70
            ],
            [
                100,
                100
            ]
        ],
        "clutchChart": [
            [
                0,
                0
            ],
            [
                30,
                30
            ],
            [
                70,
                70
            ],
            [
                100,
                100
            ]
        ],
        "in_game_tips": [
            "Opções ➔ Jogabilidade ➔ Controles: Detectar Volante.",
            "Torque de Autoalinhamento (SAT): 80% | Suspensão: 60% | Deslizamento de Pneu: 60%.",
            "Limite Físico: 540° | Zonas mortas: 0%.",
            "Mapeie o Freio de Mão no botão 25 do câmbio para curvas fechadas em cotovelo (Hairpin)."
        ],
        "keymap": {}
    }
]


class ProfileManager:
    def __init__(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        self._deleted_file = os.path.join(PROFILES_DIR, ".deleted_profiles.json")
        self._ensure_defaults()

    def _get_deleted_ids(self) -> set:
        if os.path.exists(self._deleted_file):
            try:
                with open(self._deleted_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return set(data)
            except Exception:
                pass
        return set()

    def _save_deleted_ids(self, deleted_ids: set):
        try:
            with open(self._deleted_file, "w", encoding="utf-8") as f:
                json.dump(sorted(list(deleted_ids)), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ProfileManager] Erro ao salvar lista de excluídos: {e}")

    @staticmethod
    def _sanitize_id(profile_id: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", str(profile_id or "")).strip("_")
        return safe or "perfil"

    def _profile_path(self, profile_id: str) -> str:
        safe_id = self._sanitize_id(profile_id)
        return os.path.join(PROFILES_DIR, f"{safe_id}.json")

    def _ensure_defaults(self):
        deleted_ids = self._get_deleted_ids()
        for prof in DEFAULT_PROFILES:
            if prof["id"] in deleted_ids and prof["id"] not in ("padrao", "default_w270"):
                continue
            filepath = self._profile_path(prof["id"])
            # Cria arquivos padrão apenas se ainda não existirem, preservando edições do usuário
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(prof, f, indent=4, ensure_ascii=False)

    def list_profiles(self) -> List[Dict[str, Any]]:
        profiles = []
        for filename in sorted(os.listdir(PROFILES_DIR)):
            if filename.endswith(".json") and not filename.startswith("."):
                path = os.path.join(PROFILES_DIR, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        profiles.append(data)
                except Exception as e:
                    print(f"[ProfileManager] Erro ao ler {filename}: {e}")
        return profiles

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        path = self._profile_path(profile_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ProfileManager] Erro ao carregar {profile_id}: {e}")
        return None

    def save_profile(self, profile: Dict[str, Any]) -> bool:
        raw_id = profile.get("id") or profile.get("name", "perfil").lower().replace(" ", "_")
        profile_id = self._sanitize_id(raw_id)
        profile["id"] = profile_id
        path = self._profile_path(profile_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=4, ensure_ascii=False)
            deleted_ids = self._get_deleted_ids()
            if profile_id in deleted_ids:
                deleted_ids.discard(profile_id)
                self._save_deleted_ids(deleted_ids)
            return True
        except Exception as e:
            print(f"[ProfileManager] Erro ao salvar {profile_id}: {e}")
            return False

    def delete_profile(self, profile_id: str) -> bool:
        safe_id = self._sanitize_id(profile_id)
        if safe_id in ("padrao", "default_w270"):
            return False
        path = self._profile_path(safe_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                default_ids = {p["id"] for p in DEFAULT_PROFILES}
                if safe_id in default_ids:
                    deleted_ids = self._get_deleted_ids()
                    deleted_ids.add(safe_id)
                    self._save_deleted_ids(deleted_ids)
                return True
            except Exception as e:
                print(f"[ProfileManager] Erro ao deletar: {e}")
        return False

    def export_profile(self, profile_id: str, dest_path: str) -> bool:
        src = self._profile_path(profile_id)
        if os.path.exists(src):
            try:
                shutil.copyfile(src, dest_path)
                return True
            except Exception as e:
                print(f"[ProfileManager] Erro ao exportar: {e}")
        return False

    def import_profile(self, src_path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(src_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "name" in data and "angle" in data:
                self.save_profile(data)
                return data
        except Exception as e:
            print(f"[ProfileManager] Erro ao importar: {e}")
        return None
