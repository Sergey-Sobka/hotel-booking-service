"""Room models will be implemented in their feature task."""

from django.db import models
from django.core.validators import MinValueValidator


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        DOUBLE = "DOUBLE", "Double"
        SUITE = "SUITE", "Suite"

    number = models.CharField(max_length=50, unique=True)
    room_type = models.CharField(
        max_length=10,
        choices=RoomType.choices,  # type: ignore
        default=RoomType.SINGLE,
    )
    price_per_night = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)]
    )
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"Room {self.number} - {self.get_room_type_display()}"
