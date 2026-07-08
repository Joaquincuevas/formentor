# Sistema de Administración — Backend (Django + DRF)

API REST del sistema, base de datos, puente MQTT con los controladores y envío de
emails.

## Instalación

```bash
cd admin-system/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # datos de demo (opcional)
python manage.py runserver 8000
```

> Requiere Python 3.8–3.12 (Django 4.2 LTS). Con Python 3.10+ puedes subir a Django 5.

## Broker MQTT

El backend intenta conectarse al broker definido por `MQTT_BROKER`/`MQTT_PORT`
(por defecto `localhost:1883`). Si no hay broker, el resto de la API igual funciona;
solo no habrá comunicación con los controladores. Levanta uno con:

```bash
brew install mosquitto && brew services start mosquitto
```

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/google/` | Login/registro con Google (stub: recibe `email`) → token |
| GET/POST | `/api/controllers/` | Listar / crear controladores |
| GET/POST | `/api/lockers/` | Listar / crear casilleros |
| POST | `/api/lockers/{id}/assign/` | Asignar clave y dueño (email + MQTT) |
| GET/POST/DELETE | `/api/models/` | CRUD de modelos de gestos (superusuario) |
| GET/POST/DELETE | `/api/users/` | CRUD de usuarios (superusuario) |
| POST | `/api/me/choose-model/` | Elegir modelo → regenera claves y actualiza controladores |
| GET | `/api/dashboard/user/` | Métricas del usuario |
| GET | `/api/dashboard/superuser/` | Métricas globales |

Autenticación: header `Authorization: Token <token>`.

## Detección de controladores desconectados

El aviso por email (una sola vez, tras >10 min sin heartbeat) lo hace el comando:

```bash
python manage.py check_offline
```

Programarlo con cron cada minuto:

```
* * * * * cd /ruta/backend && .venv/bin/python manage.py check_offline
```

## Cómo se cumplen los requisitos del enunciado

- **Autorregistro con Google** → `google_login` (stub listo para conectar Google Identity).
- **Asignar clave + dueño, email con figuras e instrucciones** → `LockerViewSet.assign` + `services.send_key_email`.
- **Aviso de apertura al dueño** → `services.handle_event`.
- **CRUD de modelos (superusuario)** → `GestureModelViewSet`.
- **Un usuario usa un solo modelo; al cambiarlo se regeneran claves y se actualizan
  todos sus controladores** → `choose_model`.
- **Latencia < 5 min en claves/modelo** → publicación MQTT inmediata.
- **Dashboards usuario/superusuario con aperturas de 7 días + métricas extra** →
  `user_dashboard`, `superuser_dashboard`.
- **Aviso de desconexión > 10 min (una vez)** → `check_offline` + flag `offline_notified`.
