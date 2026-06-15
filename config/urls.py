"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/rooms/", include("rooms.urls", namespace="rooms")),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/bookings/", include("bookings.urls", namespace="bookings")),
]
