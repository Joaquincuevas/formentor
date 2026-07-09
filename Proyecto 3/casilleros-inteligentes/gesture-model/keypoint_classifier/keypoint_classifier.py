#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Clasificador de gestos por keypoints — portado de kinivi (Apache-2.0).

Fuente: https://github.com/kinivi/hand-gesture-recognition-mediapipe
        model/keypoint_classifier/keypoint_classifier.py

Envuelve un modelo TFLite que recibe 42 features (landmarks normalizados) y
devuelve el indice del gesto. Se agrego `predict()` para obtener tambien la
confianza (softmax).
"""
import os

import numpy as np

# Para SOLO inferencia basta el runtime ligero de TFLite; si no esta, se usa el de
# TensorFlow completo (necesario de todos modos para entrenar con train_keypoint.py).
# El nombre del interprete cambio entre versiones de TF, asi que probamos varias vias.
try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        import tensorflow as tf
        Interpreter = tf.lite.Interpreter

_HERE = os.path.dirname(__file__)
DEFAULT_MODEL = os.path.join(_HERE, "keypoint_classifier.tflite")


class KeyPointClassifier(object):
    def __init__(self, model_path=DEFAULT_MODEL, num_threads=1):
        self.interpreter = Interpreter(model_path=model_path,
                                       num_threads=num_threads)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(self, landmark_list):
        idx, _ = self.predict(landmark_list)
        return idx

    def predict(self, landmark_list):
        """Devuelve (indice, confianza)."""
        in_idx = self.input_details[0]["index"]
        self.interpreter.set_tensor(
            in_idx, np.array([landmark_list], dtype=np.float32))
        self.interpreter.invoke()
        out_idx = self.output_details[0]["index"]
        result = np.squeeze(self.interpreter.get_tensor(out_idx))
        i = int(np.argmax(result))
        return i, float(result[i])
