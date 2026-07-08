"""Captura de dataset de gestos usando la webcam del computador.

Uso:
    python collect_data.py

Controles:
    - Teclas 0..5  -> graba una muestra del gesto correspondiente (mientras la
                      mano este visible). Manten presionado para grabar varias.
    - q            -> salir.

Genera/actualiza `data/landmarks.csv` con una fila por muestra:
    label, f0, f1, ..., f41

Recomendacion: junta ~200-300 muestras por gesto, variando angulo, distancia y
mano (izquierda/derecha) para que el modelo generalice.
"""
import csv
import os

import cv2
import mediapipe as mp

from gestures import GESTURES, NUM_GESTURES
from landmarks import normalize_landmarks

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "landmarks.csv")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    counts = [0] * NUM_GESTURES

    # si ya existe, contamos lo que hay para mostrar progreso
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as f:
            for row in csv.reader(f):
                if row:
                    counts[int(row[0])] += 1

    hands = mp.solutions.hands.Hands(
        max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5
    )
    draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    csv_file = open(CSV_PATH, "a", newline="")
    writer = csv.writer(csv_file)

    print("Gestos disponibles:")
    for i, (name, label, sym) in enumerate(GESTURES):
        print(f"  [{i}] {label} ({name})")
    print("Presiona 0..5 para grabar, q para salir.\n")

    try:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            current = None
            if result.multi_hand_landmarks:
                current = result.multi_hand_landmarks[0]
                draw.draw_landmarks(
                    frame, current, mp.solutions.hands.HAND_CONNECTIONS
                )

            y = 24
            for i, (_, label, _) in enumerate(GESTURES):
                cv2.putText(frame, f"[{i}] {label}: {counts[i]}", (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
                y += 22

            cv2.imshow("Captura de gestos (q para salir)", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if ord("0") <= key <= ord(str(NUM_GESTURES - 1)[0]) and current:
                label = key - ord("0")
                features = normalize_landmarks(current)
                writer.writerow([label] + features.tolist())
                counts[label] += 1
    finally:
        csv_file.close()
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nGuardado en {CSV_PATH}. Total por gesto: {counts}")


if __name__ == "__main__":
    main()
