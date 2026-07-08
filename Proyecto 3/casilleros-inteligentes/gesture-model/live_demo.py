"""Demo en vivo: reconoce gestos con la webcam y detecta la secuencia de 4 gestos
que forma una clave. Sirve para validar el modelo antes de pasarlo a la ESP32 y
para grabar el video de las entregas.

Uso:
    python live_demo.py

Un gesto se "confirma" cuando se mantiene estable por ~1 segundo (para evitar
falsos positivos al pasar entre gestos). Al confirmar 4 gestos se imprime la clave.
"""
import os
import time
from collections import deque

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

from gestures import GESTURES, KEY_LENGTH, LABELS
from landmarks import normalize_landmarks

BASE = os.path.dirname(__file__)
KERAS_PATH = os.path.join(BASE, "models", "gesture_model.keras")

STABLE_FRAMES = 15      # frames seguidos con el mismo gesto para confirmarlo
CONF_THRESHOLD = 0.85   # confianza minima


def main():
    if not os.path.exists(KERAS_PATH):
        raise SystemExit("No hay modelo. Corre: python train.py")
    model = tf.keras.models.load_model(KERAS_PATH)

    hands = mp.solutions.hands.Hands(
        max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5
    )
    draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    recent = deque(maxlen=STABLE_FRAMES)
    entered_key = []
    last_confirmed = None
    cooldown_until = 0.0

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        pred_label, conf = None, 0.0
        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            draw.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
            feats = normalize_landmarks(hand)[None, :]
            probs = model.predict(feats, verbose=0)[0]
            pred_label = int(np.argmax(probs))
            conf = float(probs[pred_label])
            recent.append(pred_label if conf >= CONF_THRESHOLD else -1)
        else:
            recent.append(-1)

        # confirmar gesto estable
        now = time.time()
        if (len(recent) == STABLE_FRAMES and len(set(recent)) == 1
                and recent[0] != -1 and now >= cooldown_until):
            gesture = recent[0]
            if gesture != last_confirmed:
                entered_key.append(gesture)
                last_confirmed = gesture
                cooldown_until = now + 1.0
                if len(entered_key) == KEY_LENGTH:
                    print("Clave ingresada:", entered_key,
                          "->", " ".join(GESTURES[g][2] for g in entered_key))
                    entered_key = []
                    last_confirmed = None

        # HUD
        txt = f"{LABELS[pred_label]} ({conf:.2f})" if pred_label is not None else "sin mano"
        cv2.putText(frame, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0), 2)
        seq = " ".join(GESTURES[g][2] for g in entered_key) or "(vacia)"
        cv2.putText(frame, f"Clave: {seq}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        cv2.imshow("Demo gestos (q para salir)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
