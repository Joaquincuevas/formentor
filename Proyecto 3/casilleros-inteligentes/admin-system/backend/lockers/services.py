"""Logica de negocio: reacciones a eventos MQTT y notificaciones por email.

Separado de las vistas y del cliente MQTT para poder testear y reutilizar.
"""
from datetime import datetime, timezone

from django.core.mail import send_mail
from django.utils.dateparse import parse_datetime

from .models import Controller, Locker, OpenEvent


def _parse_ts(value):
    dt = parse_datetime(value) if value else None
    return dt or datetime.now(timezone.utc)


# ---- handlers de mensajes entrantes desde los controladores ----

def handle_sync_request(controller_id, payload):
    """El controlador se anuncia. Si esta registrado, se le responde con su config."""
    from . import mqtt_client
    try:
        controller = Controller.objects.get(controller_id=controller_id)
    except Controller.DoesNotExist:
        print(f"[sync] controlador desconocido {controller_id} "
              f"(el admin debe crearlo primero)")
        return
    controller.active_lockers = payload.get("active_lockers", 0)
    controller.synced = True
    controller.last_heartbeat = datetime.now(timezone.utc)
    controller.offline_notified = False
    controller.save()
    mqtt_client.publish_sync_response(controller)
    print(f"[sync] {controller_id} sincronizado ({controller.active_lockers} casilleros)")


def handle_event(controller_id, payload):
    """Registra apertura/cierre y notifica por email al dueno si corresponde."""
    try:
        controller = Controller.objects.get(controller_id=controller_id)
        locker = controller.lockers.get(number=payload["locker"])
    except (Controller.DoesNotExist, Locker.DoesNotExist):
        return
    action = payload.get("action", "open")
    OpenEvent.objects.create(locker=locker, action=action, ts=_parse_ts(payload.get("ts")))

    if action == "open" and locker.owner_email:
        send_mail(
            subject=f"Tu casillero '{locker.name}' fue abierto",
            message=(f"Hola,\n\nSe registro una apertura de tu casillero "
                     f"'{locker.name}' el {payload.get('ts')}.\n\n"
                     f"Si no fuiste tu, contacta al administrador."),
            from_email=None,
            recipient_list=[locker.owner_email],
            fail_silently=True,
        )


def handle_heartbeat(controller_id, payload):
    try:
        controller = Controller.objects.get(controller_id=controller_id)
    except Controller.DoesNotExist:
        return
    controller.last_heartbeat = datetime.now(timezone.utc)
    controller.offline_notified = False
    controller.save(update_fields=["last_heartbeat", "offline_notified"])


# ---- notificaciones salientes ----

def send_key_email(locker, symbols):
    """Envia al dueno su nueva clave expresada con figuras + instrucciones."""
    if not locker.owner_email:
        return
    figs = " ".join(symbols[i] for i in locker.key) if symbols and locker.key else str(locker.key)
    send_mail(
        subject=f"Clave de tu casillero '{locker.name}'",
        message=(
            f"Hola,\n\nSe te asigno el casillero '{locker.name}'.\n\n"
            f"Tu clave es la siguiente secuencia de gestos:\n\n    {figs}\n\n"
            f"Para ABRIR el casillero:\n"
            f"  1. Selecciona el numero de tu casillero en el controlador.\n"
            f"  2. Presiona el boton para activar la camara (se encenderan los LEDs).\n"
            f"  3. Realiza los 4 gestos en orden frente a la camara.\n"
            f"  4. Si la clave es correcta, el casillero se abrira.\n\n"
            f"Para CERRAR: vuelve a presionar el boton de cierre.\n"
        ),
        from_email=None,
        recipient_list=[locker.owner_email],
        fail_silently=True,
    )


def notify_offline(controller):
    """Aviso (una sola vez) al administrador de un controlador desconectado."""
    if controller.offline_notified or not controller.owner.email:
        return
    send_mail(
        subject=f"Controlador '{controller.name}' desconectado",
        message=(f"El controlador '{controller.name}' ({controller.controller_id}) "
                 f"lleva mas de 10 minutos sin conexion."),
        from_email=None,
        recipient_list=[controller.owner.email],
        fail_silently=True,
    )
    controller.offline_notified = True
    controller.save(update_fields=["offline_notified"])
