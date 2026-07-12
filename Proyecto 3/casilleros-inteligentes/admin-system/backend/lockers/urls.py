from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("controllers", views.ControllerViewSet, basename="controller")
router.register("lockers", views.LockerViewSet, basename="locker")
router.register("models", views.GestureModelViewSet, basename="gesturemodel")
router.register("users", views.UserViewSet, basename="user")

urlpatterns = [
    path("auth/config/", views.auth_config),
    path("auth/google/", views.google_login),
    path("me/choose-model/", views.choose_model),
    path("dashboard/user/", views.user_dashboard),
    path("dashboard/superuser/", views.superuser_dashboard),
    path("", include(router.urls)),
]
