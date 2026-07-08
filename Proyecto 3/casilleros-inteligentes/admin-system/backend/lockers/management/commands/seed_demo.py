"""Crea datos de demostracion: superusuario, un usuario, un modelo de gestos,
un controlador con 3 casilleros y algunos eventos de apertura.

Uso:
    python manage.py seed_demo
"""
import random
from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from lockers.models import (Controller, GestureModel, Locker, OpenEvent,
                            UserProfile)

SYMBOLS = ["\U0001F590", "✊", "✌", "\U0001F44D", "☝", "\U0001F44C"]


class Command(BaseCommand):
    help = "Crea datos de demostracion"

    def handle(self, *args, **options):
        su, _ = User.objects.get_or_create(
            username="admin", defaults={"email": "admin@uandes.cl",
                                        "is_staff": True, "is_superuser": True})
        su.set_password("admin"); su.save()
        UserProfile.objects.get_or_create(user=su)

        user, _ = User.objects.get_or_create(
            username="demo@uandes.cl", defaults={"email": "demo@uandes.cl"})
        profile, _ = UserProfile.objects.get_or_create(user=user)

        model, _ = GestureModel.objects.get_or_create(
            name="Modelo base", defaults={"version": 1, "symbols": SYMBOLS})
        profile.gesture_model = model
        profile.save()

        ctrl, _ = Controller.objects.get_or_create(
            controller_id="ctrl-demo1",
            defaults={"name": "Casilleros Gimnasio", "owner": user,
                      "active_lockers": 3, "synced": True,
                      "last_heartbeat": datetime.now(timezone.utc)})

        for i in range(1, 4):
            lk, _ = Locker.objects.get_or_create(
                controller=ctrl, number=i,
                defaults={"name": f"Locker {i}", "owner_email": f"dueno{i}@mail.com",
                          "key": [random.randrange(6) for _ in range(4)]})
            # eventos de los ultimos 7 dias
            for d in range(7):
                for _ in range(random.randint(0, 4)):
                    ts = datetime.now(timezone.utc) - timedelta(
                        days=d, hours=random.randint(0, 23))
                    OpenEvent.objects.create(locker=lk, action="open", ts=ts)

        self.stdout.write(self.style.SUCCESS(
            "Datos demo creados. Superusuario: admin/admin | Usuario: demo@uandes.cl"))
