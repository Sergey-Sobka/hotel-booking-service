from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
)
from rest_framework import status
from rest_framework import generics
from django.utils import timezone as django_timezone
from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, generics, serializers
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError

from datetime import datetime, timezone, timedelta

from .models import Booking, BookingStatus
from .serializers import BookingSerializer, BookingCreateSerializer
from .filters import BookingFilter
from .validators import get_check_in_error
from payments.services import create_booking_payment_session
from payments.models import Payment


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
        today = django_timezone.localdate()
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


@extend_schema_view(
    post=extend_schema(
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
)
class BookingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filterset_class = BookingFilter

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all().select_related("room")
        return Booking.objects.filter(user=self.request.user).select_related(
            "room"
        )

    @transaction.atomic
    def perform_create(self, serializer):
        room = serializer.validated_data["room"]
        check_in = serializer.validated_data["check_in_date"]
        check_out = serializer.validated_data["check_out_date"]

        overlapping = (
            Booking.objects.select_for_update()
            .filter(
                room=room,
                status__in=[BookingStatus.BOOKED, BookingStatus.ACTIVE],
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
            )
            .exists()
        )

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


@extend_schema(
    summary="Perform administrative actions on a booking",
    description=(
        "Handles booking lifecycle actions including cancellation, no-show, and overstay. "
        "Each action triggers a corresponding payment session if applicable."
    ),
    parameters=[
        OpenApiParameter(
            name="pk",
            description="Booking ID",
            required=True,
            type=int,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name="action",
            description="The action to perform: 'cancel', 'no-show', or 'overstay'",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        ),
    ],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "extra_days": {
                    "type": "integer",
                    "description": "Required only for 'overstay' action",
                }
            },
        }
    },
    responses={
        200: OpenApiExample(
            "Success response",
            value={"detail": "Action completed successfully."},
        ),
        400: OpenApiExample(
            "Error response", value={"error": "Invalid action"}
        ),
        403: OpenApiExample(
            "Permission denied", value={"error": "Permission denied"}
        ),
    },
)
class BookingAdminActionView(APIView):
    permission_classes = [IsAuthenticated]

    def _is_less_than_24h(self, booking):
        check_in_dt = timezone.make_aware(
            timezone.datetime.combine(
                booking.check_in_date, timezone.datetime.min.time()
            )
        )
        return (check_in_dt - timezone.now()) < timedelta(hours=24)

    @transaction.atomic
    def post(self, request, pk, action):
        booking = get_object_or_404(Booking, pk=pk)

        if not (request.user.is_staff or booking.user == request.user):
            return Response({"error": "Permission denied"}, status=403)

        if action == "cancel":
            if self._is_less_than_24h(booking):
                create_booking_payment_session(
                    booking=booking,
                    payment_type=Payment.TypeChoices.CANCELLATION_FEE,
                    request=request,
                )
            booking.status = BookingStatus.CANCELLED
            booking.save()
            return Response({"detail": "Booking cancelled successfully."})

        elif action == "no-show" and request.user.is_staff:
            create_booking_payment_session(
                booking, Payment.TypeChoices.NO_SHOW_FEE, request
            )
            booking.status = BookingStatus.NO_SHOW
            booking.save()
            return Response({"detail": "No-show session created"})

        elif action == "overstay" and request.user.is_staff:
            extra_days = int(request.data.get("extra_days", 1))
            create_booking_payment_session(
                booking,
                Payment.TypeChoices.OVERSTAY_FEE,
                request,
                extra_days=extra_days,
            )
            return Response({"detail": "Overstay session created"})

        return Response(
            {"error": "Invalid action or permission denied"}, status=400
        )


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Cancel a booking",
        description=(
            "Cancels a BOOKED reservation. "
            "Only the booking owner or staff can cancel. "
            "Cancellations within 24 hours of check-in are marked "
            "as late and will incur a cancellation fee (handled in HBS-23)."
        ),
        responses={
            200: OpenApiResponse(description="Booking cancelled successfully."),
            400: OpenApiResponse(description="Booking cannot be cancelled."),
            403: OpenApiResponse(description="Not allowed to cancel this booking."),
        },
    )
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if not request.user.is_staff and booking.user != request.user:
            raise PermissionDenied(
                "You do not have permission to cancel this booking."
            )

        if booking.status != BookingStatus.BOOKED:
            raise ValidationError(
                f"Cannot cancel a booking with status '{booking.status}'."
            )

        check_in_datetime = datetime.combine(
            booking.check_in_date, datetime.min.time()
        ).replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        is_late = (check_in_datetime - now) < timedelta(hours=24)

        booking.status = BookingStatus.CANCELLED
        booking.is_late_cancellation = is_late
        booking.save(update_fields=["status", "is_late_cancellation"])

        return Response(
            {
                "detail": "Booking cancelled.",
                "is_late_cancellation": is_late,
            },
            status=status.HTTP_200_OK,
        )
