from celery import shared_task

from bookings.models import Booking
from notifications.services import send_telegram_message
from notifications.templates import (
    booking_created_message,
    booking_cancelled_message,
    booking_no_show_message,
    payment_success_message,
)
from payments.models import Payment


@shared_task
def send_booking_created_notification_task(booking_id: int) -> bool:
    try:
        booking = Booking.objects.select_related("user", "room").get(
            id=booking_id
        )
    except Booking.DoesNotExist:
        return False

    return send_telegram_message(
        booking_created_message(booking)
    )


@shared_task
def send_booking_cancelled_notification_task(booking_id: int) -> bool:
    try:
        booking = Booking.objects.select_related("user", "room").get(
            id=booking_id
        )
    except Booking.DoesNotExist:
        return False

    return send_telegram_message(
        booking_cancelled_message(booking)
    )


@shared_task
def send_booking_no_show_notification_task(booking_id: int) -> bool:
    try:
        booking = Booking.objects.select_related("user", "room").get(
            id=booking_id
        )
    except Booking.DoesNotExist:
        return False

    return send_telegram_message(
        booking_no_show_message(booking)
    )


@shared_task
def send_payment_success_notification_task(payment_id: int) -> bool:
    try:
        payment = Payment.objects.select_related(
            "booking",
            "booking__user",
            "booking__room",
        ).get(id=payment_id)
    except Payment.DoesNotExist:
        return False

    return send_telegram_message(
        payment_success_message(payment)
    )
