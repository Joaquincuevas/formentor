"""Revisa que controladores llevan > 10 min sin heartbeat y avisa (una vez).

Pensado para correr periodicamente, ej. con cron cada minuto:
    * * * * * cd .../backend && python manage.py check_offline

(Tambien podria implementarse como tarea Celery.)
"""
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core.management.base import BaseCommand

from lockers.models import Controller
from lockers.services import notify_offline


class Command(BaseCommand):
    help = "Avisa por email de controladores desconectados > 10 min"

    def handle(self, *args, **options):
        limit = timedelta(minutes=settings.OFFLINE_THRESHOLD_MINUTES)
        now = datetime.now(timezone.utc)
        n = 0
        for c in Controller.objects.filter(synced=True, offline_notified=False):
            if c.last_heartbeat and (now - c.last_heartbeat) > limit:
                notify_offline(c)
                n += 1
        self.stdout.write(self.style.SUCCESS(f"Avisos enviados: {n}"))
