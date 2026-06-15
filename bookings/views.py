from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Booking
from .serializers import BookingSerializer
from .filters import BookingFilter


class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BookingFilter

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related(
            "room"
        )


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
