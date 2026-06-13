import stripe
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Payment
from .serializers import PaymentSerializer


stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentSuccessView(APIView):

    def get(self, request):
        session_id = request.query_params.get('session_id')

        if not session_id:
            return Response(
                {"error": "Missing session_id param."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            payment = Payment.objects.get(session_id=session_id)


            stripe_session = stripe.checkout.Session.retrieve(session_id)

            if stripe_session.payment_status == "paid":

                payment.status = Payment.StatusChoices.PAID
                payment.save()


                booking = payment.booking

                if payment.type == "BOOKING":
                    booking.status = "CONFIRMED"

                elif payment.type == "CANCELLATION":
                    booking.status = "CANCELED"

                elif payment.type == "OVERSTAY":
                    booking.status = "COMPLETED"

                booking.save()

                return Response({
                    "message": f"Payment successful! Booking status updated to {booking.status}.",
                    "booking_id": booking.id,
                    "booking_status": booking.status,
                    "amount": payment.amount
                }, status=status.HTTP_200_OK)

            else:
                return Response(
                    {"error": "Stripe session is not paid yet."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class PaymentCancelView(APIView):

    def get(self, request):

        return Response({
            "message": "Payment was canceled or paused. You can complete your payment later via your profile dashboard. Note: the payment session link is valid for only 24 hours."
        }, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(booking__user=user)
