"""Captura de dataset de keypoints (estilo kinivi) para entrenar el clasificador.

Basado en el modo de logging de kinivi/hand-gesture-recognition-mediapipe (app.py),
adaptado a MediaPipe Tasks (hand_tracker) y a nuestros 6 gestos. Puede capturar
desde la webcam o desde el stream de la ESP32-CAM.

Uso:
    python collect_keypoints.py                       # webcam
    python collect_keypoints.py --source mjpeg --stream-url http://192.168.1.99/stream

Controles:
    teclas 0..5  -> graba una muestra del gesto correspondiente (mano visible)
    q            -> salir

Escribe filas [label, f0..f41] en keypoint_classifier/keypoint.csv, exactamente el
formato que espera train_keypoint.py.
"""
import argparse
import csv
import os

import cv2

from gestures import GESTURES, NUM_GESTURES
from hand_tracker import HandTracker
from keypoint_preprocess import calc_landmark_list, pre_process_landmark
from video_source import open_source

CSV_PATH = os.path.join(os.path.dirname(__file__),
                        "keypoint_classifier", "keypoint.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["webcam", "mjpeg"], default="webcam")
    ap.add_argument("--stream-url", default="http://192.168.1.99/stream")
    args = ap.parse_args()

    counts = [0] * NUM_GESTURES
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as f:
            for row in csv.reader(f):
                if row:
                    counts[int(row[0])] += 1

    tracker = HandTracker()
    kind, src = open_source(args.source, args.stream_url)
    f = open(CSV_PATH, "a", newline="")
    writer = csv.writer(f)

    print("Gestos (tecla -> gesto):")
    for i, (name, label, sym) in enumerate(GESTURES):
        print(f"  [{i}] {label} {sym}")
    print("Manten un gesto y presiona su numero para grabar. q = salir.\n")

    try:
        while True:
            ok, frame = read(kind, src)
            if not ok:
                break
            if kind == "webcam":
                frame = cv2.flip(frame, 1)
            landmarks, _ = tracker.process(frame)
            if landmarks:
                tracker.draw(frame, landmarks)

            y = 22
            for i, (_, label, _) in enumerate(GESTURES):
                cv2.putText(frame, f"[{i}] {label}: {counts[i]}", (8, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                y += 20

            cv2.imshow("Captura de keypoints (q=salir)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if ord("0") <= key <= ord("5") and landmarks:
                label = key - ord("0")
                feats = pre_process_landmark(calc_landmark_list(frame, landmarks))
                writer.writerow([label, *feats])
                counts[label] += 1
    finally:
        f.close()
        src.release()
        cv2.destroyAllWindows()
        print(f"\nGuardado en {CSV_PATH}. Muestras por gesto: {counts}")


def read(kind, src):
    return src.read()


if __name__ == "__main__":
    main()
