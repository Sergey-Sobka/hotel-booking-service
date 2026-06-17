from django.shortcuts import get_object_or_404
from django.utils import timezone as django_timezone
from django.db import transaction
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, generics, serializers
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError

from datetime import datetime, timezone, timedelta

from .models import Booking, BookingStatus
from .serializers import (
    BookingCheckOutSerializer,
    BookingCreateSerializer,
    BookingSerializer,
)
from .filters import BookingFilter
from .validators import get_check_in_error, get_check_out_error
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


class BookingCheckOutView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Check out booking",
        description=(
            "Completes an active booking and exposes overstay data for payment."
        ),
        request=None,
        responses={
            200: BookingCheckOutSerializer,
            400: OpenApiResponse(description="Booking is not eligible."),
        },
    )
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        check_out_error = get_check_out_error(booking)

        if check_out_error:
            return Response(
                {"detail": check_out_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actual_check_out_date = django_timezone.localdate()
        overstay_days = max(
            (actual_check_out_date - booking.check_out_date).days,
            0,
        )
        booking.status = BookingStatus.COMPLETED
        booking.actual_check_out_date = actual_check_out_date
        booking.save(update_fields=["status", "actual_check_out_date"])

        overstay_payment = None
        if overstay_days > 0:
            overstay_payment = create_booking_payment_session(
                booking=booking,
                payment_type=Payment.TypeChoices.OVERSTAY_FEE,
                request=request,
                extra_days=overstay_days,
            )

        response_serializer = BookingCheckOutSerializer(
            {
                "id": booking.id,
                "status": booking.status,
                "actual_check_out_date": booking.actual_check_out_date,
                "overstay_days": overstay_days,
                "overstay_payment_id": (
                    overstay_payment.id if overstay_payment else None
                ),
                "overstay_payment_url": (
                    overstay_payment.session_url if overstay_payment else None
                ),
            }
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


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
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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
                {
                    "detail": "This room is already booked for the selected dates."
                }
            )
        booking = serializer.save()
        payment = create_booking_payment_session(
            booking=booking,
            payment_type=Payment.TypeChoices.BOOKING,
            request=self.request,
        )

        response_data = serializer.data
        response_data["payment_url"] = payment.session_url

        return Response(response_data, status=status.HTTP_201_CREATED)


class BookingNoShowView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(summary="Mark booking as no-show and trigger fee")
    @transaction.atomic
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if booking.status != BookingStatus.BOOKED:
            raise ValidationError(
                f"Cannot mark a booking with status '{booking.status}' as no-show."
            )

        payment = create_booking_payment_session(
            booking, Payment.TypeChoices.NO_SHOW_FEE, request
        )
        booking.status = BookingStatus.NO_SHOW
        booking.save(update_fields=["status"])
        return Response(
            {
                "detail": "No-show status applied.",
                "payment_url": payment.session_url,
            },
            status=status.HTTP_200_OK,
        )


class BookingOverstayView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(summary="Trigger overstay fee")
    @transaction.atomic
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        if booking.status != BookingStatus.ACTIVE:
            raise ValidationError(
                "Only ACTIVE bookings can have overstay charges."
            )
        try:
            extra_days = int(request.data.get("extra_days", 1))
            if extra_days < 1:
                raise ValueError
        except (ValueError, TypeError):
            raise ValidationError(
                {
                    "extra_days": "Must be an integer greater than or equal to 1."
                }
            )
        payment = create_booking_payment_session(
            booking,
            Payment.TypeChoices.OVERSTAY_FEE,
            request,
            extra_days=extra_days,
        )
        return Response(
            {
                "detail": f"Overstay fee for {extra_days} days initiated.",
                "payment_url": payment.session_url,
            },
            status=status.HTTP_200_OK,
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
            200: OpenApiResponse(
                description="Booking cancelled successfully."
            ),
            400: OpenApiResponse(description="Booking cannot be cancelled."),
            403: OpenApiResponse(
                description="Not allowed to cancel this booking."
            ),
        },
    )
    @transaction.atomic
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
        payment_url = None
        if is_late:
            payment = create_booking_payment_session(
                booking=booking,
                payment_type=Payment.TypeChoices.CANCELLATION_FEE,
                request=request,
            )
            payment_url = payment.session_url
        booking.status = BookingStatus.CANCELLED
        booking.is_late_cancellation = is_late
        booking.save(update_fields=["status", "is_late_cancellation"])
        response_data = {
            "detail": "Booking cancelled.",
            "is_late_cancellation": is_late,
        }
        if payment_url:
            response_data["payment_url"] = payment_url

        return Response(response_data, status=status.HTTP_200_OK)
