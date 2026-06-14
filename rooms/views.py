"""Room API views will be implemented in their feature tasks."""

from rest_framework import serializers, viewsets

from .models import Room
from .permissions import IsAdminOrReadOnly
from .serializers import RoomSerializer


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()

        room_type = self.request.query_params.get("type")
        capacity = self.request.query_params.get("capacity")

        if room_type:
            queryset = queryset.filter(room_type=room_type)
        if capacity:
            try:
                capacity = int(capacity)
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"capacity": "Capacity must be an integer."}
                ) from exc
            queryset = queryset.filter(capacity=capacity)
        return queryset
