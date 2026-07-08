"""Modelo de datos del Sistema de Administracion.

Entidades:
  - GestureModel : un modelo de reconocimiento de gestos (lo gestiona el superusuario).
  - Controller   : un controlador fisico (ESP32) que administra hasta 4 casilleros.
  - Locker       : un casillero individual dentro de un controlador.
  - OpenEvent    : registro historico de aperturas/cierres (para dashboards).

Los administradores son usuarios de Django (django.contrib.auth.User). El
superusuario es un User con is_staff/is_superuser. El perfil extiende al usuario
para guardar el modelo de gestos elegido.
"""
from django.contrib.auth.models import User
from django.db import models


class GestureModel(models.Model):
    """Modelo de reconocimiento de gestos. El superusuario hace CRUD de estos."""
    name = models.CharField(max_length=120)
    version = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    # archivo .tflite del modelo entrenado (entrenamiento ocurre fuera del sistema)
    model_file = models.FileField(upload_to="models/", null=True, blank=True)
    # symbols: lista de figuras que representan cada gesto, en orden de indice
    # ej: ["\U0001F590", "✊", "✌", ...]
    symbols = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} v{self.version}"

    @property
    def model_url(self):
        return self.model_file.url if self.model_file else ""


class UserProfile(models.Model):
    """Perfil del administrador: guarda el modelo de gestos que usa.

    El enunciado exige que un usuario use SIEMPRE el mismo modelo para todos sus
    controladores. Por eso el modelo se fija a nivel de usuario, no de controlador.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    gesture_model = models.ForeignKey(
        GestureModel, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Controller(models.Model):
    """Controlador fisico de casilleros (una ESP32)."""
    controller_id = models.CharField(max_length=64, unique=True)  # id MQTT
    name = models.CharField(max_length=120)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="controllers")
    active_lockers = models.PositiveIntegerField(default=0)
    synced = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    offline_notified = models.BooleanField(default=False)  # aviso ya enviado
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.controller_id})"


class Locker(models.Model):
    """Un casillero dentro de un controlador (numero 1..4)."""
    controller = models.ForeignKey(
        Controller, on_delete=models.CASCADE, related_name="lockers"
    )
    number = models.PositiveSmallIntegerField()  # 1..4
    name = models.CharField(max_length=120)
    owner_email = models.EmailField(blank=True)
    # clave = lista de 4 indices de gesto, ej [2, 0, 5, 1]
    key = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("controller", "number")
        ordering = ["controller", "number"]

    def __str__(self):
        return f"{self.name} (ctrl {self.controller.controller_id} #{self.number})"


class OpenEvent(models.Model):
    """Registro de un evento de apertura/cierre reportado por un controlador."""
    ACTIONS = [("open", "Apertura"), ("close", "Cierre"), ("denied", "Rechazado")]
    locker = models.ForeignKey(Locker, on_delete=models.CASCADE, related_name="events")
    action = models.CharField(max_length=10, choices=ACTIONS)
    ts = models.DateTimeField()  # timestamp reportado por el controlador
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ts"]

    def __str__(self):
        return f"{self.locker} {self.action} @ {self.ts}"
