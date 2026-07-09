"""Reconocimiento de gestos en tiempo real sobre el video de la ESP32-CAM.

ENFOQUE A (IA en el computador): la ESP32-CAM transmite MJPEG por WiFi; aqui, en el
Mac, MediaPipe detecta la mano y clasificamos los 6 gestos. Cuando la secuencia de 4
gestos coincide con la clave del casillero, se publica la apertura por MQTT (el
Sistema de Administracion la registra y envia el email al dueno).

Dos clasificadores disponibles (--classifier):
  - rules    : heuristica de dedos extendidos, sin entrenar (por defecto).
  - keypoint : modelo TFLite entrenado (pipeline portado de kinivi). Requiere haber
               corrido collect_keypoints.py + train_keypoint.py.

Uso tipico (con la cam transmitiendo en http://192.168.1.99/stream):
    python recognize_stream.py --stream-url http://192.168.1.99/stream \
        --controller ctrl-demo1 --locker 1

Fallback con la webcam del Mac (si el stream de la cam falla):
    python recognize_stream.py --source webcam --controller ctrl-demo1 --locker 1

Controles en la ventana:  r = reiniciar secuencia · q = salir
"""
import argparse
import sys
import time
from collections import deque
from datetime import datetime, timezone

import cv2
import requests
import paho.mqtt.client as mqtt

from gestures import GESTURES, KEY_LENGTH, LABELS, SYMBOLS
from hand_tracker import HandTracker
from video_source import open_source

STABLE_FRAMES = 12      # frames seguidos con el mismo gesto para confirmarlo
COOLDOWN_S = 1.2        # pausa tras confirmar un gesto
KEYPOINT_MIN_CONF = 0.6 # confianza minima del clasificador entrenado


# --------------------------------------------------------------------------
# Clasificadores de gesto: por REGLAS (sin entrenar) o por MODELO (kinivi/TFLite)
# --------------------------------------------------------------------------
def make_classifier(kind):
    """Devuelve una funcion classify(landmarks, handed, frame) -> indice o None.

    kind='rules'    -> heuristica de dedos extendidos (no requiere entrenamiento).
    kind='keypoint' -> clasificador TFLite entrenado con collect_keypoints/train_keypoint
                       (pipeline portado de kinivi/hand-gesture-recognition-mediapipe).
    """
    if kind == "keypoint":
        # import diferido: solo cargar TensorFlow si se usa el modelo
        from keypoint_classifier.keypoint_classifier import KeyPointClassifier
        from keypoint_preprocess import calc_landmark_list, pre_process_landmark
        kc = KeyPointClassifier()

        def classify_kp(landmarks, handed, frame):
            feats = pre_process_landmark(calc_landmark_list(frame, landmarks))
            idx, conf = kc.predict(feats)
            return idx if conf >= KEYPOINT_MIN_CONF else None
        return classify_kp

    return lambda landmarks, handed, frame: classify(landmarks, handed)


# --------------------------------------------------------------------------
# Clasificacion de gestos por reglas (dedos extendidos)
# --------------------------------------------------------------------------
def _dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def fingers_up(lm, handedness):
    """Devuelve [pulgar, indice, medio, anular, menique] como booleanos."""
    up = []
    # pulgar: comparar x de la punta (4) e IP (3) segun la mano
    if handedness == "Right":
        up.append(lm[4].x < lm[3].x)
    else:
        up.append(lm[4].x > lm[3].x)
    # resto: punta por encima (y menor) de la articulacion PIP
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        up.append(lm[tip].y < lm[pip].y)
    return up


def classify(lm, handedness):
    """Devuelve el indice de gesto (0..5) o None."""
    thumb, index, middle, ring, pinky = fingers_up(lm, handedness)
    count = sum([thumb, index, middle, ring, pinky])

    hand_size = _dist(lm[0], lm[9]) + 1e-6
    pinch = _dist(lm[4], lm[8]) / hand_size   # pulgar-indice juntos = OK

    if pinch < 0.4 and middle and ring and pinky:
        return 5  # ok
    if count == 5:
        return 0  # palma
    if count == 0:
        return 1  # puno
    if index and middle and not ring and not pinky and not thumb:
        return 2  # victoria
    if index and not middle and not ring and not pinky and not thumb:
        return 4  # indice
    if thumb and not index and not middle and not ring and not pinky:
        return 3  # pulgar arriba
    return None


