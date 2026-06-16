from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from rest_framework import serializers

from .models import Booking, BookingStatus
from .serializers import BookingSerializer, BookingCreateSerializer
from .filters import BookingFilter
from .validators import get_check_in_error
from payments.services import create_booking_payment_session
from payments.models import Payment


class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BookingFilter

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all().select_related("room")
        return Booking.objects.filter(
            user=self.request.user
        ).select_related("room")


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)


class BookingCheckInView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Check in booking",
        description=(
            "Validates that a booking can be checked in and sets it to ACTIVE."
        ),
        request=None,
        responses={
            200: BookingSerializer,
            400: OpenApiResponse(description="Booking is not eligible."),
        },
    )
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        today = timezone.localdate()
        check_in_error = get_check_in_error(booking, today)

        if check_in_error:
            return Response(
                {"detail": check_in_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = BookingStatus.ACTIVE
        booking.save(update_fields=["status"])

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Create a booking",
    description=(
        "Creates a booking for the authenticated user"
        "Automatically attaches the user and copies the room price"
        "Validates dates and prevents overlapping reservations"
        "Returns a Stripe payment session URL"
    ),
    request=BookingCreateSerializer,
    responses={
        201: OpenApiResponse(
            description="Booking created, payment session initiated"
        ),
        400: OpenApiResponse(
            description="Validation errors or room unavailable"
        ),
    },
)
class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        room = serializer.validated_data["room"]
        check_in = serializer.validated_data["check_in_date"]
        check_out = serializer.validated_data["check_out_date"]

        overlapping = Booking.objects.select_for_update().filter(
            room=room,
            status__in=[BookingStatus.BOOKED, BookingStatus.ACTIVE],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
        ).exists()

        if overlapping:
            raise serializers.ValidationError(
                "This room is already booked for the selected dates."
            )

        booking = serializer.save()

        create_booking_payment_session(
            booking=booking,
            payment_type=Payment.TypeChoices.BOOKING,
            request=self.request,
        )
