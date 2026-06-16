from decimal import Decimal
import stripe
from django.conf import settings
from django.db import transaction
from django.urls import reverse

from bookings.models import BookingStatus, Booking
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_payment_amount(
    booking, payment_type: str, extra_days: int = 0
) -> Decimal:
    total_nights = (booking.check_out_date - booking.check_in_date).days
    base_price = Decimal(total_nights) * Decimal(str(booking.price_per_night))

    if payment_type == Payment.TypeChoices.BOOKING:
        return base_price

    elif payment_type == Payment.TypeChoices.CANCELLATION_FEE:
        return base_price * Decimal("0.5")

    elif payment_type == Payment.TypeChoices.OVERSTAY_FEE:
        price_per_night = Decimal(str(booking.price_per_night))
        return Decimal(extra_days) * price_per_night * Decimal("1.5")

    elif payment_type == Payment.TypeChoices.NO_SHOW_FEE:
        return base_price * Decimal("1.2")

    else:
        raise ValueError(f"Unknown payment type: {payment_type}")


def create_booking_payment_session(
    booking, payment_type: str, request, extra_days: int = 0
) -> Payment:
    amount = calculate_payment_amount(booking, payment_type, extra_days)
    amount_in_cents = int(amount * 100)

    success_url = (
        request.build_absolute_uri(reverse("payments:payment-success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = request.build_absolute_uri(reverse("payments:payment-cancel"))

    stripe_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
                    "product_data": {
                        "name": f"Accommodation Payment ({payment_type})",
                        "description": f"Booking #{booking.id}"
                        f" — User: {booking.user.email}",
                    },
                    "unit_amount": amount_in_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    payment = Payment.objects.create(
        booking=booking,
        type=payment_type,
        amount=amount,
        session_id=stripe_session.id,
        session_url=stripe_session.url,
        status=Payment.StatusChoices.PENDING,
    )

    return payment


def complete_payment_process(payment: Payment) -> Booking:
    with transaction.atomic():
        payment.status = Payment.StatusChoices.PAID
        payment.save()
        booking = payment.booking
        status_map = {
            Payment.TypeChoices.BOOKING: BookingStatus.BOOKED,
            Payment.TypeChoices.CANCELLATION_FEE: BookingStatus.CANCELLED,
            Payment.TypeChoices.OVERSTAY_FEE: BookingStatus.COMPLETED,
            Payment.TypeChoices.NO_SHOW_FEE: BookingStatus.NO_SHOW,
        }
        booking.status = status_map.get(payment.type, booking.status)
        booking.save()
        return booking