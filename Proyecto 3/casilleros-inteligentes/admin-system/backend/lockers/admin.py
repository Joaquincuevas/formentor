from django.contrib import admin

from .models import Controller, GestureModel, Locker, OpenEvent, UserProfile


@admin.register(Controller)
class ControllerAdmin(admin.ModelAdmin):
    list_display = ("name", "controller_id", "owner", "synced", "last_heartbeat")
    search_fields = ("name", "controller_id")


@admin.register(Locker)
class LockerAdmin(admin.ModelAdmin):
    list_display = ("name", "controller", "number", "owner_email")


@admin.register(GestureModel)
class GestureModelAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "active")


admin.site.register(OpenEvent)
admin.site.register(UserProfile)
