from django.urls import path
from .views import (
    BookingCancelView,
    BookingCheckInView,
    BookingCheckOutView,
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
    path(
        "<int:pk>/check-out/",
        BookingCheckOutView.as_view(),
        name="booking-check-out",
    ),
    path(
        "<int:pk>/cancel/",
        BookingCancelView.as_view(),
        name="booking-cancel",
    ),
]
