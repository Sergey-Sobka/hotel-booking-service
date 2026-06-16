from decimal import Decimal
from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from bookings.models import Booking, BookingStatus
from rooms.models import Room
from payments.models import Payment
from payments.services import (
    calculate_payment_amount,
    create_booking_payment_session,
    complete_payment_process,
)
from django.contrib.auth import get_user_model
from datetime import date


class PaymentServiceTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com",
        )
        self.room = Room.objects.create(
            number="101",
            room_type=Room.RoomType.SINGLE,
            price_per_night=100,
            capacity=1,
        )
        self.booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in_date=date(2026, 6, 1),
            check_out_date=date(2026, 6, 3),
            price_per_night=100,
            status=BookingStatus.BOOKED,
        )
        self.factory = RequestFactory()

    def test_calculate_payment_amount(self):
        self.assertEqual(
            calculate_payment_amount(
                self.booking, Payment.TypeChoices.BOOKING
            ),
            Decimal("200"),
        )
        self.assertEqual(
            calculate_payment_amount(
                self.booking, Payment.TypeChoices.CANCELLATION_FEE
            ),
            Decimal("100"),
        )
        self.assertEqual(
            calculate_payment_amount(
                self.booking, Payment.TypeChoices.NO_SHOW_FEE
            ),
            Decimal("240"),
        )
        self.assertEqual(
            calculate_payment_amount(
                self.booking, Payment.TypeChoices.OVERSTAY_FEE, extra_days=2
            ),
            Decimal("300"),
        )

    @patch("stripe.checkout.Session.create")
    def test_create_booking_payment_session(self, mock_stripe):
        mock_stripe.return_value = MagicMock(
            id="cs_123", url="https://checkout.stripe.com/pay/123"
        )
        request = self.factory.get("/")
        payment = create_booking_payment_session(
            self.booking, Payment.TypeChoices.BOOKING, request
        )
        self.assertEqual(payment.session_id, "cs_123")
        self.assertEqual(payment.status, Payment.StatusChoices.PENDING)
        self.assertEqual(Payment.objects.count(), 1)
        mock_stripe.assert_called_once()

    def test_complete_payment_process(self):
        payment = Payment.objects.create(
            booking=self.booking,
            type=Payment.TypeChoices.BOOKING,
            amount=200,
            status=Payment.StatusChoices.PENDING,
        )
        complete_payment_process(payment)
        payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(payment.status, Payment.StatusChoices.PAID)
        self.assertEqual(self.booking.status, BookingStatus.BOOKED)
