# Atribución — kinivi/hand-gesture-recognition-mediapipe

Parte del pipeline de reconocimiento de gestos de este proyecto está **basado en**
y **porta código de**:

- **Repositorio:** https://github.com/kinivi/hand-gesture-recognition-mediapipe
- **Autor:** Nikita Kiselov (kinivi) — a su vez basado en el trabajo de Kazuhito Takahashi.
- **Licencia:** Apache License 2.0 (ver `LICENSE` en esta carpeta).

## Qué se reutilizó / adaptó

| Nuestro archivo | Origen en el repo de kinivi |
|---|---|
| `gesture-model/keypoint_preprocess.py` | funciones `calc_landmark_list` y `pre_process_landmark` de `app.py` |
| `gesture-model/keypoint_classifier/keypoint_classifier.py` | `model/keypoint_classifier/keypoint_classifier.py` |
| `gesture-model/collect_keypoints.py` | modo de logging (`logging_csv`, `select_mode`) de `app.py` |
| `gesture-model/train_keypoint.py` | notebook `keypoint_classification.ipynb` |

## Diferencias con el original

- Adaptado a la **API MediaPipe Tasks** (`HandLandmarker`) en lugar de la API legacy
  `mp.solutions.hands`, que no está disponible en la build de MediaPipe de este equipo.
- Ampliado de **4 gestos** (Open, Close, Pointer, OK) a **6 gestos** requeridos por el
  enunciado del proyecto.
- Integrado con el flujo de casilleros (MQTT + Sistema de Administración).

## Archivos de referencia en esta carpeta (sin modificar)

- `keypoint_classifier_pretrained.tflite` — modelo preentrenado original (4 gestos).
- `keypoint_classifier_label_original.csv` — etiquetas originales.
- `keypoint_classification_EN.ipynb` — notebook de entrenamiento original.
- `LICENSE` — Apache-2.0 del repositorio original.
