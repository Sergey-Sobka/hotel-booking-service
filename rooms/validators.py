from rest_framework.exceptions import ValidationError

MAX_CALENDAR_RANGE_DAYS = 366


def validate_price_per_night(value):
    if value < 0:
        raise ValidationError("The price per night cannot be less than 0.")
    return value


def validate_room_capacity(value):
    if value <= 0:
        raise ValidationError("The room capacity must be greater than 0.")
    return value


def validate_calendar_date_range(start_date, end_date):
    if start_date > end_date:
        raise ValidationError("The 'from' date cannot be later than the 'to' date.")

    range_days = (end_date - start_date).days + 1
    if range_days > MAX_CALENDAR_RANGE_DAYS:
        raise ValidationError(
            f"The calendar range cannot exceed {MAX_CALENDAR_RANGE_DAYS} days."
        )
