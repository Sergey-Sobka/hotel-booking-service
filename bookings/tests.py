from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from rooms.models import Room
from .models import Booking, BookingStatus

User = get_user_model()


class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass",
        )
        self.room = Room.objects.create(
            number="101",
            room_type=Room.RoomType.SINGLE,
            price_per_night="100.00",
            capacity=2,
        )
        self.booking_data = dict(
            user=self.user,
            room=self.room,
            check_in_date=date(2025, 8, 1),
            check_out_date=date(2025, 8, 5),
            price_per_night="120.00",
        )

    def test_default_status_is_booked(self):
        booking = Booking(**self.booking_data)
        self.assertEqual(booking.status, BookingStatus.BOOKED)

    def test_str_representation(self):
        booking = Booking.objects.create(**self.booking_data)
        self.assertIn("2025-08-01", str(booking))

    def test_actual_check_out_nullable(self):
        booking = Booking(**self.booking_data)
        self.assertIsNone(booking.actual_check_out_date)

    def test_status_choices(self):
        valid_statuses = {s.value for s in BookingStatus}
        self.assertIn("NO_SHOW", valid_statuses)
        self.assertIn("CANCELLED", valid_statuses)
