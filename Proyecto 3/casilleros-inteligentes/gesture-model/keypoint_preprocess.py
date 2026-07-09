"""Preprocesamiento de landmarks — portado de kinivi/hand-gesture-recognition-mediapipe.

Fuente original (Apache-2.0):
  https://github.com/kinivi/hand-gesture-recognition-mediapipe  (app.py)
Adaptado para funcionar con nuestra deteccion via MediaPipe Tasks (hand_tracker.py),
cuyos landmarks exponen .x/.y normalizados 0..1.

Transformacion (identica a la del repo original):
  1. Coordenadas en pixeles.
  2. Relativas a la muneca (landmark 0).
  3. Aplanadas a una lista 1D de 42 valores.
  4. Normalizadas dividiendo por el maximo valor absoluto.
"""
import copy
import itertools


def calc_landmark_list(image, landmarks):
    """landmarks: lista de 21 puntos con .x/.y (0..1). -> [[px, py], ...]."""
    h, w = image.shape[0], image.shape[1]
    return [[min(int(lm.x * w), w - 1), min(int(lm.y * h), h - 1)]
            for lm in landmarks]


def pre_process_landmark(landmark_list):
    """[[px,py],...] (21) -> lista de 42 floats normalizados. (kinivi, textual)."""
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Coordenadas relativas a la muneca (indice 0)
    base_x, base_y = 0, 0
    for index, landmark_point in enumerate(temp_landmark_list):
        if index == 0:
            base_x, base_y = landmark_point[0], landmark_point[1]
        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

    # Aplanar a 1D
    temp_landmark_list = list(itertools.chain.from_iterable(temp_landmark_list))

    # Normalizar por el maximo valor absoluto
    max_value = max(list(map(abs, temp_landmark_list))) or 1

    return [n / max_value for n in temp_landmark_list]
