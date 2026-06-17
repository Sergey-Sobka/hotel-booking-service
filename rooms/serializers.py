from rest_framework import serializers

from .models import Room
from .validators import (
    validate_calendar_date_range,
    validate_price_per_night,
    validate_room_capacity,
)


class RoomSerializer(serializers.ModelSerializer):
    price_per_night = serializers.DecimalField(
        max_digits=10, decimal_places=2, validators=[validate_price_per_night]
    )
    capacity = serializers.IntegerField(validators=[validate_room_capacity])
    room_type_display = serializers.CharField(
        source="get_room_type_display", read_only=True
    )

    class Meta:
        model = Room
        fields = (
            "id",
            "number",
            "room_type",
            "room_type_display",
            "price_per_night",
            "capacity",
        )


class CalendarQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs):
        validate_calendar_date_range(attrs["start_date"], attrs["end_date"])
        return attrs


class CalendarResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    available = serializers.BooleanField()
