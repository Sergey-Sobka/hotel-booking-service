from django.urls import path
from .views import BookingListView, BookingDetailView

app_name = "bookings"

urlpatterns = [
    path("", BookingListView.as_view(), name="booking-list"),
    path(
        "<int:pk>/",
        BookingDetailView.as_view(),
        name="booking-detail"
    ),
]
