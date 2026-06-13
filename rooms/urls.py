from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RoomViewSet

app_name = "rooms"

router = DefaultRouter()
router.register(r"", RoomViewSet, basename="room")

urlpatterns = [
    path("", include(router.urls)),
]
