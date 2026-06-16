from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from unittest.mock import patch, MagicMock
from decimal import Decimal

from rooms.models import Room
from .models import Booking, BookingStatus
from .tasks import check_and_mark_no_shows

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
            price_per_night=Decimal("120.00"),
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

    def test_price_cannot_be_negative(self):
        data = {k: v for k, v in self.booking_data.items() if k != "price_per_night"}
        booking = Booking(price_per_night="-10.00", **data)
        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_price_zero_is_valid(self):
        data = {k: v for k, v in self.booking_data.items() if k != "price_per_night"}
        booking = Booking(price_per_night="0.00", **data)
        booking.full_clean()

    def test_check_out_must_be_after_check_in(self):
        booking = Booking(**{**self.booking_data, "check_out_date": date(2025, 7, 31)})
        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_valid_dates_pass(self):
        booking = Booking(**self.booking_data)
        booking.full_clean()


class BookingListCreateViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@a.com", password="pass")
        self.other_user = User.objects.create_user(email="b@b.com", password="pass")
        self.room = Room.objects.create(
            number="101", room_type=Room.RoomType.SINGLE,
            price_per_night="100.00", capacity=2,
        )
        self.booking = Booking.objects.create(
            user=self.user, room=self.room,
            check_in_date=date(2025, 8, 1),
            check_out_date=date(2025, 8, 5),
            price_per_night=Decimal("100.00"),
        )
        Booking.objects.create(
            user=self.other_user, room=self.room,
            check_in_date=date(2025, 9, 1),
            check_out_date=date(2025, 9, 5),
            price_per_night="100.00",
        )
        self.url = reverse("bookings:booking-list-create")

        self.payload = {
            "room": self.room.id,
            "check_in_date": date.today().isoformat(),
            "check_out_date": (date.today() + timedelta(days=3)).isoformat(),
        }

    @patch("bookings.views.create_booking_payment_session")
    def test_create_booking_success(self, mock_payment):
        mock_payment.return_value = MagicMock()
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.url, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(id=res.data["id"])
        self.assertEqual(booking.user, self.user)
        self.assertEqual(
            booking.price_per_night,
            Decimal(str(self.room.price_per_night))
        )

    @patch("bookings.views.create_booking_payment_session")
    def test_check_in_in_past_rejected(self, mock_payment):
        self.client.force_authenticate(user=self.user)
        payload = {
            **self.payload,
            "check_in_date": (date.today() - timedelta(days=1)).isoformat(),
        }
        res = self.client.post(self.url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("bookings.views.create_booking_payment_session")
    def test_check_out_before_check_in_rejected(self, mock_payment):
        self.client.force_authenticate(user=self.user)
        payload = {
            **self.payload,
            "check_out_date": date.today().isoformat(),
        }
        res = self.client.post(self.url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("bookings.views.create_booking_payment_session")
    def test_overlapping_booking_rejected(self, mock_payment):
        mock_payment.return_value = MagicMock()
        Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=3),
            price_per_night="100.00",
            status=BookingStatus.BOOKED,
        )
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.url, self.payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_rejected(self):
        res = self.client.post(self.url, self.payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own_bookings(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], self.booking.id)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url, {"status": "BOOKED"})
        self.assertEqual(len(res.data), 1)

    def test_filter_by_room(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url, {"room": self.room.id})
        self.assertEqual(len(res.data), 1)

    def test_staff_sees_all_bookings(self):
        staff = User.objects.create_user(
            email="staff@a.com", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=staff)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)


class BookingDetailViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@a.com", password="pass")
        self.other_user = User.objects.create_user(email="b@b.com", password="pass")
        self.room = Room.objects.create(
            number="101", room_type=Room.RoomType.SINGLE,
            price_per_night="100.00", capacity=2,
        )
        self.booking = Booking.objects.create(
            user=self.user, room=self.room,
            check_in_date=date(2025, 8, 1),
            check_out_date=date(2025, 8, 5),
            price_per_night="100.00",
        )
        self.url = reverse("bookings:booking-detail", kwargs={"pk": self.booking.pk})

    def test_owner_can_retrieve(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_other_user_gets_404(self):
        self.client.force_authenticate(user=self.other_user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_retrieve_any_booking(self):
        staff = User.objects.create_user(
            email="staff@a.com", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=staff)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class BookingCheckInViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="guest@a.com", password="pass")
        self.staff = User.objects.create_user(
            email="staff@a.com", password="pass", is_staff=True
        )
        self.room = Room.objects.create(
            number="201",
            room_type=Room.RoomType.SINGLE,
            price_per_night="100.00",
            capacity=2,
        )
        today = timezone.localdate()
        self.booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in_date=today,
            check_out_date=today + timedelta(days=2),
            price_per_night="100.00",
        )
        self.url = reverse("bookings:booking-check-in", kwargs={"pk": self.booking.pk})

    def test_staff_can_check_in_booked_booking(self):
        self.client.force_authenticate(user=self.staff)

        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.ACTIVE)
        self.assertEqual(res.data["status"], BookingStatus.ACTIVE)

    def test_non_staff_cannot_check_in_booking(self):
        self.client.force_authenticate(user=self.user)

        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_check_in_booking(self):
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_check_in_not_booked_booking(self):
        self.booking.status = BookingStatus.CANCELLED
        self.booking.save(update_fields=["status"])
        self.client.force_authenticate(user=self.staff)

        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_check_in_before_check_in_date(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        self.booking.check_in_date = tomorrow
        self.booking.check_out_date = tomorrow + timedelta(days=2)
        self.booking.save(update_fields=["check_in_date", "check_out_date"])
        self.client.force_authenticate(user=self.staff)

        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_check_in_after_check_out_date(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        self.booking.check_in_date = yesterday - timedelta(days=2)
        self.booking.check_out_date = yesterday
        self.booking.save(update_fields=["check_in_date", "check_out_date"])
        self.client.force_authenticate(user=self.staff)

        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# class BookingCreateViewTest(APITestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(
#             email="a@a.com", password="pass"
#         )
#         self.room = Room.objects.create(
#             number="101",
#             room_type=Room.RoomType.SINGLE,
#             price_per_night="100.00",
#             capacity=2,
#         )
#         self.url = reverse("bookings:booking-list-create")
#         self.payload = {
#             "room": self.room.id,
#             "check_in_date": date.today().isoformat(),
#             "check_out_date": (date.today() + timedelta(days=3)).isoformat(),
#         }

#     @patch("bookings.views.create_booking_payment_session")
#     def test_create_booking_success(self, mock_payment):
#         mock_payment.return_value = MagicMock()
#         self.client.force_authenticate(user=self.user)
#         res = self.client.post(self.url, self.payload)
#         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
#         booking = Booking.objects.get(id=res.data["id"])
#         self.assertEqual(booking.user, self.user)
#         self.assertEqual(
#             booking.price_per_night,
#             Decimal(str(self.room.price_per_night))
#         )

#     @patch("bookings.views.create_booking_payment_session")
#     def test_check_in_in_past_rejected(self, mock_payment):
#         self.client.force_authenticate(user=self.user)
#         payload = {
#             **self.payload,
#             "check_in_date": (date.today() - timedelta(days=1)).isoformat(),
#         }
#         res = self.client.post(self.url, payload)
#         self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

#     @patch("bookings.views.create_booking_payment_session")
#     def test_check_out_before_check_in_rejected(self, mock_payment):
#         self.client.force_authenticate(user=self.user)
#         payload = {
#             **self.payload,
#             "check_out_date": date.today().isoformat(),
#         }
#         res = self.client.post(self.url, payload)
#         self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

#     @patch("bookings.views.create_booking_payment_session")
#     def test_overlapping_booking_rejected(self, mock_payment):
#         mock_payment.return_value = MagicMock()
#         Booking.objects.create(
#             user=self.user,
#             room=self.room,
#             check_in_date=date.today(),
#             check_out_date=date.today() + timedelta(days=3),
#             price_per_night="100.00",
#             status=BookingStatus.BOOKED,
#         )
#         self.client.force_authenticate(user=self.user)
#         res = self.client.post(self.url, self.payload)
#         self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_unauthenticated_rejected(self):
#         res = self.client.post(self.url, self.payload)
#         self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class BookingTasksCeleryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="guest@example.com", password="password123"
        )
        self.room = Room.objects.create(
            number="101",
            room_type="SINGLE",
            price_per_night=100.00,
            capacity=2,
        )
        self.today = timezone.now().date()
        self.overdue_booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            check_in_date=self.today - timedelta(days=1),
            check_out_date=self.today + timedelta(days=2),
            status=BookingStatus.BOOKED,
            price_per_night=100.00,
        )
        self.future_booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=3),
            status=BookingStatus.BOOKED,
            price_per_night=100.00,
        )

    def test_check_and_mark_no_shows(self):
        result = check_and_mark_no_shows()
        self.overdue_booking.refresh_from_db()
        self.future_booking.refresh_from_db()
        self.assertEqual(self.overdue_booking.status, BookingStatus.NO_SHOW)
        self.assertEqual(self.future_booking.status, BookingStatus.BOOKED)
        self.assertIn("Successfully marked 1 bookings as NO_SHOW", result)
