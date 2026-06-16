from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, BookingStatus
from .serializers import BookingSerializer
from .filters import BookingFilter
from .validators import get_check_in_error


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
