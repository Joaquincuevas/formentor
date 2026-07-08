# Firmware — ESP32-CAM (Controlador de Casilleros)

## Requisitos

- Placa **ESP32-CAM** (AI-Thinker) — la que tienes.
- **Adaptador FTDI/USB-TTL a 3.3V** para programarla (la ESP32-CAM no tiene USB).
- [PlatformIO](https://platformio.org/) (extensión de VS Code) o Arduino IDE.

## Cómo flashear (con PlatformIO)

1. Copia tu configuración en `src/config.h` (WiFi, IP del broker MQTT, `CONTROLLER_ID`).
2. Conecta el FTDI: `5V→5V`, `GND→GND`, `TX→U0R`, `RX→U0T`.
3. Puentea **GPIO0 → GND** para entrar en modo flasheo y resetea la placa.
4. `pio run -t upload`
5. Quita el puente GPIO0–GND, resetea, y abre el monitor: `pio device monitor`.

## Qué funciona hoy (sin actuador)

- Conexión WiFi + MQTT y sincronización con el Sistema de Administración.
- Recepción de claves y actualizaciones de modelo por MQTT.
- Heartbeat cada 60 s.
- Prueba por el monitor serial: escribe `open 1` para simular el ingreso de una clave
  al casillero 1 (te pedirá 4 índices de gesto) y `close 1` para cerrarlo. Los eventos
  se publican al admin.

## Qué falta conectar (cuando tengas el hardware)

| Componente | Para qué | Pin sugerido (`config.h`) |
|---|---|---|
| Relé/transistor + solenoide o servo | abrir/cerrar el casillero | GPIO 12/13/15/14 |
| LED indicador | feedback visual (listo/capturando/ok/error) | GPIO 2 |
| Sensor magnético (reed) | confirmar puerta abierta/cerrada | GPIO 16 |
| Botón/selector | elegir el casillero a operar | GPIO 3 |
| Batería (power bank / 18650 + regulador) | energía autónoma | — |

> La ESP32-CAM deja **pocos GPIO libres** (la cámara usa la mayoría). Con 4 casilleros
> puede que necesites un **expansor de I/O (PCF8574)** o un **registro de
> desplazamiento (74HC595)** para los relés. Documéntalo en el diseño de EP1.

## Reconocimiento de gestos on-device

`readGestureSequence()` es hoy un **stub** por serial. La integración real usa el
modelo cuantizado que genera `gesture-model/export_tflite.py` (`gesture_model.cc`)
con **TensorFlow Lite for Microcontrollers**. Dado lo limitado de la RAM/flash de la
ESP32-CAM, valida temprano si el pipeline completo corre on-device o si conviene un
enfoque más liviano (p. ej. clasificar sobre landmarks precomputados). Este análisis
es parte de lo que pide describir el documento de diseño (EP1).
