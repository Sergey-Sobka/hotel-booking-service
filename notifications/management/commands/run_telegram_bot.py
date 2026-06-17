import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run Telegram bot health monitor process."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Telegram bot health check interval in seconds.",
        )

    def handle(self, *args, **options):
        interval = options["interval"]

        self.stdout.write(
            self.style.SUCCESS("Telegram bot service started.")
        )

        while True:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            api_url = settings.TELEGRAM_API_URL

            if not bot_token:
                self.stdout.write(
                    self.style.WARNING(
                        "TELEGRAM_BOT_TOKEN is not configured. "
                        "Bot service is running in idle mode."
                    )
                )
                time.sleep(interval)
                continue

            try:
                response = requests.get(
                    f"{api_url}/bot{bot_token}/getMe",
                    timeout=10,
                )

                if response.ok:
                    bot_data = response.json().get("result", {})
                    username = bot_data.get("username", "unknown")
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Telegram bot is available: @{username}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Telegram bot check failed: "
                            f"{response.status_code} {response.text}"
                        )
                    )

            except requests.RequestException as error:
                self.stdout.write(
                    self.style.WARNING(
                        f"Telegram bot check error: {error}"
                    )
                )

            time.sleep(interval)
