"""Utilidades para convertir una mano detectada por MediaPipe en un vector de
caracteristicas normalizado, independiente de la posicion y escala de la mano.

MediaPipe Hands entrega 21 landmarks (x, y, z) por mano. Para clasificar el gesto
NO usamos los pixeles crudos (eso seria pesado e inestable), sino las coordenadas
relativas de los landmarks:

  1. Se toma la muneca (landmark 0) como origen.
  2. Se restan sus coordenadas a todos los puntos (invariancia a traslacion).
  3. Se divide por la distancia maxima (invariancia a escala).

Resultado: 42 features (21 puntos x, y). Descartamos z porque en la ESP32-CAM la
profundidad es poco confiable y encarece el modelo. Este mismo preprocesamiento
debe replicarse en el dispositivo embebido.
"""
import numpy as np

NUM_LANDMARKS = 21
FEATURE_DIM = NUM_LANDMARKS * 2  # 42


def normalize_landmarks(hand_landmarks) -> np.ndarray:
    """hand_landmarks: objeto de MediaPipe (.landmark con .x .y). -> vector (42,)."""
    pts = np.array([[lm.x, lm.y] for lm in hand_landmarks.landmark], dtype=np.float32)
    return normalize_points(pts)


def normalize_points(pts: np.ndarray) -> np.ndarray:
    """pts: array (21, 2) con coordenadas absolutas -> vector (42,) normalizado."""
    base = pts[0].copy()          # muneca como origen
    rel = pts - base
    max_dist = np.max(np.linalg.norm(rel, axis=1))
    if max_dist > 1e-6:
        rel = rel / max_dist
    return rel.flatten()
