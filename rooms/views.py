"""Room API views will be implemented in their feature tasks."""

from datetime import date, timedelta

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Room
from .permissions import IsAdminOrReadOnly
from .serializers import (
    RoomSerializer,
    CalendarQuerySerializer,
    CalendarResponseSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List rooms",
        description="Returns rooms, optionally filtered by room type and capacity.",
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by room type.",
                enum=Room.RoomType.values,
            ),
            OpenApiParameter(
                name="capacity",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by exact room capacity.",
            ),
        ],
        responses={
            200: RoomSerializer(many=True),
            400: OpenApiResponse(description="Invalid capacity value."),
        },
    )
)
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

    @extend_schema(
        summary="Get room availability calendar",
        description=(
            "Returns each day in the requested date range marked as available "
            "or unavailable. BOOKED and ACTIVE bookings make a day unavailable. "
            "The maximum inclusive range is 366 days."
        ),
        parameters=[
            OpenApiParameter(
                name="from",
                type=date,
                location=OpenApiParameter.QUERY,
                required=True,
                description="First calendar date in YYYY-MM-DD format.",
            ),
            OpenApiParameter(
                name="to",
                type=date,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Last calendar date in YYYY-MM-DD format.",
            ),
        ],
        responses={
            200: CalendarResponseSerializer(many=True),
            400: OpenApiResponse(
                description="Missing, invalid, reversed, or excessive date range."
            ),
            404: OpenApiResponse(description="Room not found."),
        },
    )
    @action(detail=True, methods=["get"])
    def calendar(self, request, pk=None):
        room = self.get_object()

        query_data = {
            "start_date": request.query_params.get("from"),
            "end_date": request.query_params.get("to"),
        }
        query_serializer = CalendarQuerySerializer(data=query_data)
        query_serializer.is_valid(raise_exception=True)

        start_date = query_serializer.validated_data["start_date"]
        end_date = query_serializer.validated_data["end_date"]

        overlapping_bookings = room.bookings.filter(
            status__in=["BOOKED", "ACTIVE"],
            check_in_date__lt=end_date + timedelta(days=1),
            check_out_date__gt=start_date,
        )

        calendar_data = []
        current_date = start_date

        while current_date <= end_date:
            is_available = True

            for booking in overlapping_bookings:
                if booking.check_in_date <= current_date < booking.check_out_date:
                    is_available = False
                    break

            calendar_data.append({"date": current_date, "available": is_available})
            current_date += timedelta(days=1)

        response_serializer = CalendarResponseSerializer(calendar_data, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
