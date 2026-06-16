from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from payments.models import Payment
from bookings.models import Booking, BookingStatus
from rooms.models import Room
from datetime import date


class PaymentViewsTest(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="password"
        )
        self.room = Room.objects.create(
            number="101", price_per_night=100, capacity=1
        )
        self.booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in_date=date(2026, 7, 1),
            check_out_date=date(2026, 7, 3),
            price_per_night=100,
        )
        self.payment = Payment.objects.create(
            booking=self.booking,
            session_id="cs_test_123",
            amount=200,
            status=Payment.StatusChoices.PENDING,
        )
        self.client.force_authenticate(user=self.user)

    @patch("stripe.checkout.Session.retrieve")
    def test_payment_success_view(self, mock_retrieve):
        mock_retrieve.return_value = MagicMock(payment_status="paid")
        url = reverse("payments:payment-success")
        response = self.client.get(f"{url}?session_id=cs_test_123")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.BOOKED)

    def test_payment_list_view(self):
        url = reverse("payments:payment-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["session_id"], "cs_test_123")

    def test_payment_cancel_view(self):
        url = reverse("payments:payment-cancel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("cancelled", response.data["message"])
