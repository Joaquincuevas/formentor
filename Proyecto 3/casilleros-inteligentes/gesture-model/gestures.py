"""Definicion de los gestos soportados por el sistema.

El enunciado exige manejar AL MENOS 6 gestos distintos. Cada clave de casillero es
una secuencia de 4 de estos gestos (indices 0..5).

El indice (posicion en la lista) es lo que viaja por MQTT como parte de la clave,
por lo que este orden debe ser el MISMO en el firmware, el modelo y el sistema de
administracion. No reordenar sin regenerar el modelo y las claves.
"""

# nombre interno, etiqueta legible, emoji/figura para el email al dueno
GESTURES = [
    ("palm", "Palma abierta", "\U0001F590"),      # 0  🖐
    ("fist", "Puno cerrado", "✊"),            # 1  ✊
    ("peace", "Victoria / dos dedos", "✌"),   # 2  ✌
    ("thumbs_up", "Pulgar arriba", "\U0001F44D"),  # 3  👍
    ("point", "Indice apuntando", "☝"),       # 4  ☝
    ("ok", "Senal de OK", "\U0001F44C"),           # 5  👌
]

NUM_GESTURES = len(GESTURES)
KEY_LENGTH = 4  # gestos por clave

NAMES = [g[0] for g in GESTURES]
LABELS = [g[1] for g in GESTURES]
SYMBOLS = [g[2] for g in GESTURES]


def name_to_index(name: str) -> int:
    return NAMES.index(name)


def key_to_symbols(key):
    """[2, 0, 5, 1] -> '✌ 🖐 👌 ✊' (para mostrar al dueno del casillero)."""
    return " ".join(SYMBOLS[i] for i in key)