# --------------------------------------------------------------------------
# Integracion con el backend y MQTT
# --------------------------------------------------------------------------
def fetch_key(api, email, controller_id, locker_number):
    """Obtiene la clave del casillero desde el Sistema de Administracion."""
    try:
        tok = requests.post(f"{api}/auth/google/", json={"email": email},
                            timeout=5).json()["token"]
        headers = {"Authorization": f"Token {tok}"}
        lockers = requests.get(f"{api}/lockers/", headers=headers, timeout=5).json()
        for lk in lockers:
            ctrl = requests.get(f"{api}/controllers/{lk['controller']}/",
                                headers=headers, timeout=5).json()
            if ctrl["controller_id"] == controller_id and lk["number"] == locker_number:
                return lk["key"]
    except Exception as exc:
        print(f"[api] no se pudo obtener la clave ({exc}); usa --key")
    return None


def publish_event(broker, controller_id, locker_number, action):
    try:
        c = mqtt.Client()
        c.connect(broker, 1883, 5)
        payload = ('{"locker":%d,"action":"%s","ts":"%s"}'
                   % (locker_number, action,
                      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        c.publish(f"casilleros/{controller_id}/event", payload)
        c.disconnect()
    except Exception as exc:
        print(f"[mqtt] no se pudo publicar ({exc})")


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mjpeg", "webcam"], default="mjpeg")
    ap.add_argument("--stream-url", default="http://192.168.1.99/stream")
    ap.add_argument("--controller", default="ctrl-demo1")
    ap.add_argument("--locker", type=int, default=1)
    ap.add_argument("--key", default=None, help="clave fija, ej '2,0,5,1' (salta la API)")
    ap.add_argument("--api", default="http://localhost:8090/api")
    ap.add_argument("--email", default="demo@uandes.cl")
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--classifier", choices=["rules", "keypoint"], default="rules",
                    help="'rules' (heuristica) o 'keypoint' (modelo TFLite entrenado)")
    ap.add_argument("--no-window", action="store_true", help="modo headless (sin ventana)")
    args = ap.parse_args()

    if args.key:
        target = [int(x) for x in args.key.split(",")]
    else:
        target = fetch_key(args.api, args.email, args.controller, args.locker)
    if not target or len(target) != KEY_LENGTH:
        print("No hay clave valida. Usa --key '2,0,5,1'."); sys.exit(1)
    print(f"Clave objetivo casillero {args.locker}: {target} "
          f"-> {' '.join(SYMBOLS[i] for i in target)}")

    kind, src = open_source(args.source, args.stream_url)
    tracker = HandTracker(min_conf=0.5)
    classify_gesture = make_classifier(args.classifier)
    print(f"Clasificador: {args.classifier}")

    recent = deque(maxlen=STABLE_FRAMES)
    entered, last_conf, cooldown = [], None, 0.0
    result_msg, result_until = "", 0.0

    while True:
        ok, frame = src.read()
        if not ok:
            print("stream terminado / sin frame"); break
        if kind == "webcam":
            frame = cv2.flip(frame, 1)

        landmarks, handed = tracker.process(frame)
        pred = None
        if landmarks:
            tracker.draw(frame, landmarks)
            pred = classify_gesture(landmarks, handed, frame)
        recent.append(pred if pred is not None else -1)

        now = time.time()
        if (len(recent) == STABLE_FRAMES and len(set(recent)) == 1
                and recent[0] != -1 and now >= cooldown):
            g = recent[0]
            if g != last_conf:
                entered.append(g); last_conf = g; cooldown = now + COOLDOWN_S
                print(f"gesto confirmado: {LABELS[g]}  secuencia={entered}")
                if len(entered) == KEY_LENGTH:
                    if entered == target:
                        result_msg = "ABIERTO"
                        publish_event(args.broker, args.controller, args.locker, "open")
                        print(">>> CLAVE CORRECTA: casillero ABIERTO <<<")
                    else:
                        result_msg = "DENEGADO"
                        publish_event(args.broker, args.controller, args.locker, "denied")
                        print(">>> clave incorrecta <<<")
                    result_until = now + 3.0
                    entered, last_conf = [], None

        if now > result_until:
            result_msg = ""

        # --- overlay ---
        txt = LABELS[pred] if pred is not None else "sin gesto"
        cv2.putText(frame, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        seq = " ".join(SYMBOLS[g] for g in entered) or "(vacia)"
        cv2.putText(frame, f"Clave: {seq}", (10, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
        if result_msg:
            color = (0, 200, 0) if result_msg == "ABIERTO" else (0, 0, 255)
            cv2.putText(frame, result_msg, (10, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3)

        if not args.no_window:
            cv2.imshow("Casilleros - reconocimiento de gestos (q=salir, r=reset)", frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                break
            if k == ord("r"):
                entered, last_conf = [], None

    src.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
