from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "status",
            "type",
            "amount",
            "session_url",
            "session_id",
            "created_at",
        ]

        read_only_fields = fields
