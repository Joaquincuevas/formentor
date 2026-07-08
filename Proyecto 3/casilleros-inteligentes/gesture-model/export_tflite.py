"""Convierte el modelo Keras a TensorFlow Lite con cuantizacion entera completa,
para poder ejecutarlo en la ESP32 con TensorFlow Lite for Microcontrollers.

Tecnicas de reduccion aplicadas (esto es lo que pide describir el enunciado):
  - Cuantizacion post-entrenamiento a int8: pesos y activaciones pasan de float32
    a int8, reduciendo ~4x el tamano y permitiendo inferencia entera (mas rapida
    y sin FPU).
  - Se usa un dataset representativo para calibrar los rangos de cuantizacion.
  - El resultado se exporta ademas como arreglo C (gesture_model.cc) para
    compilarlo dentro del firmware (TFLite Micro no lee archivos, se embebe).

Uso:
    python export_tflite.py
"""
import csv
import os

import numpy as np
import tensorflow as tf

from landmarks import FEATURE_DIM

BASE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE, "models")
KERAS_PATH = os.path.join(MODEL_DIR, "gesture_model.keras")
CSV_PATH = os.path.join(BASE, "data", "landmarks.csv")
TFLITE_PATH = os.path.join(MODEL_DIR, "gesture_model.tflite")
CC_PATH = os.path.join(MODEL_DIR, "gesture_model.cc")


def representative_dataset():
    """Muestras reales para calibrar la cuantizacion."""
    with open(CSV_PATH, newline="") as f:
        rows = [r for r in csv.reader(f) if r]
    np.random.shuffle(rows)
    for row in rows[:300]:
        x = np.array([[float(v) for v in row[1:]]], dtype=np.float32)
        yield [x]


def to_c_array(data: bytes, var: str) -> str:
    lines = [f"const unsigned char {var}[] = {{"]
    for i in range(0, len(data), 12):
        chunk = ", ".join(f"0x{b:02x}" for b in data[i:i + 12])
        lines.append(f"  {chunk},")
    lines.append("};")
    lines.append(f"const unsigned int {var}_len = {len(data)};")
    return "\n".join(lines)


def main():
    if not os.path.exists(KERAS_PATH):
        raise SystemExit("No hay modelo. Corre primero: python train.py")

    model = tf.keras.models.load_model(KERAS_PATH)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model = converter.convert()
    with open(TFLITE_PATH, "wb") as f:
        f.write(tflite_model)

    with open(CC_PATH, "w") as f:
        f.write("// Generado por export_tflite.py — modelo de gestos cuantizado int8\n")
        f.write(f"// Entrada: {FEATURE_DIM} floats normalizados (ver landmarks.py)\n\n")
        f.write(to_c_array(tflite_model, "gesture_model_tflite"))
        f.write("\n")

    kb = len(tflite_model) / 1024
    print(f"TFLite:  {TFLITE_PATH}  ({kb:.1f} KB)")
    print(f"C array: {CC_PATH}  (copiar al firmware para TFLite Micro)")


if __name__ == "__main__":
    main()
