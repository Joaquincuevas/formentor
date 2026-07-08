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

## Reducción para embebido (lo que pide el enunciado)

1. **Representación por landmarks** → entrada de solo 42 números.
2. **Arquitectura mínima** (42→32→16→6).
3. **Cuantización post-entrenamiento a int8** con dataset representativo (`export_tflite.py`),
   reduciendo ~4× el tamaño y permitiendo inferencia entera sin FPU.
4. **Embebido como arreglo C** para TFLite Micro (el micro no monta un filesystem).

> El preprocesamiento de `landmarks.py` (origen en la muñeca + normalización por
> escala) debe replicarse en el firmware antes de invocar el modelo.
