import os
import sys

from django.apps import AppConfig


class LockersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lockers"

    def ready(self):
        # No arrancar MQTT en comandos de gestion (migrate, makemigrations, etc.)
        mgmt = {"migrate", "makemigrations", "collectstatic", "shell",
                "createsuperuser", "test", "seed_demo"}
        if any(cmd in sys.argv for cmd in mgmt):
            return
        # Con el autoreloader de runserver hay 2 procesos; solo el hijo (RUN_MAIN)
        # debe abrir la conexion MQTT para no duplicar el cliente.
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return
        try:
            from . import mqtt_client
            mqtt_client.start()
        except Exception as exc:
            print(f"[lockers] MQTT no iniciado: {exc}")
