from django.db import models

from bookings.models import Booking





class Payment(models.Model):


    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        EXPIRED = 'EXPIRED', 'Expired'

    class TypeChoices(models.TextChoices):
        BOOKING = 'BOOKING', 'Booking'
        CANCELLATION = 'CANCELLATION', 'Cancellation Fee'
        OVERSTAY = 'OVERSTAY', 'Overstay Fee'
        NO_SHOW = 'NO_SHOW', 'No Show Fee'


    booking = models.ForeignKey(
    Booking,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="bookings"
    )


    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="Payment status"
    )


    type = models.CharField(
        max_length=15,
        choices=TypeChoices.choices,
        verbose_name="Payment type"
    )


    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Amount to be paid"
    )


    session_url = models.URLField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name="Stripe link"
    )


    session_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Stripe Session ID"
    )


    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return (f"Payment {self.id} ({self.get_type_display()}) "
                f"- {self.status} - {self.amount} USD")
