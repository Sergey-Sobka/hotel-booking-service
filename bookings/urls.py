from django.urls import path
from .views import BookingCheckInView, BookingListView, BookingDetailView, BookingCreateView


app_name = "bookings"

urlpatterns = [
    path("", BookingListView.as_view(), name="booking-list"),
    path("<int:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path(
        "<int:pk>/check-in/",
        BookingCheckInView.as_view(),
        name="booking-check-in",
    ),
    path("create/", BookingCreateView.as_view(), name="booking-create"),
]
