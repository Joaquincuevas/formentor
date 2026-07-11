"""Entrena el clasificador de keypoints y lo exporta a TFLite.

Port del notebook `keypoint_classification.ipynb` de kinivi
(https://github.com/kinivi/hand-gesture-recognition-mediapipe, Apache-2.0),
adaptado a nuestros 6 gestos y a script.

Entrada:  keypoint_classifier/keypoint.csv   (label, 42 features)  <- collect_keypoints.py
Salidas:  keypoint_classifier/keypoint_classifier.tflite        (float, lo usa el Mac)
          keypoint_classifier/keypoint_classifier_int8.tflite   (cuantizado, base ESP32-S3)

Arquitectura (igual que kinivi): 42 -> Dropout -> 20 -> Dropout -> 10 -> 6.
"""
import csv
import os
from collections import Counter

import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf

from gestures import NUM_GESTURES, LABELS

BASE = os.path.join(os.path.dirname(__file__), "keypoint_classifier")
CSV_PATH = os.path.join(BASE, "keypoint.csv")
TFLITE_PATH = os.path.join(BASE, "keypoint_classifier.tflite")
TFLITE_INT8_PATH = os.path.join(BASE, "keypoint_classifier_int8.tflite")
NUM_FEATURES = 42


def per_class_report(model, X_te, y_te):
    """Precision/recall aproximada por gesto para saber cual esta debil."""
    pred = np.argmax(model.predict(X_te, verbose=0), axis=1)
    print("\nDesempeno por gesto (en test):")
    for c in range(NUM_GESTURES):
        mask = y_te == c
        n = int(mask.sum())
        if n == 0:
            print(f"  [{c}] {LABELS[c]:<22} sin muestras en test")
            continue
        acc = float((pred[mask] == c).mean())
        flag = "  <-- revisar / grabar mas" if acc < 0.8 else ""
        print(f"  [{c}] {LABELS[c]:<22} acc={acc:.2f} (n={n}){flag}")


def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit("No hay dataset. Corre primero: python collect_keypoints.py")

    X = np.loadtxt(CSV_PATH, delimiter=",", dtype="float32",
                   usecols=list(range(1, NUM_FEATURES + 1)))
    y = np.loadtxt(CSV_PATH, delimiter=",", dtype="int32", usecols=(0,))
    if X.ndim == 1:  # una sola fila
        X = X.reshape(1, -1)
        y = y.reshape(1)

    counts = Counter(y.tolist())
    print(f"Dataset: {len(X)} muestras")
    for c in range(NUM_GESTURES):
        print(f"  [{c}] {LABELS[c]:<22} {counts.get(c, 0)} muestras")
    if min(counts.get(c, 0) for c in range(NUM_GESTURES)) < 10:
        print("\nAviso: hay gestos con <10 muestras. El modelo va a ser flojo ahi.")

    # stratify solo si cada clase tiene >=2 muestras
    strat = y if all(v >= 2 for v in counts.values()) else None
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=strat)

    model = tf.keras.models.Sequential([
        tf.keras.layers.Input((NUM_FEATURES,)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(20, activation="relu"),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(10, activation="relu"),
        tf.keras.layers.Dense(NUM_GESTURES, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    model.fit(X_tr, y_tr, epochs=1000, batch_size=128,
              validation_data=(X_te, y_te), verbose=2,
              callbacks=[tf.keras.callbacks.EarlyStopping(patience=20,
                                                          restore_best_weights=True)])

    loss, acc = model.evaluate(X_te, y_te, verbose=0)
    print(f"\nAccuracy global en test: {acc:.3f}")
    per_class_report(model, X_te, y_te)

    # --- export float (lo usa recognize_stream.py en el Mac) ---
    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite = conv.convert()
    with open(TFLITE_PATH, "wb") as fp:
        fp.write(tflite)
    print(f"\nTFLite float: {TFLITE_PATH} ({len(tflite)/1024:.1f} KB)")

    # --- export int8 cuantizado (base para el modelo on-device en la ESP32-S3) ---
    def rep_data():
        for i in range(min(200, len(X_tr))):
            yield [X_tr[i:i + 1]]
    conv8 = tf.lite.TFLiteConverter.from_keras_model(model)
    conv8.optimizations = [tf.lite.Optimize.DEFAULT]
    conv8.representative_dataset = rep_data
    conv8.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv8.inference_input_type = tf.int8
    conv8.inference_output_type = tf.int8
    try:
        tflite8 = conv8.convert()
        with open(TFLITE_INT8_PATH, "wb") as fp:
            fp.write(tflite8)
        print(f"TFLite int8:  {TFLITE_INT8_PATH} ({len(tflite8)/1024:.1f} KB)")
    except Exception as exc:
        print(f"(no se pudo exportar int8: {exc})")

    print("\nListo. Prueba en vivo:")
    print("  python recognize_stream.py --classifier keypoint --source webcam --key '0,1,2,3'")


if __name__ == "__main__":
    main()
