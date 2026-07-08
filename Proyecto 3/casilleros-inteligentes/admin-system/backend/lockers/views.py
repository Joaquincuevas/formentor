"""Vistas / API REST del Sistema de Administracion."""
import random
from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from . import mqtt_client, services
from .models import Controller, GestureModel, Locker, OpenEvent, UserProfile
from .serializers import (ControllerSerializer, GestureModelSerializer,
                          LockerSerializer, OpenEventSerializer, UserSerializer)


# ---------------------------------------------------------------------------
# Autenticacion (stub de "login con Google")
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    """Autorregistro/login con cuenta de Google.

    STUB para desarrollo: en produccion aqui se verifica el id_token de Google
    (google-auth) y se extrae el email. Por ahora aceptamos el email directo y
    creamos el usuario si no existe. Devuelve un token de API.
    """
    email = request.data.get("email")
    if not email:
        return Response({"detail": "email requerido"}, status=400)
    user, created = User.objects.get_or_create(
        username=email, defaults={"email": email}
    )
    if created:
        UserProfile.objects.get_or_create(user=user)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token": token.key,
        "user": UserSerializer(user).data,
        "created": created,
    })


# ---------------------------------------------------------------------------
# Modelos de gestos (CRUD del superusuario)
# ---------------------------------------------------------------------------
class GestureModelViewSet(viewsets.ModelViewSet):
    queryset = GestureModel.objects.all()
    serializer_class = GestureModelSerializer

    def get_permissions(self):
        # solo el superusuario administra modelos; el resto solo lee
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminUser()]


# ---------------------------------------------------------------------------
# Controladores
# ---------------------------------------------------------------------------
class ControllerViewSet(viewsets.ModelViewSet):
    serializer_class = ControllerSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Controller.objects.prefetch_related("lockers")
        return qs if user.is_superuser else qs.filter(owner=user)

    def perform_create(self, serializer):
        controller = serializer.save(owner=self.request.user)
        # intenta enviar la config inicial si el controlador ya esta escuchando
        mqtt_client.publish_sync_response(controller)


# ---------------------------------------------------------------------------
# Casilleros
# ---------------------------------------------------------------------------
class LockerViewSet(viewsets.ModelViewSet):
    serializer_class = LockerSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Locker.objects.select_related("controller")
        return qs if user.is_superuser else qs.filter(controller__owner=user)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Asigna clave y/o dueno a un casillero.

        body: { "key": [2,0,5,1], "owner_email": "x@y.com" }
        - Actualiza el casillero.
        - Publica la clave al controlador por MQTT (latencia < 5 min).
        - Envia email al dueno con la clave en figuras + instrucciones.
        """
        locker = self.get_object()
        key = request.data.get("key")
        owner_email = request.data.get("owner_email")
        if key is not None:
            locker.key = key
        if owner_email is not None:
            locker.owner_email = owner_email
        locker.save()

        mqtt_client.publish_key(locker.controller.controller_id, locker.number, locker.key)

        profile = getattr(locker.controller.owner, "profile", None)
        symbols = profile.gesture_model.symbols if (profile and profile.gesture_model) else []
        services.send_key_email(locker, symbols)

        return Response(LockerSerializer(locker).data)


# ---------------------------------------------------------------------------
# Eleccion de modelo del usuario (regenera claves + actualiza controladores)
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def choose_model(request):
    """El usuario elige el modelo de gestos que usara en TODOS sus controladores.

    body: { "gesture_model_id": 3 }
    Al cambiar de modelo:
      - Se guarda en el perfil.
      - Se regeneran las claves de todos los casilleros activos con los simbolos
        del nuevo modelo.
      - Se publica el nuevo modelo y las nuevas claves a todos los controladores.
      - Se envia email a cada dueno con la nueva clave.
    """
    model_id = request.data.get("gesture_model_id")
    model = GestureModel.objects.filter(id=model_id, active=True).first()
    if not model:
        return Response({"detail": "modelo no encontrado o inactivo"}, status=404)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.gesture_model = model
    profile.save()

    n_symbols = len(model.symbols) if model.symbols else 6
    for controller in request.user.controllers.all():
        mqtt_client.publish_model(controller.controller_id, model)
        for locker in controller.lockers.all():
            locker.key = [random.randrange(n_symbols) for _ in range(4)]
            locker.save()
            mqtt_client.publish_key(controller.controller_id, locker.number, locker.key)
            services.send_key_email(locker, model.symbols)

    return Response({"detail": "modelo actualizado y claves regeneradas",
                     "gesture_model": model.id})


# ---------------------------------------------------------------------------
# Usuarios (CRUD del superusuario)
# ---------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------
def _openings_last_7_days(events_qs):
    """Devuelve [{date, count}] de aperturas por dia en los ultimos 7 dias."""
    today = datetime.now(timezone.utc).date()
    buckets = {today - timedelta(days=i): 0 for i in range(6, -1, -1)}
    start = today - timedelta(days=6)
    for ev in events_qs.filter(action="open", ts__date__gte=start):
        d = ev.ts.date()
        if d in buckets:
            buckets[d] += 1
    return [{"date": d.isoformat(), "count": c} for d, c in sorted(buckets.items())]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """Dashboard del usuario: uso de SUS casilleros."""
    controllers = request.user.controllers.all()
    lockers = Locker.objects.filter(controller__in=controllers)
    events = OpenEvent.objects.filter(locker__in=lockers)

    # 3 metricas adicionales elegidas por el grupo:
    #  - casillero mas usado (ultimos 7 dias)
    #  - promedio de intentos rechazados por apertura
    #  - controladores en linea vs total
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    most_used = (events.filter(action="open", ts__gte=week_ago)
                 .values("locker__name")
                 .annotate(n=Count("id")).order_by("-n").first())
    opens = events.filter(action="open").count()
    denied = events.filter(action="denied").count()
    online = sum(1 for c in controllers
                 if c.last_heartbeat and
                 (datetime.now(timezone.utc) - c.last_heartbeat) < timedelta(minutes=10))

    return Response({
        "openings_last_7_days": _openings_last_7_days(events),
        "most_used_locker": most_used["locker__name"] if most_used else None,
        "denied_ratio": round(denied / opens, 2) if opens else 0,
        "controllers_online": online,
        "controllers_total": controllers.count(),
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def superuser_dashboard(request):
    """Dashboard del superusuario: informacion general del sistema."""
    events = OpenEvent.objects.all()
    controllers = Controller.objects.all()
    now = datetime.now(timezone.utc)
    online = sum(1 for c in controllers
                 if c.last_heartbeat and (now - c.last_heartbeat) < timedelta(minutes=10))

    # 4 metricas adicionales:
    week_ago = now - timedelta(days=7)
    active_models = GestureModel.objects.filter(active=True).count()
    total_opens = events.filter(action="open").count()
    denied = events.filter(action="denied").count()
    busiest = (events.filter(action="open", ts__gte=week_ago)
               .values("locker__controller__name")
               .annotate(n=Count("id")).order_by("-n").first())

    return Response({
        "users_count": User.objects.count(),
        "controllers_count": controllers.count(),
        "lockers_count": Locker.objects.count(),
        "openings_last_7_days": _openings_last_7_days(events),
        "controllers_online": online,
        "controllers_offline": controllers.count() - online,
        "active_models": active_models,
        "total_denied_attempts": denied,
        "busiest_controller": busiest["locker__controller__name"] if busiest else None,
    })
