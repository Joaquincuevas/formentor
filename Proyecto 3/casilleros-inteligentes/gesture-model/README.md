# Modelo de identificación de gestos

Reconoce **6 gestos manuales** a partir de los 21 landmarks que entrega MediaPipe
Hands, y los clasifica con una red neuronal pequeña exportable a la ESP32.

## Por qué landmarks y no imágenes crudas

Clasificar sobre las 42 coordenadas normalizadas de la mano (no sobre píxeles) hace
el modelo diminuto, robusto a iluminación/fondo e invariante a posición y escala.
Es la técnica clave para que corra en un embebido. Ver `landmarks.py`.

## Instalación

```bash
cd gesture-model
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> En Apple Silicon, si `mediapipe` da problemas, usa Python 3.11 o 3.12.

## Flujo de trabajo

```bash
python collect_data.py     # 1. grabar dataset con la webcam (teclas 0..5)
python train.py            # 2. entrenar el clasificador
python live_demo.py        # 3. probar en vivo el reconocimiento de claves
python export_tflite.py    # 4. exportar a TFLite int8 + arreglo C para el firmware
```

## Salidas

- `models/gesture_model.keras` — modelo entrenado (lo sirve el sistema de admin).
- `models/gesture_model.tflite` — modelo cuantizado int8 (para la ESP32).
- `models/gesture_model.cc` — el mismo modelo como arreglo C para TFLite Micro.
- `models/label_map.txt` — índice → nombre del gesto.

## Pipeline basado en kinivi (clasificador por keypoints)

Además del reconocimiento por reglas, se integró el pipeline de
[kinivi/hand-gesture-recognition-mediapipe](https://github.com/kinivi/hand-gesture-recognition-mediapipe)
(Apache-2.0), adaptado a la API MediaPipe Tasks y a nuestros 6 gestos. Ver
[`reference/kinivi/ATTRIBUTION.md`](reference/kinivi/ATTRIBUTION.md).

Flujo para entrenar tu propio clasificador:

```bash
python collect_keypoints.py                 # 1. graba keypoints (teclas 0..5)
#   o desde la cam:  python collect_keypoints.py --source mjpeg --stream-url http://192.168.1.99/stream
python train_keypoint.py                    # 2. entrena -> keypoint_classifier/keypoint_classifier.tflite
python recognize_stream.py --classifier keypoint --source webcam   # 3. reconoce con el modelo
```

- `recognize_stream.py --classifier rules` (por defecto) → heurística de dedos, sin entrenar.
- `recognize_stream.py --classifier keypoint` → usa el modelo TFLite entrenado.

El clasificador entrenado (`keypoint_classifier.tflite`) es la base del modelo que
luego se reduce para correr en la **ESP32-S3** on-device.

## Reducción para embebido (lo que pide el enunciado)

1. **Representación por landmarks** → entrada de solo 42 números.
2. **Arquitectura mínima** (42→32→16→6).
3. **Cuantización post-entrenamiento a int8** con dataset representativo (`export_tflite.py`),
   reduciendo ~4× el tamaño y permitiendo inferencia entera sin FPU.
4. **Embebido como arreglo C** para TFLite Micro (el micro no monta un filesystem).

> El preprocesamiento de `landmarks.py` (origen en la muñeca + normalización por
> escala) debe replicarse en el firmware antes de invocar el modelo.
