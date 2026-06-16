import requests
from unittest.mock import Mock, patch
from django.test import SimpleTestCase, override_settings
from notifications.services import send_telegram_message


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

