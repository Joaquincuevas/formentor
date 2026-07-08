"""Wrapper de deteccion de manos usando la API MediaPipe Tasks (HandLandmarker).

Las builds recientes de mediapipe (>=0.10.3x) en algunas plataformas ya NO incluyen
la API legacy `mp.solutions.hands`, solo `mp.tasks`. Este modulo ofrece una interfaz
simple e independiente de esa diferencia:

    tracker = HandTracker()
    landmarks, handedness = tracker.process(bgr_frame)  # 21 landmarks o (None, None)
    tracker.draw(bgr_frame, landmarks)

`landmarks` es una lista de 21 objetos con atributos .x .y .z (normalizados 0..1),
compatible con el resto del codigo (gestures/classify).
"""
import os

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task")

# conexiones de la mano (para dibujar), indices de landmarks
_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),            # pulgar
    (0, 5), (5, 6), (6, 7), (7, 8),            # indice
    (5, 9), (9, 10), (10, 11), (11, 12),       # medio
    (9, 13), (13, 14), (14, 15), (15, 16),     # anular
    (13, 17), (17, 18), (18, 19), (19, 20),    # menique
    (0, 17),                                    # palma
]


class HandTracker:
    def __init__(self, model_path=MODEL_PATH, min_conf=0.5):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Falta {model_path}. Descargalo con:\n"
                "curl -sL -o models/hand_landmarker.task "
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                "hand_landmarker/float16/1/hand_landmarker.task")
        opts = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            num_hands=1,
            min_hand_detection_confidence=min_conf,
            min_tracking_confidence=min_conf,
            running_mode=vision.RunningMode.IMAGE,
        )
        self.detector = vision.HandLandmarker.create_from_options(opts)

    def process(self, bgr_frame):
        """Devuelve (landmarks, handedness) o (None, None)."""
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        res = self.detector.detect(mp_image)
        if not res.hand_landmarks:
            return None, None
        handed = "Right"
        if res.handedness and res.handedness[0]:
            handed = res.handedness[0][0].category_name  # 'Left' / 'Right'
        return res.hand_landmarks[0], handed

    def draw(self, bgr_frame, landmarks):
        if not landmarks:
            return
        h, w = bgr_frame.shape[:2]
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
        for a, b in _CONNECTIONS:
            cv2.line(bgr_frame, pts[a], pts[b], (255, 255, 255), 1)
        for p in pts:
            cv2.circle(bgr_frame, p, 3, (0, 255, 0), -1)
