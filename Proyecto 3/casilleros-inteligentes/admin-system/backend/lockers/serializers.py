from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Controller, GestureModel, Locker, OpenEvent, UserProfile


class GestureModelSerializer(serializers.ModelSerializer):
    model_url = serializers.ReadOnlyField()

    class Meta:
        model = GestureModel
        fields = ["id", "name", "version", "active", "symbols", "model_file",
                  "model_url", "created_at"]


class LockerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locker
        fields = ["id", "controller", "number", "name", "owner_email", "key"]


class ControllerSerializer(serializers.ModelSerializer):
    lockers = LockerSerializer(many=True, read_only=True)
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Controller
        fields = ["id", "controller_id", "name", "active_lockers", "synced",
                  "last_heartbeat", "is_online", "lockers", "created_at"]
        read_only_fields = ["synced", "last_heartbeat", "active_lockers"]

    def get_is_online(self, obj):
        from datetime import datetime, timedelta, timezone
        from django.conf import settings
        if not obj.last_heartbeat:
            return False
        limit = timedelta(minutes=settings.OFFLINE_THRESHOLD_MINUTES)
        return (datetime.now(timezone.utc) - obj.last_heartbeat) < limit


class OpenEventSerializer(serializers.ModelSerializer):
    locker_name = serializers.CharField(source="locker.name", read_only=True)

    class Meta:
        model = OpenEvent
        fields = ["id", "locker", "locker_name", "action", "ts", "received_at"]


class UserSerializer(serializers.ModelSerializer):
    gesture_model = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_superuser", "gesture_model"]

    def get_gesture_model(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.gesture_model_id if profile else None
