# Contrato MQTT — formato de payloads

Todos los payloads son JSON UTF-8. `{controller_id}` es un identificador único del
controlador (ej. `ctrl-a1b2c3`). Los casilleros dentro de un controlador se numeran
`1..4` (campo `locker`).

## `casilleros/{controller_id}/sync/request`  (controlador → admin)
El controlador se anuncia al arrancar. Indica cuántos casilleros físicos tiene activos.
```json
{ "controller_id": "ctrl-a1b2c3", "active_lockers": 3, "firmware": "0.1.0" }
```

## `casilleros/{controller_id}/sync/response`  (admin → controlador)
Respuesta del admin con la configuración inicial.
```json
{
  "controller_name": "Casilleros Gimnasio",
  "model_version": 4,
  "model_url": "http://.../models/4/gesture_model.tflite",
  "lockers": [
    { "locker": 1, "name": "Locker A", "key": [2, 0, 5, 1] },
    { "locker": 2, "name": "Locker B", "key": [0, 0, 3, 4] }
  ]
}
```
`key` es la secuencia de 4 índices de gesto (0..5).

## `casilleros/{controller_id}/keys`  (admin → controlador)
Actualización de la clave de un casillero (latencia objetivo < 5 min).
```json
{ "locker": 2, "key": [1, 3, 3, 0] }
```

## `casilleros/{controller_id}/model`  (admin → controlador)
Nueva versión del modelo de gestos a descargar (latencia objetivo < 5 min).
```json
{ "model_version": 5, "model_url": "http://.../models/5/gesture_model.tflite", "sha256": "..." }
```

## `casilleros/{controller_id}/event`  (controlador → admin)
Evento de apertura o cierre.
```json
{ "locker": 1, "action": "open", "ts": "2026-07-08T14:03:00Z" }
```
`action` ∈ `{"open", "close", "denied"}`.

## `casilleros/{controller_id}/heartbeat`  (controlador → admin)
Latido periódico (cada 60 s). Si el admin no recibe latidos por > 10 min, marca el
controlador como desconectado y envía **un solo** email de aviso al administrador.
```json
{ "ts": "2026-07-08T14:03:00Z", "rssi": -61 }
```
