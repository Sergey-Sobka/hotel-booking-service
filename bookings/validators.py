from .models import BookingStatus


def get_check_in_error(booking, today):
    if booking.status != BookingStatus.BOOKED:
        return "Only booked bookings can be checked in."
    if today < booking.check_in_date:
        return "Booking cannot be checked in before check-in date."
    if today >= booking.check_out_date:
        return "Booking cannot be checked in after check-out date."
    return None


def get_check_out_error(booking):
    if booking.status != BookingStatus.ACTIVE:
        return "Only active bookings can be checked out."
    return None
