"""Admin registrations for rooms."""

from django.contrib import admin
from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("number", "room_type", "price_per_night", "capacity")
    list_filter = ("room_type", "capacity")
    search_fields = ("number",)
    ordering = ("number",)
