from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking, BookingStatus
from rooms.models import Room
from rooms.validators import MAX_CALENDAR_RANGE_DAYS

User = get_user_model()


class TestRoomViewSet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="testpassword123"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", password="adminpassword123", is_staff=True
        )

        self.room1 = Room.objects.create(
            number="101",
            room_type="SINGLE",
            price_per_night=Decimal("50.00"),
            capacity=1,
        )
        self.room2 = Room.objects.create(
            number="102",
            room_type="DOUBLE",
            price_per_night=Decimal("100.00"),
            capacity=2,
        )
        self.room3 = Room.objects.create(
            number="103",
            room_type="SUITE",
            price_per_night=Decimal("200.00"),
            capacity=4,
        )

        self.list_url = reverse("rooms:room-list")
        self.detail_url = reverse("rooms:room-detail", kwargs={"pk": self.room1.pk})
        self.calendar_url = reverse("rooms:room-calendar", kwargs={"pk": self.room1.pk})

    def test_list_rooms_public_access(self):
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

    def test_create_room_admin_only(self):
        self.client.force_authenticate(user=self.admin)

        payload = {
            "number": "201",
            "room_type": "DOUBLE",
            "price_per_night": "150.00",
            "capacity": 2,
        }
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Room.objects.filter(number="201").exists())

    def test_create_room_forbidden_for_regular_user(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "number": "202",
            "room_type": "SINGLE",
            "price_per_night": "80.00",
            "capacity": 1,
        }
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Room.objects.filter(number="202").exists())

    def test_filter_rooms_by_type(self):
        res = self.client.get(self.list_url, {"type": "DOUBLE"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["number"], self.room2.number)

    def test_filter_rooms_by_capacity(self):
        res = self.client.get(self.list_url, {"capacity": 4})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["number"], self.room3.number)

    def test_filter_rooms_by_invalid_capacity(self):
        res = self.client.get(self.list_url, {"capacity": "invalid"})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", res.data)

    def test_calendar_marks_booked_and_active_dates_unavailable(self):
        Booking.objects.create(
            room=self.room1,
            user=self.user,
            check_in_date=date(2026, 6, 16),
            check_out_date=date(2026, 6, 18),
            status=BookingStatus.BOOKED,
            price_per_night=Decimal("50.00"),
        )
        Booking.objects.create(
            room=self.room1,
            user=self.admin,
            check_in_date=date(2026, 6, 19),
            check_out_date=date(2026, 6, 20),
            status=BookingStatus.ACTIVE,
            price_per_night=Decimal("50.00"),
        )

        res = self.client.get(
            self.calendar_url,
            {"from": "2026-06-15", "to": "2026-06-20"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            [
                {"date": "2026-06-15", "available": True},
                {"date": "2026-06-16", "available": False},
                {"date": "2026-06-17", "available": False},
                {"date": "2026-06-18", "available": True},
                {"date": "2026-06-19", "available": False},
                {"date": "2026-06-20", "available": True},
            ],
        )

    def test_calendar_ignores_non_blocking_booking_statuses(self):
        for booking_status in (
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
            BookingStatus.NO_SHOW,
        ):
            Booking.objects.create(
                room=self.room1,
                user=self.user,
                check_in_date=date(2026, 6, 16),
                check_out_date=date(2026, 6, 18),
                status=booking_status,
                price_per_night=Decimal("50.00"),
            )

        res = self.client.get(
            self.calendar_url,
            {"from": "2026-06-16", "to": "2026-06-17"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(all(day["available"] for day in res.data))

    def test_calendar_requires_valid_date_range(self):
        missing_dates_res = self.client.get(self.calendar_url)
        reversed_dates_res = self.client.get(
            self.calendar_url,
            {"from": "2026-06-20", "to": "2026-06-19"},
        )

        self.assertEqual(missing_dates_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(reversed_dates_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calendar_rejects_range_longer_than_maximum(self):
        start_date = date(2026, 1, 1)
        end_date = start_date + timedelta(days=MAX_CALENDAR_RANGE_DAYS)

        res = self.client.get(
            self.calendar_url,
            {"from": start_date.isoformat(), "to": end_date.isoformat()},
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res.data)
