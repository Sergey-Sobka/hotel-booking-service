from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class BookingStatus(models.TextChoices):
    BOOKED = "BOOKED", "Booked"
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    NO_SHOW = "NO_SHOW", "No Show"


class Booking(models.Model):
    room = models.ForeignKey(
        "rooms.Room",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    actual_check_out_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.BOOKED,
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ["-check_in_date"]

        constraints = [
            models.CheckConstraint(
                check=models.Q(check_out_date__gt=models.F("check_in_date")),
                name="check_out_after_check_in",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "check_in_date",
                    "check_out_date"
                ],
                name="booking_dates_idx"
            ),
            models.Index(fields=["status"], name="booking_status_idx"),
        ]
    
    def clean(self):
        if self.check_out_date and self.check_in_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError("check_out_date must be after check_in_date")

    def __str__(self):
        return f"Booking #{self.pk} — {self.user} | {self.check_in_date} -\
 {self.check_out_date}"
