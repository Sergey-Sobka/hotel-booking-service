import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Payment
from .serializers import PaymentSerializer

from bookings.models import BookingStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentSuccessView(APIView):
    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "Missing session_id param."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            payment = Payment.objects.get(session_id=session_id)
            stripe_session = stripe.checkout.Session.retrieve(session_id)

            if stripe_session.payment_status == "paid":
                if payment.status == Payment.StatusChoices.PAID:
                    return HttpResponseRedirect(settings.FRONTEND_URL)
                with transaction.atomic():
                    payment.status = Payment.StatusChoices.PAID
                    payment.save()
                    booking = payment.booking

                    if payment.type == Payment.TypeChoices.BOOKING:
                        booking.status = BookingStatus.BOOKED
                    elif payment.type == Payment.TypeChoices.CANCELLATION_FEE:
                        booking.status = BookingStatus.CANCELLED
                    elif payment.type == Payment.TypeChoices.OVERSTAY_FEE:
                        booking.status = BookingStatus.COMPLETED
                    booking.save()

                return HttpResponseRedirect("http://127.0.0.1:8000/")

            else:
                return Response(
                    {"error": "Stripe session is not paid yet."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PaymentCancelView(APIView):
    def get(self, request):
        return HttpResponseRedirect("http://127.0.0.1:8000/")


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(booking__user=user)
