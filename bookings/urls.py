from django.urls import path
from .views import (
    BookingCancelView,
    BookingCheckInView,
    BookingCheckOutView,
    BookingListCreateView,
    BookingDetailView,
    BookingNoShowView,
    BookingOverstayView,
)

app_name = "bookings"

urlpatterns = [
    path("", BookingListCreateView.as_view(), name="booking-list"),
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
        "<int:pk>/no-show/",
        BookingNoShowView.as_view(),
        name="booking-no-show",
    ),
    path(
        "<int:pk>/overstay/",
        BookingOverstayView.as_view(),
        name="booking-overstay",
    ),
    path(
        "<int:pk>/cancel/",
        BookingCancelView.as_view(),
        name="booking-cancel",
    ),
]
