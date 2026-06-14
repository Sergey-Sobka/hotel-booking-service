from rest_framework.exceptions import ValidationError


def validate_price_per_night(value):
    if value < 0:
        raise ValidationError("The price per night cannot be less than 0.")
    return value


def validate_room_capacity(value):
    if value <= 0:
        raise ValidationError("The room capacity must be greater than 0.")
    return value
