import requests
from unittest.mock import Mock, patch
from django.test import SimpleTestCase, override_settings
from notifications.services import send_telegram_message
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from notifications.templates import (
    booking_created_message,
    booking_cancelled_message,
    booking_no_show_message,
    payment_success_message,
)


class TelegramNotificationServiceTests(SimpleTestCase):
    @override_settings(
        TELEGRAM_BOT_TOKEN="test-token",
        TELEGRAM_CHAT_ID="test-chat-id",
        TELEGRAM_API_URL="https://api.telegram.org",
    )
    @patch("notifications.services.requests.post")
    def test_send_telegram_message_success(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = send_telegram_message("Test message")

        self.assertTrue(result)
        mock_post.assert_called_once_with(
            "https://api.telegram.org/bottest-token/sendMessage",
            json={
                "chat_id": "test-chat-id",
                "text": "Test message",
                "parse_mode": "HTML",
            },
            timeout=10,
        )

    @override_settings(
        TELEGRAM_BOT_TOKEN=None,
        TELEGRAM_CHAT_ID="test-chat-id",
        TELEGRAM_API_URL="https://api.telegram.org",
    )
    def test_send_telegram_message_returns_false_without_token(self):
        result = send_telegram_message("Test message")

        self.assertFalse(result)

    @override_settings(
        TELEGRAM_BOT_TOKEN="test-token",
        TELEGRAM_CHAT_ID=None,
        TELEGRAM_API_URL="https://api.telegram.org",
    )
    def test_send_telegram_message_returns_false_without_chat_id(self):
        result = send_telegram_message("Test message")

        self.assertFalse(result)

    @override_settings(
        TELEGRAM_BOT_TOKEN="test-token",
        TELEGRAM_CHAT_ID="test-chat-id",
        TELEGRAM_API_URL="https://api.telegram.org",
    )
    @patch("notifications.services.requests.post")
    def test_send_telegram_message_returns_false_on_request_error(
        self,
        mock_post,
    ):
        mock_post.side_effect = requests.RequestException("Telegram API error")

        result = send_telegram_message("Test message")

        self.assertFalse(result)


class NotificationTemplateTests(SimpleTestCase):
    def test_booking_created_message_payload(self):
        booking = SimpleNamespace(
            id=1,
            user=SimpleNamespace(email="guest@example.com"),
            room="Room 101",
            check_in_date=date(2026, 6, 20),
            check_out_date=date(2026, 6, 25),
            price_per_night=Decimal("100.00"),
        )

        message = booking_created_message(booking)

        self.assertIn("New booking created", message)
        self.assertIn("Booking ID:</b> 1", message)
        self.assertIn("Guest:</b> guest@example.com", message)
        self.assertIn("Room:</b> Room 101", message)
        self.assertIn("Check-in:</b> 2026-06-20", message)
        self.assertIn("Check-out:</b> 2026-06-25", message)
        self.assertIn("Price per night:</b> 100.00 USD", message)

    def test_booking_cancelled_message_payload(self):
        booking = SimpleNamespace(
            id=2,
            user=SimpleNamespace(email="guest@example.com"),
            room="Room 202",
            check_in_date=date(2026, 6, 20),
            check_out_date=date(2026, 6, 25),
            is_late_cancellation=True,
        )

        message = booking_cancelled_message(booking)

        self.assertIn("Booking cancelled", message)
        self.assertIn("Booking ID:</b> 2", message)
        self.assertIn("Guest:</b> guest@example.com", message)
        self.assertIn("Room:</b> Room 202", message)
        self.assertIn("Late cancellation:</b> True", message)

    def test_booking_no_show_message_payload(self):
        booking = SimpleNamespace(
            id=3,
            user=SimpleNamespace(email="guest@example.com"),
            room="Room 303",
            check_in_date=date(2026, 6, 10),
            check_out_date=date(2026, 6, 12),
        )

        message = booking_no_show_message(booking)

        self.assertIn("Booking marked as no-show", message)
        self.assertIn("Booking ID:</b> 3", message)
        self.assertIn("Guest:</b> guest@example.com", message)
        self.assertIn("Room:</b> Room 303", message)
        self.assertIn("Check-in:</b> 2026-06-10", message)

    def test_payment_success_message_payload(self):
        payment = SimpleNamespace(
            id=4,
            type="BOOKING",
            amount=Decimal("500.00"),
            booking=SimpleNamespace(
                id=5,
                user=SimpleNamespace(email="guest@example.com"),
            ),
        )

        message = payment_success_message(payment)

        self.assertIn("Payment successful", message)
        self.assertIn("Payment ID:</b> 4", message)
        self.assertIn("Booking ID:</b> 5", message)
        self.assertIn("Guest:</b> guest@example.com", message)
        self.assertIn("Type:</b> BOOKING", message)
        self.assertIn("Amount:</b> 500.00 USD", message)
