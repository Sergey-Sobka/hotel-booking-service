from celery import shared_task
from django.utils import timezone
from bookings.models import Booking, BookingStatus
from notifications.tasks import send_booking_no_show_notification_task


@shared_task
def check_and_mark_no_shows():
    today = timezone.now().date()
    overdue_bookings = Booking.objects.filter(
        check_in_date__lt=today, status=BookingStatus.BOOKED
    )

    count = 0
    for booking in overdue_bookings:
        booking.status = BookingStatus.NO_SHOW
        booking.save(update_fields=["status"])
        send_booking_no_show_notification_task.delay(booking.id)
        count += 1

    return f"Successfully marked {count} bookings as NO_SHOW."
