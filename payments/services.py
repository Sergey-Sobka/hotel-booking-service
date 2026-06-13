from decimal import Decimal
import stripe
from django.conf import settings
from django.urls import reverse
from .models import Payment


stripe.api_key = settings.STRIPE_SECRET_KEY
print("=== Мій Stripe Ключ із Налаштувань: ===", settings.STRIPE_SECRET_KEY)

def calculate_payment_amount(booking, payment_type: str, extra_days: int = 0) -> Decimal:

    base_price = Decimal(str(booking.total_price))
    
    if payment_type == Payment.TypeChoices.BOOKING:

        return base_price
        
    elif payment_type == Payment.TypeChoices.CANCELLATION:

        return base_price * Decimal('0.5')
        
    elif payment_type == Payment.TypeChoices.OVERSTAY:

        price_per_night = Decimal(str(booking.room.price_per_night))
        return Decimal(extra_days) * price_per_night * Decimal('1.5')
        
    elif payment_type == Payment.TypeChoices.NO_SHOW:

        return base_price * Decimal('1.2')
        
    else:
        raise ValueError(f"Невідомий тип платежу: {payment_type}")


def create_booking_payment_session(booking, payment_type: str, request, extra_days: int = 0) -> Payment:

    amount = calculate_payment_amount(booking, payment_type, extra_days)
    

    amount_in_cents = int(amount * 100)
    

    success_url = request.build_absolute_uri(reverse("payments:payment-success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("payments:payment-cancel"))


    stripe_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': getattr(settings, 'STRIPE_CURRENCY', 'usd'),
                'product_data': {
                    'name': f"Оплата за проживання ({payment_type})",
                    'description': f"Бронювання №{booking.id} — Користувач: {booking.user.email}",
                },
                'unit_amount': amount_in_cents,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
    )


    payment = Payment.objects.create(
        booking=booking,
        type=payment_type,
        amount=amount,
        session_id=stripe_session.id,
        session_url=stripe_session.url,
        status=Payment.StatusChoices.PENDING
    )

    return payment