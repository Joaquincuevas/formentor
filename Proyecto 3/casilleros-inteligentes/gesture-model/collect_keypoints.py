"""Captura de dataset de keypoints (estilo kinivi) para entrenar el clasificador.

Basado en el modo de logging de kinivi/hand-gesture-recognition-mediapipe (app.py),
adaptado a MediaPipe Tasks (hand_tracker) y a nuestros 6 gestos. Puede capturar
desde la webcam o desde el stream de la ESP32-CAM.

NO guarda imagenes: de cada frame extrae los 21 landmarks de la mano, los normaliza
(relativo a la muneca + escala) y guarda 42 numeros por muestra. Eso hace el modelo
diminuto e invariante a fondo/iluminacion/posicion.

Uso:
    python collect_keypoints.py                       # webcam (recomendado)
    python collect_keypoints.py --target 120          # meta de muestras por gesto
    python collect_keypoints.py --source mjpeg --stream-url http://192.168.1.95/stream

Controles:
    0..5    -> EMPIEZA a grabar ese gesto en continuo (graba cada frame con mano).
               Presiona el mismo numero otra vez, o ESPACIO, para PARAR.
               Para automaticamente al llegar a la meta.
    d       -> borra la ultima muestra grabada (deshacer)
    q       -> salir y guardar

Consejo: mientras graba un gesto, mueve/rota/inclina lentamente la mano y acercala/
alejala. Asi el dataset cubre variaciones y el modelo generaliza mucho mejor.

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


def load_counts():
    counts = [0] * NUM_GESTURES
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as f:
            for row in csv.reader(f):
                if row:
                    counts[int(row[0])] += 1
    return counts


def rewrite_without_last(label):
    """Elimina la ultima fila con esa etiqueta (deshacer)."""
    if not os.path.exists(CSV_PATH):
        return False
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.reader(f))
    for i in range(len(rows) - 1, -1, -1):
        if rows[i] and int(rows[i][0]) == label:
            del rows[i]
            with open(CSV_PATH, "w", newline="") as f:
                csv.writer(f).writerows(rows)
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["webcam", "mjpeg"], default="webcam")
    ap.add_argument("--stream-url", default="http://192.168.1.95/stream")
    ap.add_argument("--target", type=int, default=100,
                    help="muestras objetivo por gesto (default 100)")
    args = ap.parse_args()

    counts = load_counts()
    tracker = HandTracker()
    kind, src = open_source(args.source, args.stream_url)

    print("Gestos (tecla -> gesto):")
    for i, (_, label, sym) in enumerate(GESTURES):
        print(f"  [{i}] {label} {sym}")
    print("\nPresiona un numero para GRABAR en continuo; mismo numero o ESPACIO para "
          "PARAR.\nMueve la mano mientras grabas. d = deshacer, q = salir.\n")

    f = open(CSV_PATH, "a", newline="")
    writer = csv.writer(f)
    recording = None  # gesto que se esta grabando, o None
    last_label = None

    try:
        while True:
            ok, frame = src.read()
            if not ok:
                break
            if kind == "webcam":
                frame = cv2.flip(frame, 1)
            landmarks, _ = tracker.process(frame)
            if landmarks:
                tracker.draw(frame, landmarks)

            # grabacion continua
            if recording is not None and landmarks:
                feats = pre_process_landmark(calc_landmark_list(frame, landmarks))
                writer.writerow([recording, *feats])
                counts[recording] += 1
                last_label = recording
                if counts[recording] >= args.target:
                    print(f"  meta alcanzada para [{recording}] "
                          f"{GESTURES[recording][1]} ({counts[recording]})")
                    recording = None

            # HUD
            y = 24
            for i, (_, label, _) in enumerate(GESTURES):
                done = counts[i] >= args.target
                color = (0, 200, 0) if done else (200, 200, 200)
                bar = "#" * min(20, counts[i] * 20 // max(1, args.target))
                cv2.putText(frame, f"[{i}] {label}: {counts[i]}/{args.target} {bar}",
                            (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                y += 22

            if recording is not None:
                cv2.putText(frame, f"REC [{recording}] {GESTURES[recording][1]}",
                            (8, y + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.circle(frame, (frame.shape[1] - 30, 30), 12, (0, 0, 255), -1)
            elif not landmarks:
                cv2.putText(frame, "sin mano", (8, y + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            cv2.imshow("Captura de keypoints (0-5 grabar, espacio parar, q salir)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" "):
                recording = None
            elif key == ord("d"):
                if last_label is not None and rewrite_without_last(last_label):
                    counts[last_label] = max(0, counts[last_label] - 1)
                    print(f"  deshecha 1 muestra de [{last_label}] "
                          f"{GESTURES[last_label][1]}")
            elif ord("0") <= key <= ord("5"):
                g = key - ord("0")
                recording = None if recording == g else g  # toggle
    finally:
        f.close()
        src.release()
        cv2.destroyAllWindows()
        print(f"\nGuardado en {CSV_PATH}")
        print(f"Muestras por gesto: {counts}")
        if all(c >= 20 for c in counts):
            print("Dataset listo. Ahora entrena:  python train_keypoint.py")
        else:
            faltan = [GESTURES[i][1] for i, c in enumerate(counts) if c < 20]
            print(f"Faltan mas muestras de: {', '.join(faltan)}")


if __name__ == "__main__":
    main()
