from django.urls import path
from .views import (
    BookingCheckInView,
    BookingListCreateView,
    BookingDetailView,
)


app_name = "bookings"

urlpatterns = [
    path("", BookingListCreateView.as_view(), name="booking-list-create"),
    path("<int:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path(
        "<int:pk>/check-in/",
        BookingCheckInView.as_view(),
        name="booking-check-in",
    ),
]
