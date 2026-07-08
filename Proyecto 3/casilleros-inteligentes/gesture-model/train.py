"""Entrena un clasificador de gestos a partir de `data/landmarks.csv`.

El modelo es una red neuronal densa pequena (MLP): 42 entradas -> 32 -> 16 ->
NUM_GESTURES. Es deliberadamente chico para poder cuantizarlo y correrlo en un
dispositivo embebido (ver export_tflite.py).

Uso:
    python train.py

Salidas:
    models/gesture_model.keras   (modelo entrenado)
    models/label_map.txt         (indice -> nombre de gesto)
"""
import csv
import os

import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf

from gestures import GESTURES, NAMES, NUM_GESTURES
from landmarks import FEATURE_DIM

BASE = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE, "data", "landmarks.csv")
MODEL_DIR = os.path.join(BASE, "models")


def load_dataset():
    X, y = [], []
    with open(CSV_PATH, newline="") as f:
        for row in csv.reader(f):
            if not row:
                continue
            y.append(int(row[0]))
            X.append([float(v) for v in row[1:]])
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)
    if X.shape[1] != FEATURE_DIM:
        raise ValueError(f"Se esperaban {FEATURE_DIM} features, hay {X.shape[1]}")
    return X, y


def build_model():
    return tf.keras.Sequential([
        tf.keras.layers.Input(shape=(FEATURE_DIM,)),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(NUM_GESTURES, activation="softmax"),
    ])


def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit("No hay dataset. Corre primero: python collect_data.py")
    os.makedirs(MODEL_DIR, exist_ok=True)

    X, y = load_dataset()
    print(f"Dataset: {len(X)} muestras, {NUM_GESTURES} clases")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = build_model()
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    model.fit(X_tr, y_tr, validation_data=(X_te, y_te),
              epochs=60, batch_size=32, verbose=2)

    loss, acc = model.evaluate(X_te, y_te, verbose=0)
    print(f"\nAccuracy en test: {acc:.3f}")

    model.save(os.path.join(MODEL_DIR, "gesture_model.keras"))
    with open(os.path.join(MODEL_DIR, "label_map.txt"), "w") as f:
        for i, name in enumerate(NAMES):
            f.write(f"{i}\t{name}\n")
    print(f"Modelo guardado en {MODEL_DIR}/gesture_model.keras")


if __name__ == "__main__":
    main()
