"""Entrena el clasificador de keypoints y lo exporta a TFLite.

Port del notebook `keypoint_classification.ipynb` de kinivi
(https://github.com/kinivi/hand-gesture-recognition-mediapipe, Apache-2.0),
adaptado a nuestros 6 gestos y a script.

Entrada:  keypoint_classifier/keypoint.csv   (label, 42 features)  <- collect_keypoints.py
Salidas:  keypoint_classifier/keypoint_classifier.tflite
          (el .tflite lo usa recognize_stream.py y sirve de base para el modelo
           reducido que ira a la ESP32-S3)

Arquitectura (igual que kinivi): 42 -> Dropout -> 20 -> Dropout -> 10 -> 6.
"""
import csv
import os

import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf

from gestures import NUM_GESTURES

BASE = os.path.join(os.path.dirname(__file__), "keypoint_classifier")
CSV_PATH = os.path.join(BASE, "keypoint.csv")
TFLITE_PATH = os.path.join(BASE, "keypoint_classifier.tflite")
NUM_FEATURES = 42


def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit("No hay dataset. Corre primero: python collect_keypoints.py")

    X = np.loadtxt(CSV_PATH, delimiter=",", dtype="float32",
                   usecols=list(range(1, NUM_FEATURES + 1)))
    y = np.loadtxt(CSV_PATH, delimiter=",", dtype="int32", usecols=(0,))
    print(f"Dataset: {len(X)} muestras, {NUM_GESTURES} clases")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

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
    print(f"\nAccuracy en test: {acc:.3f}")

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite = converter.convert()
    with open(TFLITE_PATH, "wb") as f:
        f.write(tflite)
    print(f"Modelo TFLite guardado en {TFLITE_PATH} ({len(tflite)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
