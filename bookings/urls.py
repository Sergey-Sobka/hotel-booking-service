from django.urls import path
from .views import BookingListView, BookingDetailView


app_name = "bookings"

urlpatterns = [
    path("bookings/", BookingListView.as_view(), name="booking-list"),
    path(
        "bookings/<int:pk>/",
        BookingDetailView.as_view(),
        name="booking-detail"
    ),
]
