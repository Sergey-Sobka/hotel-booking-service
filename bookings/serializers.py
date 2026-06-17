from rest_framework import serializers
from datetime import date

from .models import Booking


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "room", "check_in_date", "check_out_date"]

    def validate_check_in_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                "Check-in date cannot be in the past."
            )
        return value

    def validate(self, attrs):
        check_in = attrs.get("check_in_date")
        check_out = attrs.get("check_out_date")

        if check_out <= check_in:
            raise serializers.ValidationError(
                "Check-out date must be after check-in date."
            )

        return attrs

    def create(self, validated_data):
        room = validated_data["room"]
        validated_data["user"] = self.context["request"].user
        validated_data["price_per_night"] = room.price_per_night
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ("user",)


class BookingCheckOutSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    actual_check_out_date = serializers.DateField()
    overstay_days = serializers.IntegerField()
    overstay_payment_id = serializers.IntegerField(
        allow_null=True,
        required=False,
    )
    overstay_payment_url = serializers.URLField(
        allow_null=True,
        required=False,
    )
