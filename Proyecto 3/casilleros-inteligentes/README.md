# Casilleros Inteligentes — Proyecto 3 (Web + Embebidos)

Sistema para gestionar remotamente controladores de apertura/cierre de casilleros,
donde la clave de cada casillero es una secuencia de **4 gestos manuales** (de un
conjunto de al menos 6 gestos posibles), reconocidos con visión por computador.

## Componentes

| Carpeta | Qué es | ¿Necesita hardware? |
|---|---|---|
| [`gesture-model/`](gesture-model/) | Entrenamiento y exportación del modelo de gestos (MediaPipe + TensorFlow → TFLite) | No, solo webcam |
| [`admin-system/backend/`](admin-system/backend/) | Sistema de Administración: API REST (Django + DRF), base de datos, MQTT, emails | No |
| [`admin-system/frontend/`](admin-system/frontend/) | Dashboard web (React + Vite + Axios) | No |
| [`simulator/`](simulator/) | Controlador de casilleros **simulado** por MQTT, para probar el sistema sin la ESP32 | No |
| [`firmware/`](firmware/) | Firmware real de la ESP32-CAM (PlatformIO / Arduino) | Sí (ESP32-CAM + actuador) |

## Orden recomendado para trabajar en vacaciones (solo con la ESP32-CAM)

1. **Modelo de gestos** (`gesture-model/`) — se hace 100% en tu laptop con la webcam.
2. **Sistema de Administración** (`admin-system/`) — backend + frontend, sin hardware.
3. **Simulador** (`simulator/`) — reemplaza a la ESP32 para probar la sincronización MQTT
   de punta a punta.
4. **Firmware** (`firmware/`) — flashear la ESP32-CAM: cámara + WiFi + MQTT ya funcionan
   sin actuador. El motor/solenoide y sensores se agregan cuando los tengas.

## Broker MQTT

Todos los componentes hablan por MQTT. Para desarrollo puedes usar:

- **Mosquitto local**: `brew install mosquitto && brew services start mosquitto`
  (broker en `localhost:1883`).
- O el broker público de prueba de HiveMQ: `broker.hivemq.com:1883` (sin credenciales,
  **no usar para datos reales**).

### Convención de tópicos MQTT

```
casilleros/{controller_id}/sync/request     # controlador -> admin: anuncia n° de casilleros activos
casilleros/{controller_id}/sync/response    # admin -> controlador: config inicial (nombres, modelo)
casilleros/{controller_id}/keys             # admin -> controlador: claves actualizadas por casillero
casilleros/{controller_id}/model            # admin -> controlador: nueva versión del modelo
casilleros/{controller_id}/event            # controlador -> admin: apertura/cierre de casillero
casilleros/{controller_id}/heartbeat        # controlador -> admin: latido cada 60s (detectar desconexión)
```

Ver [`docs/mqtt.md`](docs/mqtt.md) para el formato de cada payload.
