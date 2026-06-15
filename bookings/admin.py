from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "room", "status", "check_in_date", "check_out_date", "price_per_night")
    list_filter = ("status",)
    search_fields = ("user__email", "room__id")
