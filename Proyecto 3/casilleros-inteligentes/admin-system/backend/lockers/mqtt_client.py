"""Puente MQTT del Sistema de Administracion.

Corre en un hilo de fondo dentro del proceso Django. Se suscribe a los eventos que
publican los controladores (sync/request, event, heartbeat) y expone metodos para
publicar hacia ellos (claves, modelo, respuesta de sync).

Ver el contrato de topicos en docs/mqtt.md.
"""
import json
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from django.conf import settings

_client = None
_lock = threading.Lock()


def _topic(controller_id, suffix):
    return f"casilleros/{controller_id}/{suffix}"


def _on_connect(client, userdata, flags, rc):
    print(f"[mqtt] admin conectado al broker (rc={rc})")
    # escuchamos a todos los controladores con wildcard
    client.subscribe("casilleros/+/sync/request")
    client.subscribe("casilleros/+/event")
    client.subscribe("casilleros/+/heartbeat")


def _on_message(client, userdata, msg):
    # import diferido para evitar cargar Django antes de tiempo
    from lockers import services
    parts = msg.topic.split("/")
    if len(parts) < 3:
        return
    controller_id = parts[1]
    kind = "/".join(parts[2:])
    try:
        payload = json.loads(msg.payload.decode() or "{}")
    except json.JSONDecodeError:
        return

    try:
        if kind == "sync/request":
            services.handle_sync_request(controller_id, payload)
        elif kind == "event":
            services.handle_event(controller_id, payload)
        elif kind == "heartbeat":
            services.handle_heartbeat(controller_id, payload)
    except Exception as exc:  # no dejar morir el hilo MQTT
        print(f"[mqtt] error procesando {msg.topic}: {exc}")


def start():
    """Arranca el cliente MQTT una sola vez."""
    global _client
    with _lock:
        if _client is not None:
            return
        client = mqtt.Client(client_id="admin-system")
        client.on_connect = _on_connect
        client.on_message = _on_message
        # connect_async + loop_start reintenta solo hasta que el broker este
        # disponible, sin bloquear el arranque de Django ni depender del orden.
        client.reconnect_delay_set(min_delay=1, max_delay=10)
        client.connect_async(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
        client.loop_start()
        _client = client
        print(f"[mqtt] intentando conectar a "
              f"{settings.MQTT_BROKER}:{settings.MQTT_PORT} (reintenta en segundo plano)")


def _publish(controller_id, suffix, payload):
    if _client is None:
        print("[mqtt] cliente no iniciado, no se pudo publicar")
        return
    _client.publish(_topic(controller_id, suffix), json.dumps(payload))


# ---- publicaciones hacia los controladores ----

def publish_sync_response(controller):
    """Envia al controlador su config inicial tras registrarse."""
    profile = getattr(controller.owner, "profile", None)
    model = profile.gesture_model if profile else None
    _publish(controller.controller_id, "sync/response", {
        "controller_name": controller.name,
        "model_version": model.version if model else None,
        "model_url": model.model_url if model else "",
        "lockers": [
            {"locker": lk.number, "name": lk.name, "key": lk.key}
            for lk in controller.lockers.all()
        ],
    })


def publish_key(controller_id, locker_number, key):
    _publish(controller_id, "keys", {"locker": locker_number, "key": key})


def publish_model(controller_id, model):
    _publish(controller_id, "model", {
        "model_version": model.version,
        "model_url": model.model_url,
    })


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
